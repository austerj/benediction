import curses
from dataclasses import dataclass, field

RGB = tuple[int, int, int]


# subclassing as int to enable Color instance behaving as int reference expected by curses
@dataclass(frozen=True)
class Color(int):
    number: int = field(repr=False, hash=False)
    red: int
    green: int
    blue: int

    def __new__(cls, number: int, *args, **kwargs):
        return super().__new__(cls, number)

    def init(self):
        curses.init_color(self.number, (self.red * 1000) // 255, (self.green * 1000) // 255, (self.blue * 1000) // 255)
        return self


@dataclass(frozen=True)
class ColorPair(int):
    number: int = field(repr=False, hash=False)
    foreground: Color
    background: Color

    def __new__(cls, number: int, *args, **kwargs):
        return super().__new__(cls, curses.color_pair(number))

    def init(self):
        curses.init_pair(self.number, self.foreground, self.background)
        return self


# exposed color classes that internally manages unique colors
class Color_:
    __colors: dict[RGB, Color] = dict()

    def __new__(cls, red: int, green: int, blue: int):
        rgb = red, green, blue
        # add new color or retrieve existing
        if rgb not in cls.__colors:
            cls.__colors[rgb] = Color(len(cls.__colors), red, green, blue).init()
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
            cls.__pairs[pair_key] = ColorPair(len(cls.__pairs) + 1, foreground, background).init()
        return cls.__pairs[pair_key]
