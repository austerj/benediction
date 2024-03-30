import pytest

from benediction import errors
from benediction.layout import Column, Layout, Row
from benediction.window import Window


def check_dimensions(item: Row | Column, width: int | float, height: int | float):
    # allowing off-by-one error due to truncation (e.g. 33-33-34 for three windows in 100 width)
    return width - 1 <= item.window.width_outer <= width + 1 and height - 1 <= item.window.height_outer <= height + 1


def w():
    return Window()


def test_implicit_layout():
    layout = Layout()

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
            .col(w()).col(w())
        # r1
        # -----------------------------
        #     c0    | c1 | c2 | c3 | c4
        #           |    |    |    |  
        # -----------------------------
        .row(h=r1_h).subd()
            .col(w(), w=r1_c0_w).col(w()).col(w()).col(w()).col(w())
        # r2
        # -----------------------------
        #       c0      |     c1r0    
        #               |--------------
        #               |     c1r1    
        #               |             
        # -----------------------------
        .row().subd()
            .col(w()).col().subd()
                .row(w(), r2_c1_r0_h)
                .row(w())

    )
    # fmt: on

    for height, width in [(100, 100), (80, 120), (91, 51)]:
        layout.update(0, 0, width, height)

        # row0 cols
        r0_c_w = width / 2
        assert check_dimensions(layout.rows[0].cols[0], r0_c_w, r0_h)
        assert check_dimensions(layout.rows[0].cols[1], r0_c_w, r0_h)
        # row1 cols
        assert check_dimensions(layout.rows[1].cols[0], r1_c0_w, r1_h)
        r1_c_w = (width - r1_c0_w) / 4
        assert check_dimensions(layout.rows[1].cols[1], r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[2], r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[3], r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[4], r1_c_w, r1_h)
        # row2 cols
        r2_c_w = width / 2
        r2_h = height - (r0_h + r1_h)
        assert check_dimensions(layout.rows[2].cols[0], r2_c_w, r2_h)
        # row2,col1 rows
        r2_c1_r1_h = r2_h - r2_c1_r0_h
        assert check_dimensions(layout.rows[2].cols[1].rows[0], r2_c_w, r2_c1_r0_h)
        assert check_dimensions(layout.rows[2].cols[1].rows[1], r2_c_w, r2_c1_r1_h)


def test_insufficient_space():
    layout = Layout()

    layout.row(h=50).subd().col(w(), w=30).col(w())

    # fail: insufficient height
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(0, 0, 40, 40)

    # fail: insufficient width
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(0, 0, 20, 60)

    # still fails because dynamic column has no available space
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(0, 0, 30, 50)

    # does not fail - dynamic column gets width of 1
    layout.update(0, 0, 31, 50)
    assert check_dimensions(layout.rows[0].cols[1], 1, 50)


def test_margins():
    layout = Layout()
    margin_layout = Layout()

    # fmt: off
    (layout
        .row().subd()
            .col(w()).col(w())
        .row(w())
    )
    (margin_layout
        .row(m=1).subd()
            .col(w(), ml=2, mb=2).col(w(), mr=4)
        .row(w(), mx=1, mt=3)
    )
    # fmt: on

    height, width = 100, 100
    layout.update(0, 0, height, width)
    margin_layout.update(0, 0, height, width)

    # unmargined layout takes up all available space
    assert check_dimensions(layout.rows[0].cols[0], width / 2, height / 2)
    assert check_dimensions(layout.rows[0].cols[1], width / 2, height / 2)
    assert check_dimensions(layout.rows[1], width, height / 2)
    # positions match borders of available space
    r0_c0_w = layout.rows[0].cols[0].window
    assert r0_c0_w.left_abs == 0
    assert r0_c0_w.top_abs == 0
    assert r0_c0_w.right_abs == r0_c0_w.width_outer - 1
    assert r0_c0_w.bottom_abs == r0_c0_w.height_outer - 1
    r0_c1_w = layout.rows[0].cols[1].window
    assert r0_c1_w.left_abs == r0_c0_w.width_outer
    assert r0_c1_w.top_abs == 0
    assert r0_c1_w.right_abs == r0_c0_w.width_outer + r0_c1_w.width_outer - 1
    assert r0_c1_w.bottom_abs == r0_c1_w.height_outer - 1
    r1_w = layout.rows[1].window
    assert r1_w.left_abs == 0
    assert r1_w.top_abs == r0_c1_w.height_outer
    assert r1_w.right_abs == width - 1
    assert r1_w.bottom_abs == height - 1

    # margined layout leaves gaps as defined by margins
    assert check_dimensions(margin_layout.rows[0].cols[0], width / 2 - (2 + 1), height / 2 - (2 + 2))
    assert check_dimensions(margin_layout.rows[0].cols[1], width / 2 - (2 + 4), height / 2 - (2 + 0))
    assert check_dimensions(margin_layout.rows[1], width - 2, height / 2 - 3)
    # positions match borders of margined space
    m_r0_c0_w = margin_layout.rows[0].cols[0].window
    assert m_r0_c0_w.left_abs == r0_c0_w.left_abs + (1 + 2)  # 1 from row m=1, 2 from ml=2
    assert m_r0_c0_w.top_abs == r0_c0_w.top_abs + 1  # 1 from row m=1
    assert m_r0_c0_w.right_abs == r0_c0_w.right_abs  # no margin
    assert m_r0_c0_w.bottom_abs == r0_c0_w.bottom_abs - (1 + 2)  # 1 from row m=1, 2 from mb=2
    m_r0_c1_w = margin_layout.rows[0].cols[1].window
    assert m_r0_c1_w.left_abs == r0_c1_w.left_abs  # no margin
    assert m_r0_c1_w.top_abs == r0_c1_w.top_abs + 1  # 1 from row m=1
    assert m_r0_c1_w.right_abs == r0_c1_w.right_abs - (1 + 4)  # 1 from row m=1, 4 from mr=4
    assert m_r0_c1_w.bottom_abs == r0_c1_w.bottom_abs - 1  # 1 from row m=1
    m_r1_w = margin_layout.rows[1].window
    assert m_r1_w.left_abs == r1_w.left_abs + 1  # 1 from mx=1
    assert m_r1_w.top_abs == r1_w.top_abs + 3  # 3 from row mt=3
    assert m_r1_w.right_abs == r1_w.right_abs - 1  # 1 from row mx=1
    assert m_r1_w.bottom_abs == r1_w.bottom_abs  # no margin


