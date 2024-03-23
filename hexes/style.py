from __future__ import annotations

import curses
import typing
from dataclasses import dataclass, field, replace

from hexes.color.color import Color, ColorPair_

Attribute = typing.Literal[
    "alternate_character_set",
    "blink",
    "bold",
    "dim",
    "invisible",
    "italic",
    "normal",
    "protected_mode",
    "reverse_colors",
    "standout_mode",
    "underline_mode",
    "highlight_horizontal",
    "highlight_left",
    "highlight_low",
    "highlight_right",
    "highlight_top",
    "highlight_vertical",
]

_ATTRIBUTES: dict[Attribute, int] = {
    "alternate_character_set": curses.A_ALTCHARSET,
    "blink": curses.A_BLINK,
    "bold": curses.A_BOLD,
    "dim": curses.A_DIM,
    "invisible": curses.A_INVIS,
    "italic": curses.A_ITALIC,
    "normal": curses.A_NORMAL,
    "protected_mode": curses.A_PROTECT,
    "reverse_colors": curses.A_REVERSE,
    "standout_mode": curses.A_STANDOUT,
    "underline_mode": curses.A_UNDERLINE,
    "highlight_horizontal": curses.A_HORIZONTAL,
    "highlight_left": curses.A_LEFT,
    "highlight_low": curses.A_LOW,
    "highlight_right": curses.A_RIGHT,
    "highlight_top": curses.A_TOP,
    "highlight_vertical": curses.A_VERTICAL,
}


def _bitor(xs: tuple[int, ...]):
    # bitwise or of all provided integers
    value = 0
    for x in xs:
        value |= x
    return value


def _default_to_parent(parent: Style, **kwargs):
    return {k: (getattr(parent, k) if v is None else v) for k, v in kwargs.items()}


class StyleKwargs(typing.TypedDict):
    fg: typing.NotRequired[Color | None]
    bg: typing.NotRequired[Color | None]
    alternate_character_set: typing.NotRequired[bool | None]
    blink: typing.NotRequired[bool | None]
    bold: typing.NotRequired[bool | None]
    dim: typing.NotRequired[bool | None]
    invisible: typing.NotRequired[bool | None]
    italic: typing.NotRequired[bool | None]
    normal: typing.NotRequired[bool | None]
    protected_mode: typing.NotRequired[bool | None]
    reverse_colors: typing.NotRequired[bool | None]
    standout_mode: typing.NotRequired[bool | None]
    underline_mode: typing.NotRequired[bool | None]
    highlight_horizontal: typing.NotRequired[bool | None]
    highlight_left: typing.NotRequired[bool | None]
    highlight_low: typing.NotRequired[bool | None]
    highlight_right: typing.NotRequired[bool | None]
    highlight_top: typing.NotRequired[bool | None]
    highlight_vertical: typing.NotRequired[bool | None]


@dataclass(frozen=True, slots=True)
class Style:
    default: typing.ClassVar[Style]
    fg: Color | None = field(default=None)
    bg: Color | None = field(default=None)
    # attribute flags
    alternate_character_set: bool = field(default=False, kw_only=True)
    blink: bool = field(default=False, kw_only=True)
    bold: bool = field(default=False, kw_only=True)
    dim: bool = field(default=False, kw_only=True)
    invisible: bool = field(default=False, kw_only=True)
    italic: bool = field(default=False, kw_only=True)
    normal: bool = field(default=False, kw_only=True)
    protected_mode: bool = field(default=False, kw_only=True)
    reverse_colors: bool = field(default=False, kw_only=True)
    standout_mode: bool = field(default=False, kw_only=True)
    underline_mode: bool = field(default=False, kw_only=True)
    highlight_horizontal: bool = field(default=False, kw_only=True)
    highlight_left: bool = field(default=False, kw_only=True)
    highlight_low: bool = field(default=False, kw_only=True)
    highlight_right: bool = field(default=False, kw_only=True)
    highlight_top: bool = field(default=False, kw_only=True)
    highlight_vertical: bool = field(default=False, kw_only=True)
    # integer representation of attribute flags
    _attr: int = field(init=False, repr=False)

    def __post_init__(self):
        # set integer representation of style
        object.__setattr__(self, "_attr", _bitor(tuple(v for k, v in _ATTRIBUTES.items() if getattr(self, k))))

    def __int__(self):
        return self.attr

    @property
    def attr(self) -> int:
        if self.fg is not None and self.bg is not None:
            return ColorPair_(self.fg, self.bg) | self._attr
        elif self.fg is not None and self.bg is None:
            return self.fg.fg | self._attr
        elif self.bg is not None and self.fg is None:
            return self.bg.bg | self._attr
        else:
            return self._attr

    def inherit(self, **kwargs: typing.Unpack[StyleKwargs]):
        """Create new Style overwriting provided fields."""
        return replace(self, **_default_to_parent(self, **kwargs))


Style.default = Style()
