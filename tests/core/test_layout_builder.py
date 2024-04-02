import pytest

from benediction import errors
from benediction.core.node import Node
from benediction.core.node.layout.builder import Layout


def check_dimensions(item: Node, height: int | float, width: int | float):
    # allowing off-by-one error due to truncation (e.g. 33-33-34 for three windows in 100 width)
    return width - 1 <= item.frame.width_outer <= width + 1 and height - 1 <= item.frame.height_outer <= height + 1


def test_implicit_layout():
    layout = Layout()
    Layout()

    r0_h = 10
    r1_h = 20
    r1_c0_w = 20
    r2_c1_r0_h = 5

    # fmt: off
    (layout
        # r0
        # -----------------------------
        #       c0      |      c1     
        #               |             
        # -----------------------------
        .row(h=r0_h).subd()
            .col().col()
        # r1
        # -----------------------------
        #     c0    | c1 | c2 | c3 | c4
        #           |    |    |    |  
        # -----------------------------
        .row(h=r1_h).subd()
            .col(w=r1_c0_w).col().col().col().col()
        # r2
        # -----------------------------
        #       c0      |     c1r0    
        #               |--------------
        #               |     c1r1    
        #               |             
        # -----------------------------
        .row().subd()
            .col().col().subd()
                .row(h=r2_c1_r0_h)
                .row()
    )
    # fmt: on

    for height, width in [(100, 100), (80, 120), (91, 51)]:
        layout.node.update_frame(0, 0, height, width)

        # row0 cols
        r0_c_w = width / 2
        assert check_dimensions(layout[0][0], r0_h, r0_c_w)
        assert check_dimensions(layout[0][1], r0_h, r0_c_w)
        # row1 cols
        assert check_dimensions(layout[1][0], r1_h, r1_c0_w)
        r1_c_w = (width - r1_c0_w) / 4
        assert check_dimensions(layout[1][1], r1_h, r1_c_w)
        assert check_dimensions(layout[1][2], r1_h, r1_c_w)
        assert check_dimensions(layout[1][3], r1_h, r1_c_w)
        assert check_dimensions(layout[1][4], r1_h, r1_c_w)
        # row2 cols
        r2_c_w = width / 2
        r2_h = height - (r0_h + r1_h)
        assert check_dimensions(layout[2][0], r2_h, r2_c_w)
        # row2,col1 rows
        r2_c1_r1_h = r2_h - r2_c1_r0_h
        assert check_dimensions(layout[2][1][0], r2_c1_r0_h, r2_c_w)
        assert check_dimensions(layout[2][1][1], r2_c1_r1_h, r2_c_w)


def test_insufficient_space():
    layout = Layout()

    layout.row(h=50).subd().col(w=30).col()

    # fail: insufficient height
    with pytest.raises(errors.InsufficientSpaceError):
        layout.node.update_frame(0, 0, 40, 40)

    # fail: insufficient width
    with pytest.raises(errors.InsufficientSpaceError):
        layout.node.update_frame(0, 0, 60, 20)

    # still fails because dynamic column has no available space
    with pytest.raises(errors.InsufficientSpaceError):
        layout.node.update_frame(0, 0, 50, 30)

    # does not fail - dynamic column gets width of 1
    layout.node.update_frame(0, 0, 50, 31)
    assert check_dimensions(layout[0][1], 50, 1)


