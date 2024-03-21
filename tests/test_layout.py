import pytest

from hexes import errors
from hexes.layout import Column, Layout, Row
from hexes.window import Window


def check_dimensions(item: Row | Column, width: int | float, height: int | float):
    # allowing off-by-one error due to truncation (e.g. 33-33-34 for three windows in 100 width)
    if (window := item.window) is None:
        raise TypeError
    return width - 1 <= window.width <= width + 1 and height - 1 <= window.height <= height + 1


def w():
    return Window()


def test_dynamic_dimensions():
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
        .row(height=r0_h).subd()
            .col(w()).col(w())
        # r1
        # -----------------------------
        #     c0    | c1 | c2 | c3 | c4
        #           |    |    |    |  
        # -----------------------------
        .row(height=r1_h).subd()
            .col(w(), width=r1_c0_w).col(w()).col(w()).col(w()).col(w())
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
        layout.update(height, width)

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

    layout.row(height=50).subd().col(w(), width=30).col(w())

    # fail: insufficient height
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(40, 40)

    # fail: insufficient width
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(60, 20)

    # still fails because dynamic column has no available space
    with pytest.raises(errors.InsufficientSpaceError):
        layout.update(50, 30)

    # does not fail - dynamic column gets width of 1
    layout.update(50, 31)
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
            .col(w(), ml=1, mb=2).col(w(), mr=1)
        .row(w(), mx=1, mt=3)
    )
    # fmt: on

    height, width = 100, 100
    layout.update(height, width)
    margin_layout.update(height, width)

    # unmargined layout takes up all available space
    assert check_dimensions(layout.rows[0].cols[0], width / 2, height / 2)
    assert check_dimensions(layout.rows[0].cols[1], width / 2, height / 2)
    assert check_dimensions(layout.rows[1], width, height / 2)

    # margined layout leaves gaps as defined by margins
    assert check_dimensions(margin_layout.rows[0].cols[0], width / 2 - (2 + 1), height / 2 - (2 + 2))
    assert check_dimensions(margin_layout.rows[0].cols[1], width / 2 - (2 + 1), height / 2 - (2 + 0))
    assert check_dimensions(margin_layout.rows[1], width - 2, height / 2 - 3)
