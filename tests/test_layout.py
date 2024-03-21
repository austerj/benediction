import pytest

from hexes import errors
from hexes.layout import Layout
from hexes.window import AbstractWindow, Window


def check_dimensions(window: AbstractWindow | None, width: int | float, height: int | float):
    # allowing off-by-one error due to truncation (e.g. 33-33-34 for three windows in 100 width)
    if window is None:
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
        assert check_dimensions(layout.rows[0].cols[0].window, r0_c_w, r0_h)
        assert check_dimensions(layout.rows[0].cols[1].window, r0_c_w, r0_h)
        # row1 cols
        assert check_dimensions(layout.rows[1].cols[0].window, r1_c0_w, r1_h)
        r1_c_w = (width - r1_c0_w) / 4
        assert check_dimensions(layout.rows[1].cols[1].window, r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[2].window, r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[3].window, r1_c_w, r1_h)
        assert check_dimensions(layout.rows[1].cols[4].window, r1_c_w, r1_h)
        # row2 cols
        r2_c_w = width / 2
        r2_h = height - (r0_h + r1_h)
        assert check_dimensions(layout.rows[2].cols[0].window, r2_c_w, r2_h)
        # row2,col1 rows
        r2_c1_r1_h = r2_h - r2_c1_r0_h
        assert check_dimensions(layout.rows[2].cols[1].rows[0].window, r2_c_w, r2_c1_r0_h)
        assert check_dimensions(layout.rows[2].cols[1].rows[1].window, r2_c_w, r2_c1_r1_h)


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
