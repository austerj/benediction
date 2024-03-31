import pytest

from benediction import errors
from benediction.core.layout.frame import Frame

t, l, h, w = 5, 2, 50, 20
pt, pb, pl, pr = 2, 2, 1, 1


@pytest.fixture
def dims():
    return {
        "top": t,
        "left": l,
        "height": h,
        "width": w,
        "padding_top": pt,
        "padding_bottom": pb,
        "padding_left": pl,
        "padding_right": pr,
    }


def test_invalid_dimensions(dims):
    # test that invalid dimensions raise

    # using specified dimensions works
    Frame().set_dimensions(**dims)

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "top": -1})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "left": -1})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "width": -1})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "height": -1})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "padding_top": h - pb})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "padding_bottom": h - pt})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "padding_left": w - pr})

    with pytest.raises(errors.FrameError):
        Frame().set_dimensions(**{**dims, "padding_right": w - pl})


def test_dimensions(dims):
    frame = Frame()

    # frame is ready after setting dimensions
    assert not frame.is_ready

    with pytest.raises(errors.FrameError):
        frame.width

    frame.set_dimensions(**dims)
    assert frame.is_ready

    # absolute dimensions are as expected
    assert frame.top_abs == t
    assert frame.middle_abs == t + (h - 1) // 2
    assert frame.bottom_abs == t + h - 1
    assert frame.left_abs == l
    assert frame.center_abs == l + (w - 1) // 2
    assert frame.right_abs == l + w - 1

    # outer dimensions are as expected
    assert frame.top_outer == 0
    assert frame.middle_outer == (h - 1) // 2
    assert frame.bottom_outer == h - 1
    assert frame.left_outer == 0
    assert frame.center_outer == (w - 1) // 2
    assert frame.right_outer == w - 1

    # inner dimensions are as expected
    assert frame.top == pt
    assert frame.middle == pt + (h - (pt + pb) - 1) // 2
    assert frame.bottom == pt + (h - (pt + pb)) - 1
    assert frame.left == pl
    assert frame.center == pl + (w - (pl + pr) - 1) // 2
    assert frame.right == pl + w - (pl + pr) - 1


def test_positions(dims):
    frame = Frame()
    frame.set_dimensions(**dims)

    # inner positions
    assert frame.y("top") == frame.top
    assert frame.y("middle") == frame.middle
    assert frame.y("bottom") == frame.bottom
    assert frame.x("left") == frame.left
    assert frame.x("center") == frame.center
    assert frame.x("right") == frame.right

    # outer positions
    assert frame.y("top-outer") == frame.top_outer
    assert frame.y("middle-outer") == frame.middle_outer
    assert frame.y("bottom-outer") == frame.bottom_outer
    assert frame.x("left-outer") == frame.left_outer
    assert frame.x("center-outer") == frame.center_outer
    assert frame.x("right-outer") == frame.right_outer


def test_anchors(dims):
    frame = Frame()
    frame.set_dimensions(**dims)

    # default anchors
    assert frame.y_anchor(5) == "top"
    assert frame.y_anchor("top") == "top"
    assert frame.y_anchor("top-outer") == "top"
    assert frame.y_anchor("middle") == "middle"
    assert frame.y_anchor("middle-outer") == "middle"
    assert frame.y_anchor("bottom") == "bottom"
    assert frame.y_anchor("bottom-outer") == "bottom"
    assert frame.x_anchor(5) == "left"
    assert frame.x_anchor("left") == "left"
    assert frame.x_anchor("left-outer") == "left"
    assert frame.x_anchor("center") == "center"
    assert frame.x_anchor("center-outer") == "center"
    assert frame.x_anchor("right") == "right"
    assert frame.x_anchor("right-outer") == "right"

    y, x = 5, 7
    width, height = 5, 3
    assert frame.anchor_y(y, height, "top") == y
    assert frame.anchor_y(y, height, "middle") == y - (height - 1) // 2
    assert frame.anchor_y(y, height, "bottom") == y - (height - 1)
    assert frame.anchor_x(x, width, "left") == x
    assert frame.anchor_x(x, width, "center") == x - (width - 1) // 2
    assert frame.anchor_x(x, width, "right") == x - (width - 1)


def test_overflow_check(dims):
    frame = Frame()
    frame.set_dimensions(**dims)

    # inner overflow checks
    assert not frame.x_overflows(frame.left)
    assert not frame.x_overflows(frame.right)
    assert frame.x_overflows(frame.right + 1)
    assert not frame.y_overflows(frame.top)
    assert not frame.y_overflows(frame.bottom)
    assert frame.y_overflows(frame.bottom + 1)

    # outer overflow checks
    assert not frame.x_overflows(frame.left_outer, boundary="outer")
    assert not frame.x_overflows(frame.right_outer, boundary="outer")
    assert frame.x_overflows(frame.right_outer + 1, boundary="outer")
    assert not frame.y_overflows(frame.top_outer, boundary="outer")
    assert not frame.y_overflows(frame.bottom_outer, boundary="outer")
    assert frame.y_overflows(frame.bottom_outer + 1, boundary="outer")


def test_overflow_clip(dims):
    frame = Frame()
    frame.set_dimensions(**dims)

    # inner overflow clipping
    xs = (-w, l - 1, w // 2, w + 34, l + w + 2, l + w // 4, w + 2, w - 5)
    assert not all(frame.left <= x <= frame.right for x in xs)
    assert all(frame.left <= x <= frame.right for x in frame.clip_x(*xs))
    ys = (-h, t - 1, h // 2, h + 34, t + h + 2, t + h // 4, h + 2, h - 5)
    assert not all(frame.top <= y <= frame.bottom for y in ys)
    assert all(frame.top <= y <= frame.bottom for y in frame.clip_y(*ys))

    # outer overflow clipping
    xs = (-w, l - 1, w // 2, w + 34, l + w + 2, l + w // 4, w + 2, w - 5)
    assert not all(frame.left_outer <= x <= frame.right_outer for x in xs)
    assert all(frame.left_outer <= x <= frame.right_outer for x in frame.clip_x(*xs, boundary="outer"))
    ys = (-h, t - 1, h // 2, h + 34, t + h + 2, t + h // 4, h + 2, h - 5)
    assert not all(frame.top_outer <= y <= frame.bottom_outer for y in ys)
    assert all(frame.top_outer <= y <= frame.bottom_outer for y in frame.clip_y(*ys, boundary="outer"))
