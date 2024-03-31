import pytest

from benediction import errors
from benediction.core.layout.frame import ConstrainedFrame

h, h_min, h_max = 0.5, 25, 30
w, w_min, w_max = 0.3, 5, 40
mt, mb, ml, mr = 0.1, 2, 2, 1
pt, pb, pl, pr = 2, 3, 2, 0.1


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
