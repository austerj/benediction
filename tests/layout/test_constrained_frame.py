import pytest

from benediction import errors
from benediction.core.layout.frame import ConstrainedFrame

h, h_min, h_max = 0.6, 25, 30
w, w_min, w_max = 0.5, 10, 40
mt, mb, ml, mr = 0.1, 2, 2, 1
pt, pb, pl, pr = 1, 1, 1, 0.05
const_h, const_w = 10, 10


@pytest.fixture
def constraints():
    return {
        "height": h,
        "height_min": h_min,
        "height_max": h_max,
        "width": w,
        "width_min": w_min,
        "width_max": w_max,
        "margin_top": mt,
        "margin_bottom": mb,
        "margin_left": ml,
        "margin_right": mr,
        "padding_top": pt,
        "padding_bottom": pb,
        "padding_left": pl,
        "padding_right": pr,
    }


@pytest.fixture
def implicit_constraints(constraints):
    return {**constraints, "height": None, "width": None}


@pytest.fixture
def exact_constraints(constraints):
    return {
        **constraints,
        "height": const_h,
        "width": const_w,
        "height_min": None,
        "height_max": None,
        "width_min": None,
        "width_max": None,
    }


def test_invalid_constraints(constraints):
    # valid constraints work
    ConstrainedFrame(**constraints)

    # negative height / width / constraints fail
    for attr in ["height", "height_min", "height_max", "width", "width_min", "width_max"]:
        with pytest.raises(errors.FrameConstraintError, match="non-strictly positive"):
            ConstrainedFrame(**{**constraints, attr: -1.0})

    # cannot use bounds when height / width is absolute
    for attr in ["height", "width"]:
        with pytest.raises(errors.FrameConstraintError, match="bounds with absolute"):
            ConstrainedFrame(**{**constraints, attr: 50})

    # cannot use relative bounds when height / width is relative
    for attr in ["height_min", "height_max", "width_min", "width_max"]:
        with pytest.raises(errors.FrameConstraintError, match="relative bounds with relative"):
            ConstrainedFrame(**{**constraints, f"{attr}": 0.1})

    # relative bounds must be between 0 and 1
    for attr in ["height_min", "height_max", "width_min", "width_max"]:
        with pytest.raises(errors.FrameConstraintError, match="strictly between 0 and 1"):
            ConstrainedFrame(**{**constraints, "height": None, "width": None, f"{attr}": 1.1})

    # lower bound > upper bound
    for attr in ["height", "width"]:
        with pytest.raises(errors.FrameConstraintError, match="less than upper bound"):
            ConstrainedFrame(**{**constraints, f"{attr}_min": 5, f"{attr}_max": 4})


def test_constraints(implicit_constraints, exact_constraints):
    outer_h, outer_w = 20, 50

    # valid dimensions work
    ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_min, w_min, outer_h, outer_w)
    ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_max, w_max, outer_h, outer_w)

    # below lower bound fails
    with pytest.raises(errors.FrameConstraintError, match="lower bound"):
        ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_min - 1, w_min, outer_h, outer_w)
        ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_min, w_min - 1, outer_h, outer_w)

    # above upper bound fails
    with pytest.raises(errors.FrameConstraintError, match="upper bound"):
        ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_max + 1, w_max, outer_h, outer_w)
        ConstrainedFrame(**implicit_constraints).set_dimensions(0, 0, h_max, w_max + 1, outer_h, outer_w)

    # assigning anything but exact absolute width / height fails
    with pytest.raises(errors.FrameConstraintError, match=r"exact \(absolute\)"):
        ConstrainedFrame(**exact_constraints).set_dimensions(0, 0, const_h - 1, const_w, outer_h, outer_w)
        ConstrainedFrame(**exact_constraints).set_dimensions(0, 0, const_h, const_w + 1, outer_h, outer_w)
    # exact assignment works
    ConstrainedFrame(**exact_constraints).set_dimensions(0, 0, const_h, const_w, outer_h, outer_w)

    # assigning anything but exact relative width / height fails
    with pytest.raises(errors.FrameConstraintError, match=r"exact \(relative\)"):
        ConstrainedFrame(**{**exact_constraints, "height": h}).set_dimensions(
            0, 0, int(h * outer_h) - 1, const_w, outer_h, outer_w
        )
        ConstrainedFrame(**{**exact_constraints, "width": w}).set_dimensions(
            0, 0, const_h, int(w * outer_w) + 1, outer_h, outer_w
        )
    # exact assignment works
    ConstrainedFrame(**{**exact_constraints, "height": h}).set_dimensions(
        0, 0, int(h * outer_h), const_w, outer_h, outer_w
    )
    ConstrainedFrame(**{**exact_constraints, "width": w}).set_dimensions(
        0, 0, const_h, int(w * outer_w), outer_h, outer_w
    )
