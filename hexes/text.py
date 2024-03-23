import typing

HorizontalAlignment = typing.Literal["left", "center", "right"]
_XALIGN: dict[HorizontalAlignment, typing.Callable[[list[str], int], list[str]]] = {
    "left": lambda strs, width: [f"{s:<{width}}" for s in strs],
    "center": lambda strs, width: [f"{s:^{width}}" for s in strs],
    "right": lambda strs, width: [f"{s:>{width}}" for s in strs],
}


def align(strs: list[str], alignment: HorizontalAlignment):
    """Horizontal alignment of strings."""
    # strip whitespace
    stripped_strs = [s.strip() for s in strs]
    width = max(len(s) for s in stripped_strs)
    # align each row in same width
    return _XALIGN[alignment](stripped_strs, width)
