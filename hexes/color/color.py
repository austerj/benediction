from __future__ import annotations

import curses
import typing
from dataclasses import dataclass, field

from hexes import errors
from hexes.color import tailwind, x11

RGB = tuple[int, int, int]


# subclassing as int to enable passing instances directly as curses attr args
@dataclass(frozen=True)
class Color(int):
    number: int = field(repr=False, hash=False)
    red: int
    green: int
    blue: int

    def __new__(cls, number: int, *args, **kwargs):
        return super().__new__(cls, number)

    @property
    def fg(self) -> ColorPair:
        """Return color as foreground paired with default background."""
        return ColorPair_(self, Color_.default)

    @property
    def bg(self) -> ColorPair:
        """Return color as background paired with default foreground."""
        return ColorPair_(Color_.default, self)


@dataclass(frozen=True)
class ColorPair(int):
    number: int = field(repr=False, hash=False)
    foreground: Color
    background: Color

    def __new__(cls, number: int, *args, **kwargs):
        return super().__new__(cls, 0 if number <= 0 else curses.color_pair(number))


# exposed color classes that internally manages uniqueness
class Color_:
    __colors: dict[RGB, Color] = dict()
    default = Color(-1, None, None, None)  # type: ignore

    def __new__(cls, red: int = 0, green: int = 0, blue: int = 0):
        rgb = red, green, blue
        # add new color or retrieve existing
        if rgb not in cls.__colors:
            number = len(cls.__colors)
            cls.__colors[rgb] = Color(number, *rgb)
            # init new color definition (mapping 0-255 to curses range 0-1000)
            curses.init_color(number, *[(x * 1_000) // 255 for x in rgb])
        return cls.__colors[rgb]

    @classmethod
    def tw(cls, color: tailwind.COLOR) -> Color:
        """Get named Tailwind color."""
        try:
            rgb = tailwind.colors[color]
        except KeyError:
            raise errors.ColorError("Tailwind color not found.")
        return cls(*rgb)  # type: ignore

    @classmethod
    def tws(
        cls,
        name: tailwind.NAME,
        shades: typing.Sequence[tailwind.SHADE] = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900),
    ) -> tuple[Color, ...]:
        """Get shades of named Tailwind color."""
        return tuple(cls.tw(f"{name}-{shade}") for shade in shades)  # type: ignore

    @classmethod
    def x11(cls, color: x11.COLOR) -> Color:
        """Get named X11 color."""
        try:
            rgb = x11.colors[color]
        except KeyError:
            raise errors.ColorError("X11 color not found.")
        return cls(*rgb)  # type: ignore


class ColorPair_:
    __pairs: dict[tuple[Color, Color], ColorPair] = dict()
    default: ColorPair = ColorPair(0, None, None)  # type: ignore

    def __new__(cls, foreground: Color | RGB, background: Color | RGB):
        # retrieve colors
        if isinstance(foreground, tuple):
            foreground = Color_(*foreground)
        if isinstance(background, tuple):
            background = Color_(*background)
        # add new pair or retrieve existing
        pair_key = (foreground, background)
        if pair_key not in cls.__pairs:
            # NOTE: need to start pair number from 1 due to 0 being reserved for white-on-black
            number = len(cls.__pairs) + 1
            cls.__pairs[pair_key] = ColorPair(number, foreground, background)
            curses.init_pair(number, foreground, background)
        return cls.__pairs[pair_key]
