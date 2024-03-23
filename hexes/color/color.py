import curses
import typing
from dataclasses import dataclass, field

from hexes import errors
from hexes.color import tailwind

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

    def __post_init__(self):
        curses.init_color(self.number, (self.red * 1000) // 255, (self.green * 1000) // 255, (self.blue * 1000) // 255)


@dataclass(frozen=True)
class ColorPair(int):
    number: int = field(repr=False, hash=False)
    foreground: Color
    background: Color

    def __new__(cls, number: int, *args, **kwargs):
        return super().__new__(cls, curses.color_pair(number))

    def __post_init__(self):
        curses.init_pair(self.number, self.foreground, self.background)


# exposed color classes that internally manages unique colors
class Color_:
    __colors: dict[RGB, Color] = dict()

    # overloading init for typing purposes
    @typing.overload
    def __init__(self, name: tailwind.COLOR):
        ...

    @typing.overload
    def __init__(self, red: int, green: int, blue: int):
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __new__(cls, name_or_red: tailwind.COLOR | int = 0, green: int = 0, blue: int = 0):
        if isinstance(name_or_red, str):
            try:
                rgb = tailwind.colors[name_or_red]
            except KeyError:
                raise errors.ColorError("Color not found.")
        else:
            rgb = name_or_red, green, blue
        # add new color or retrieve existing
        if rgb not in cls.__colors:
            cls.__colors[rgb] = Color(len(cls.__colors), *rgb)
        return cls.__colors[rgb]


class ColorPair_:
    __pairs: dict[tuple[Color, Color], ColorPair] = dict()

    def __new__(cls, foreground: Color | RGB, background: Color | RGB):
        # retrieve colors
        if isinstance(foreground, tuple):
            foreground = Color_(*foreground)
        if isinstance(background, tuple):
            background = Color_(*background)
        # add new pair or retrieve existing
        pair_key = (foreground, background)
        if pair_key not in cls.__pairs:
            # NOTE: need to start pair number from 1 due to 0 being reserved for black-on-white
            cls.__pairs[pair_key] = ColorPair(len(cls.__pairs) + 1, foreground, background)
        return cls.__pairs[pair_key]
