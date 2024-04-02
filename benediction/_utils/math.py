import typing

# tuple of (lower, upper) bounds
Bounds = tuple[int | None, int | None]


def clip(value: int, bounds: Bounds) -> int:
    """Clip a value between a minimum and a maximum."""
    lower_bound, upper_bound = bounds
    return (
        # clip to upper bound if above
        upper_bound
        if (upper_bound is not None and value > upper_bound)
        # clip to lower bound if below
        else lower_bound
        if (lower_bound is not None and value < lower_bound)
        # else return value
        else value
    )


@typing.overload
def to_abs(value: int | float, relative_to: int) -> int:
    ...


@typing.overload
def to_abs(value: None, relative_to: int) -> None:
    ...


def to_abs(value: int | float | None, relative_to: int):
    """Interpret as absolute units if integer, otherwise as rounded-down ratio of reference value."""
    return int(value * relative_to) if isinstance(value, float) else value