def test_dynamic_floats():
    layout = Layout()

    layout.row(w(), h=0.5).row(w(), h=0.2).row().subd().col(w(), w=0.4).col(w()).col(w())

    layout.update(0, 0, 100, 100)
    assert check_dimensions(layout[0], 100, 50)
    assert check_dimensions(layout[1], 100, 20)
    assert check_dimensions(layout[2][0], 40, 30)
    assert check_dimensions(layout[2][1], 30, 30)
    assert check_dimensions(layout[2][2], 30, 30)


def test_padding():
    layout = Layout()
    padded_layout = Layout()

    layout.row(w())
    padded_layout.row(w(), p=1, pr=2)

    layout.update(0, 0, 100, 100)
    padded_layout.update(0, 0, 100, 100)

    row = layout.rows[0]
    padded_row = padded_layout.rows[0]

    # padding does not change window dimensions
    assert check_dimensions(row, 100, 100)
    assert check_dimensions(padded_row, 100, 100)

    # regular row window has relative positions in corners of screen
    assert row.window.left == 0
    assert row.window.top == 0
    assert row.window.right == 99
    assert row.window.bottom == 99

    # padded row window shifts relative positions
    assert padded_row.window.left == 1
    assert padded_row.window.top == 1
    assert padded_row.window.right == 97
    assert padded_row.window.bottom == 98


def test_layout_order():

    row_layout = Layout()
    row_layout.col().row(w()).row(w())
    assert row_layout.order == "row"

    # cannot add row to row-major layout
    with pytest.raises(errors.LayoutError):
        row_layout.row()

    col_layout = Layout()
    col_layout.row().col(w()).col(w())
    assert col_layout.order == "col"

    # cannot add column to column-major layout
    with pytest.raises(errors.LayoutError):
        col_layout.col()


def test_layout_items():
    layout = Layout()

    # fmt: off
    (layout
        .row().subd()
            .col(w()).col(w())
        .row(w())
    )
    # fmt: on

    # fmt: off
    assert [type(x) for x in layout.flatten()] == [
        Column, # root column
            Row, # row 0
                Column, # row 0, column 0
                Column, # row 0, column 1
            Row, # row 1
    ]
    # fmt: on

    # fmt: off
    assert [type(x) for x in layout.windows] == [
        # ScreenWindow, # root column
            # Row, # row 0
                Window, # row 0, column 0
                Window, # row 0, column 1
            Window, # row 1
    ]
    # fmt: on


def test_relative_layout():
    layout = Layout()

    r0_h, r0_c0_w, r0_c1_mb, r1_h, r1_mr = 0.4, 0.25, 0.15, 0.2, 0.1

    # fmt: off
    (layout
        .row(w(), h=r0_h).subd()
            .col(w(), w=r0_c0_w).col(w(), mb=r0_c1_mb)
        .row(w(), h=r1_h, mr=r1_mr)
        .row(w())
    )
    # fmt: on

    for height in [30, 50, 60]:
        for width in [30, 60, 90]:
            layout.update(0, 0, width, height)
            # row 0
            assert check_dimensions(layout[0], width, r0_h * height)
            assert check_dimensions(layout[0][0], r0_c0_w * width, r0_h * height)
            assert check_dimensions(layout[0][1], (1 - r0_c0_w) * width, (1 - r0_c1_mb) * (r0_h * height))
            # row 1
            assert check_dimensions(layout[1], (1 - r1_mr) * width, r1_h * height)
            # row 2
            assert check_dimensions(layout[2], width, (1 - r0_h - r1_h) * height)


def test_bounds():
    layout = Layout()

    r0_h_min, r0_h_max = 10, 30
    r1_h_min, r1_h_max = 5, 10
    r1_c0_w_min, r1_c0_w_max = 20, 25
    r1_c1_w = 2

    # fmt: off
    (layout
        .row(w(), min_h=r0_h_min, max_h=r0_h_max)
        .row(w(), min_h=r1_h_min, max_h=r1_h_max).subd()
            .col(w(), min_w=r1_c0_w_min, max_w=r1_c0_w_max).col(w(), w=r1_c1_w).col(w())
        .row(w())
    )
    # fmt: on

    # height must be between 15 (+1 for last row) and 60 (+1 for last row) due to constraints
    for height in [16, 40, 61]:
        # 20 (+1+2) and 25 (+1+2) due to constraints
        for width in [23, 25, 27]:
            layout.update(0, 0, width, height)
            # row 0
            assert layout[0].window.width == width
            assert r0_h_min <= layout[0].window.height <= r0_h_max
            # row 1
            assert layout[1].window.width == width
            assert r1_h_min <= layout[1].window.height <= r1_h_max
            assert r1_c0_w_min <= layout[1][0].window.width <= r1_c0_w_max
            assert layout[1][1].window.width == r1_c1_w
            assert layout[1][2].window.width == width - r1_c1_w - layout[1][0].window.width
            # row 2
            assert layout[2].window.width == width
            assert check_dimensions(layout[2], width, height - layout[0].window.height - layout[1].window.height)