def test_margins():
    layout = Layout()
    margin_layout = Layout()

    # fmt: off
    (layout
        .row().subd()
            .col().col()
        .row()
    )
    (margin_layout
        .row(m=1).subd()
            .col(ml=2, mb=2).col(mr=4)
        .row(mx=1, mt=3)
    )
    # fmt: on

    height, width = 100, 100
    layout.node.update_frame(0, 0, height, width)
    margin_layout.node.update_frame(0, 0, height, width)

    # unmargined layout takes up all available space
    assert check_dimensions(layout[0][0], height / 2, width / 2)
    assert check_dimensions(layout[0][1], height / 2, width / 2)
    assert check_dimensions(layout[1], height / 2, width)
    # positions match borders of available space
    r0_c0_w = layout[0][0].frame
    assert r0_c0_w.left_abs == 0
    assert r0_c0_w.top_abs == 0
    assert r0_c0_w.right_abs == r0_c0_w.width_outer - 1
    assert r0_c0_w.bottom_abs == r0_c0_w.height_outer - 1
    r0_c1_w = layout[0][1].frame
    assert r0_c1_w.left_abs == r0_c0_w.width_outer
    assert r0_c1_w.top_abs == 0
    assert r0_c1_w.right_abs == r0_c0_w.width_outer + r0_c1_w.width_outer - 1
    assert r0_c1_w.bottom_abs == r0_c1_w.height_outer - 1
    r1_w = layout[1].frame
    assert r1_w.left_abs == 0
    assert r1_w.top_abs == r0_c1_w.height_outer
    assert r1_w.right_abs == width - 1
    assert r1_w.bottom_abs == height - 1

    # margined layout leaves gaps as defined by margins
    assert check_dimensions(margin_layout[0][0], height / 2 - (2 + 2), width / 2 - (2 + 1))
    assert check_dimensions(margin_layout[0][1], height / 2 - (2 + 0), width / 2 - (2 + 4))
    assert check_dimensions(margin_layout[1], height / 2 - 3, width - 2)
    # positions match borders of margined space
    m_r0_c0_w = margin_layout[0][0].frame
    assert m_r0_c0_w.left_abs == r0_c0_w.left_abs + (1 + 2)  # 1 from row m=1, 2 from ml=2
    assert m_r0_c0_w.top_abs == r0_c0_w.top_abs + 1  # 1 from row m=1
    assert m_r0_c0_w.right_abs == r0_c0_w.right_abs  # no margin
    assert m_r0_c0_w.bottom_abs == r0_c0_w.bottom_abs - (1 + 2)  # 1 from row m=1, 2 from mb=2
    m_r0_c1_w = margin_layout[0][1].frame
    assert m_r0_c1_w.left_abs == r0_c1_w.left_abs  # no margin
    assert m_r0_c1_w.top_abs == r0_c1_w.top_abs + 1  # 1 from row m=1
    assert m_r0_c1_w.right_abs == r0_c1_w.right_abs - (1 + 4)  # 1 from row m=1, 4 from mr=4
    assert m_r0_c1_w.bottom_abs == r0_c1_w.bottom_abs - 1  # 1 from row m=1
    m_r1_w = margin_layout[1].frame
    assert m_r1_w.left_abs == r1_w.left_abs + 1  # 1 from mx=1
    assert m_r1_w.top_abs == r1_w.top_abs + 3  # 3 from row mt=3
    assert m_r1_w.right_abs == r1_w.right_abs - 1  # 1 from row mx=1
    assert m_r1_w.bottom_abs == r1_w.bottom_abs  # no margin


def test_dynamic_floats():
    layout = Layout()

    layout.row(h=0.5).row(h=0.2).row().subd().col(w=0.4).col().col()

    layout.node.update_frame(0, 0, 100, 100)
    assert check_dimensions(layout[0], 50, 100)
    assert check_dimensions(layout[1], 20, 100)
    assert check_dimensions(layout[2][0], 30, 40)
    assert check_dimensions(layout[2][1], 30, 30)
    assert check_dimensions(layout[2][2], 30, 30)


