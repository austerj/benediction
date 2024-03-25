import typing

HorizontalAlignment = typing.Literal["left", "center", "right"]
_XALIGN: dict[HorizontalAlignment, typing.Callable[[list[str], int], list[str]]] = {
    "left": lambda strs, width: [f"{s:<{width}}" for s in strs],
    "center": lambda strs, width: [f"{s:^{width}}" for s in strs],
    "right": lambda strs, width: [f"{s:>{width}}" for s in strs],
}
_XSTRIP: dict[HorizontalAlignment, typing.Callable[[list[str]], list[str]]] = {
    "left": lambda strs: [s.lstrip() for s in strs],
    "center": lambda strs: [s.strip() for s in strs],
    "right": lambda strs: [s.rstrip() for s in strs],
}


def align(strs: list[str], alignment: HorizontalAlignment):
    """Horizontal alignment of strings."""
    # strip whitespace
    strs = _XSTRIP[alignment](strs)
    width = max(len(s) for s in strs)
    # align each row in same width
    return _XALIGN[alignment](strs, width)


def simple_wrap(strs: str | list[str], width: int, ignore_leading_whitespace: bool = True) -> list[str]:
    """Wrap (list of) strings into strings of length less than or equal to width."""
    # special case: just return every char from flattened list
    if width <= 1:
        if isinstance(strs, str):
            return [c for c in strs]
        return [c for str_ in strs for c in str_]
    # build up list by exhausting flattened string
    wrapped_strs = []
    remaining_str = strs if isinstance(strs, str) else "\n".join(strs)
    while remaining_str:
        # ignore leading whitespace after the first line
        if wrapped_strs and (remaining_str[0] == "\n" or (ignore_leading_whitespace and remaining_str[0] == " ")):
            wrapped_strs.append(remaining_str[1 : width + 1].replace("\n", " ") or " ")
            remaining_str = remaining_str[width + 1 :]
        else:
            wrapped_strs.append(remaining_str[:width].replace("\n", " "))
            remaining_str = remaining_str[width:]
    return wrapped_strs