def test_padding():
    layout = Layout()
    padded_layout = Layout()

    layout.row()
    padded_layout.row(p=1, pr=2)

    layout.node.update_frame(0, 0, 100, 100)
    padded_layout.node.update_frame(0, 0, 100, 100)

    row = layout[0]
    padded_row = padded_layout[0]

    # padding does not change window dimensions
    assert check_dimensions(row, 100, 100)
    assert check_dimensions(padded_row, 100, 100)

    # regular row window has relative positions in corners of screen
    assert row.frame.left == 0
    assert row.frame.top == 0
    assert row.frame.right == 99
    assert row.frame.bottom == 99

    # padded row window shifts relative positions
    assert padded_row.frame.left == 1
    assert padded_row.frame.top == 1
    assert padded_row.frame.right == 97
    assert padded_row.frame.bottom == 98


def test_layout_order():

    row_layout = Layout()
    row_layout.col().subd().row().row()
    assert row_layout.order == "row"

    # cannot add row to row-major layout
    with pytest.raises(errors.LayoutError):
        row_layout.row()

    col_layout = Layout()
    col_layout.row().subd().col().col()
    assert col_layout.order == "col"

    # cannot add column to column-major layout
    with pytest.raises(errors.LayoutError):
        col_layout.col()


def test_layout_orientation():
    layout = Layout()

    # fmt: off
    (layout
        .row().subd()
            .col().col()
        .row()
    )
    # fmt: on

    # fmt: off
    assert [x.orientation for x in layout.node.flatten()] == [
        "col", # root column
            "row", # row 0
                "col", # row 0, column 0
                "col", # row 0, column 1
            "row", # row 1
    ]
    # fmt: on


def test_relative_layout():
    layout = Layout()

    r0_h, r0_c0_w, r0_c1_mb, r1_h, r1_mr = 0.4, 0.25, 0.15, 0.2, 0.1

    # fmt: off
    (layout
        .row(h=r0_h).subd()
            .col(w=r0_c0_w).col(mb=r0_c1_mb)
        .row(h=r1_h, mr=r1_mr)
        .row()
    )
    # fmt: on

    for height in [30, 50, 60]:
        for width in [30, 60, 90]:
            layout.node.update_frame(0, 0, height, width)
            # row 0
            assert check_dimensions(layout[0], r0_h * height, width)
            assert check_dimensions(layout[0][0], r0_h * height, r0_c0_w * width)
            assert check_dimensions(layout[0][1], (1 - r0_c1_mb) * (r0_h * height), (1 - r0_c0_w) * width)
            # row 1
            assert check_dimensions(layout[1], r1_h * height, (1 - r1_mr) * width)
            # row 2
            assert check_dimensions(layout[2], (1 - r0_h - r1_h) * height, width)


def test_bounds():
    layout = Layout()

    r0_h_min, r0_h_max = 10, 30
    r1_h_min, r1_h_max = 5, 10
    r1_c0_w_min, r1_c0_w_max = 20, 25
    r1_c1_w = 2

    # fmt: off
    (layout
        .row(min_h=r0_h_min, max_h=r0_h_max)
        .row(min_h=r1_h_min, max_h=r1_h_max).subd()
            .col(min_w=r1_c0_w_min, max_w=r1_c0_w_max).col(w=r1_c1_w).col()
        .row()
    )
    # fmt: on

    # height must be between 15 (+1 for last row) and 60 (+1 for last row) due to constraints
    for height in [16, 40, 61]:
        # 20 (+1+2) and 25 (+1+2) due to constraints
        for width in [23, 25, 27]:
            layout.node.update_frame(0, 0, height, width)
            # row 0
            assert layout[0].frame.width == width
            assert r0_h_min <= layout[0].frame.height <= r0_h_max
            # row 1
            assert layout[1].frame.width == width
            assert r1_h_min <= layout[1].frame.height <= r1_h_max
            assert r1_c0_w_min <= layout[1][0].frame.width <= r1_c0_w_max
            assert layout[1][1].frame.width == r1_c1_w
            assert layout[1][2].frame.width == width - r1_c1_w - layout[1][0].frame.width
            # row 2
            assert layout[2].frame.width == width
            assert check_dimensions(layout[2], height - layout[0].frame.height - layout[1].frame.height, width)
