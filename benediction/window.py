from __future__ import annotations

import curses
import math
import textwrap
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from benediction import errors, text
from benediction.style import MainStyleKwargs, Style

OverflowBoundary = typing.Literal["inner", "outer"]

# map string list to anchor value
HorizontalAnchor = typing.Literal["left", "center", "right"]
VerticalAnchor = typing.Literal["top", "middle", "bottom"]
_XANCHOR: dict[HorizontalAnchor, typing.Callable[[list[str]], int]] = {
    "left": lambda strs: 0,
    "center": lambda strs: -max(len(s) for s in strs) // 2 + 1,
    "right": lambda strs: -max(len(s) for s in strs) + 1,
}
_YANCHOR: dict[VerticalAnchor, typing.Callable[[list[str]], int]] = {
    "top": lambda strs: 0,
    "middle": lambda strs: -len(strs) // 2 + 1,
    "bottom": lambda strs: -len(strs) + 1,
}

# match positions to default anchors
HorizontalPosition = typing.Literal["left", "center", "right", "left-outer", "center-outer", "right-outer"]
VerticalPosition = typing.Literal["top", "middle", "bottom", "top-outer", "middle-outer", "bottom-outer"]
_XDEFAULTANCHOR: dict[HorizontalPosition, HorizontalAnchor] = {
    "left": "left",
    "left-outer": "left",
    "center": "center",
    "center-outer": "center",
    "right": "right",
    "right-outer": "right",
}
_YDEFAULTANCHOR: dict[VerticalPosition, VerticalAnchor] = {
    "top": "top",
    "top-outer": "top",
    "middle": "middle",
    "middle-outer": "middle",
    "bottom": "bottom",
    "bottom-outer": "bottom",
}

# match positions to property names
_XTOPROP: dict[HorizontalPosition, str] = {key: key.replace("-", "_") for key in _XDEFAULTANCHOR.keys()}
_YTOPROP: dict[VerticalPosition, str] = {key: key.replace("-", "_") for key in _YDEFAULTANCHOR.keys()}


class TextWrapKwargs(typing.TypedDict):
    initial_indent: typing.NotRequired[str]
    subsequent_indent: typing.NotRequired[str]
    expand_tabs: typing.NotRequired[bool]
    replace_whitespace: typing.NotRequired[bool]
    fix_sentence_endings: typing.NotRequired[bool]
    break_long_words: typing.NotRequired[bool]
    drop_whitespace: typing.NotRequired[bool]
    break_on_hyphens: typing.NotRequired[bool]
    tabsize: typing.NotRequired[int]


@dataclass
class AbstractWindow(ABC):
    """Container class managing the dimenions of a curses window."""

    _win: "curses._CursesWindow | None" = field(default=None, init=False, repr=False)
    # attributes set on update
    __width: int | None = field(default=None, init=False, repr=False)
    __height: int | None = field(default=None, init=False, repr=False)
    __left: int | None = field(default=None, init=False, repr=False)
    __top: int | None = field(default=None, init=False, repr=False)
    __padding_left: int = field(default=0, init=False, repr=False)
    __padding_top: int = field(default=0, init=False, repr=False)
    __padding_right: int = field(default=0, init=False, repr=False)
    __padding_bottom: int = field(default=0, init=False, repr=False)
    # styles
    __style: Style = field(default=Style.default, init=False, repr=False)

    # dimensions
    @property
    def width_outer(self):
        """Width of outer window (ignoring padding)."""
        if self.__width is None:
            raise ValueError("Width must be set before being accessed.")
        return self.__width

    @property
    def height_outer(self):
        """Height of outer window (ignoring padding)."""
        if self.__height is None:
            raise ValueError("Height must be set before being accessed.")
        return self.__height

    @property
    def width(self):
        """Width of inner window (with padding)."""
        return self.width_outer - (self.__padding_left + self.__padding_right)

    @property
    def height(self):
        """Height of inner window (with padding)."""
        return self.height_outer - (self.__padding_top + self.__padding_bottom)

    # absolute positions
    @property
    def top_abs(self):
        """Top of window (y-coordinate, absolute)."""
        if self.__top is None:
            raise ValueError("Vertical offset must be set before being accessed.")
        return self.__top

    @property
    def middle_abs(self):
        """Vertical middle of window (y-coordinate, absolute)."""
        return (self.bottom_abs - self.top_abs) // 2

    @property
    def bottom_abs(self):
        """Bottom of window (y-coordinate, absolute)."""
        return self.top_abs + self.height_outer - 1

    @property
    def left_abs(self):
        """Left of window (x-coordinate, absolute)."""
        if self.__left is None:
            raise ValueError("Horizontal offset must be set before being accessed.")
        return self.__left

    @property
    def center_abs(self):
        """Vertical center of window (x-coordinate, absolute)."""
        return (self.right_abs - self.left_abs) // 2

    @property
    def right_abs(self):
        """Right of window (x-coordinate, absolute)."""
        return self.left_abs + self.width_outer - 1

    # outer relative positions
    @property
    def top_outer(self):
        """Top of window (y-coordinate, relative unpadded)."""
        return 0

    @property
    def middle_outer(self):
        """Vertical middle of window (y-coordinate, relative unpadded)."""
        return self.height_outer // 2

    @property
    def bottom_outer(self):
        """Bottom of window (y-coordinate, relative unpadded)."""
        return self.height_outer - 1

    @property
    def left_outer(self):
        """Left of window (x-coordinate, relative unpadded)."""
        return 0

    @property
    def center_outer(self):
        """Vertical center of window (x-coordinate, relative unpadded)."""
        return self.right_outer // 2

    @property
    def right_outer(self):
        """Right of window (x-coordinate, relative unpadded)."""
        return self.width_outer - 1

    # padded relative positions
    @property
    def top(self):
        """Top of window (y-coordinate, relative padded)."""
        return self.__padding_top

    @property
    def middle(self):
        """Vertical middle of window (y-coordinate, relative padded)."""
        return (self.bottom + self.top) // 2

    @property
    def bottom(self):
        """Bottom of window (y-coordinate, relative padded)."""
        return self.top + self.height - 1

    @property
    def left(self):
        """Left of window (x-coordinate, relative padded)."""
        return self.__padding_left

    @property
    def center(self):
        """Vertical center of window (x-coordinate, relative padded)."""
        return (self.right + self.left) // 2

    @property
    def right(self):
        """Right of window (x-coordinate, relative padded)."""
        return self.left + self.width - 1

    def set_dimensions(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        padding_left: int = 0,
        padding_top: int = 0,
        padding_right: int = 0,
        padding_bottom: int = 0,
    ):
        # set dimensional attributes
        self.__left = left
        self.__top = top
        self.__width = width
        self.__height = height
        # set padding
        self.__padding_left = padding_left
        self.__padding_top = padding_top
        self.__padding_right = padding_right
        self.__padding_bottom = padding_bottom
        # init / resize window or silently fail on error (e.g. screen overflow)
        try:
            if not self._win:
                self.init(left, top, width, height)
                self.win.bkgd(self.style.win_ch, self.style.win_attr)
            else:
                self.resize(left, top, width, height)
        except curses.error:
            pass

    def set_style(self, style: Style):
        self.__style = style
        if self._win:
            self.win.bkgd(self.style.win_ch, self.style.win_attr)
        return self

    @property
    def style(self):
        return self.__style

    @property
    def win(self):
        if self._win is None:
            raise errors.WindowNotInitializedError("Window must be initialized before being accessed.")
        return self._win

    def format(
        self,
        from_y: int | VerticalPosition,
        from_x: int | HorizontalPosition,
        to_y: int | VerticalPosition | None,
        to_x: int | HorizontalPosition | None,
        y_shift: int = 0,
        x_shift: int = 0,
        to_y_shift: int = 0,
        to_x_shift: int = 0,
        clip_overflow_y: OverflowBoundary | typing.Literal[False] | None = None,
        clip_overflow_x: OverflowBoundary | typing.Literal[False] | None = None,
        **style_kwargs: typing.Unpack[MainStyleKwargs],
    ):
        """Change the formatting in a region of the window."""
        # infer overflow clipping
        clip_overflow_y = self._infer_overflow_boundary(from_y, to_y) if clip_overflow_y is None else clip_overflow_y
        clip_overflow_x = self._infer_overflow_boundary(from_x, to_x) if clip_overflow_x is None else clip_overflow_x

        # get region
        from_y_ = self.get_y(from_y) + y_shift
        from_x_ = self.get_x(from_x) + x_shift
        to_y_ = (from_y_ if to_y is None else self.get_y(to_y)) + to_y_shift
        to_x_ = (from_x_ if to_x is None else self.get_x(to_x)) + to_x_shift

        # handle overflow
        if clip_overflow_x:
            from_x_, to_x_ = self.clip_x(from_x_, to_x_, boundary=clip_overflow_x)
        elif self.x_overflows(from_x_, to_x_, boundary="outer"):
            raise errors.WindowOverflowError()
        if clip_overflow_y:
            from_y_, to_y_ = self.clip_y(from_y_, to_y_, boundary=clip_overflow_y)
        elif self.y_overflows(from_y_, to_y_, boundary="outer"):
            raise errors.WindowOverflowError()

        # apply attribute to each row of region
        num = max(to_x_ - from_x_ + 1, 0)
        for y in range(from_y_, to_y_ + 1):
            self.win.chgat(y, from_x_, num, self.style.derive(**style_kwargs).attr)

    def print(
        self,
        str_: str | list[str],
        y: int | float | VerticalPosition = "top",
        x: int | float | HorizontalPosition = "left",
        y_anchor: VerticalAnchor | None = None,
        x_anchor: HorizontalAnchor | None = None,
        y_shift: int | float = 0,
        x_shift: int | float = 0,
        clip_overflow_y: OverflowBoundary | typing.Literal[False] | None = None,
        clip_overflow_x: OverflowBoundary | typing.Literal[False] | None = None,
        ignore_overflow: bool = False,
        alignment: text.HorizontalAlignment | typing.Literal[False] = False,
        wrap: typing.Literal["simple", "textwrap", False] | None = None,
        wrap_width: int | None = None,
        textwrap_kwargs: TextWrapKwargs = {},
        attr: int | None = None,
        **style_kwargs: typing.Unpack[MainStyleKwargs],
    ):
        """Print a (multi-line) string to the window."""
        # infer overflow clipping
        clip_overflow_y = self._infer_overflow_boundary(y) if clip_overflow_y is None else clip_overflow_y
        clip_overflow_x = self._infer_overflow_boundary(x) if clip_overflow_x is None else clip_overflow_x

        # compute base coordinates
        inner_x = clip_overflow_x != "outer"
        inner_y = clip_overflow_y != "outer"
        y_: int = self.get_y(y, inner_y) + self.get_y(y_shift, inner_y)
        x_: int = self.get_x(x, inner_x) + self.get_x(x_shift, inner_x)

        # get anchors
        y_anchor = y_anchor if y_anchor is not None else _YDEFAULTANCHOR[y] if isinstance(y, str) else "top"
        x_anchor = x_anchor if x_anchor is not None else _XDEFAULTANCHOR[x] if isinstance(x, str) else "left"

        # infer wrapping method from other parameters
        wrap = wrap if wrap is not None else "simple" if isinstance(str_, str) or wrap_width is not None else False

        if wrap:
            if wrap_width is None:
                if not isinstance(str_, str):
                    raise ValueError("Cannot cannot infer wrap width from list of strings.")
                # infer wrap width s.t. lines wrap at point of horizontal overflow
                elif x_anchor == "center":
                    # NOTE: this ties directly to the middle anchor "rounding down", which leads
                    # to the string always growing to the right first (when the number of chars
                    # is even) - so the width here corresponds to the minimum of where the
                    # string would overflow on either side given this pattern, e.g.:
                    #
                    #  ... 2 3 4 5 6 7 8 ...
                    # LEFT |   x       | RIGHT
                    #      | _ _ _     |
                    #      | _ _ _ _   |
                    #      _ _ _ _ _   |
                    #      _ _ _ _ _ _ |
                    #    _ _ _ _ _ _ _ |
                    #    _ _ _ _ _ _ _ _
                    #
                    # x  L   R   W
                    # ------------
                    # ...
                    # 7  11  2   2
                    # 6  9   4   4
                    # 5  7   6   6
                    # 4  5   8   5
                    # 3  3   10  3
                    # ...
                    #
                    # with x being the position, L/R the left/right char limit and W the width
                    r = self.right_outer if x_anchor.endswith("outer") else self.right
                    l = self.left_outer if x_anchor.endswith("outer") else self.left
                    wrap_width = min(
                        2 * (x_ - l) + 1,
                        2 * (r - x_),
                    )
                elif x_anchor == "right":
                    l = self.left_outer if x_anchor.endswith("outer") else self.left
                    wrap_width = x_ - l + 1
                else:
                    r = self.right_outer if x_anchor.endswith("outer") else self.right
                    wrap_width = r - x_ + 1
                wrap_width = max(wrap_width, 1)
            # apply wrap to (list of) strings
            if wrap == "textwrap":
                if not isinstance(str_, str):
                    raise ValueError("Cannot wrap list of strings with 'textwrap': use 'simple'.")
                elif not str_ or str_.isspace():
                    raise ValueError("Cannot apply 'textwrap' to whitespace string: use 'simple'.")
                strs = textwrap.wrap(
                    str_,
                    wrap_width,
                    **textwrap_kwargs,
                )
            else:
                strs = text.simple_wrap(str_, wrap_width)
        elif isinstance(str_, str):
            # not wrapping string - so just contain in list
            strs = [str_]
        else:
            # proceed with list of strings provided as param
            strs = str_

        # align text
        if alignment:
            strs = text.align(strs, alignment)

        # compute anchors
        y_ += _YANCHOR[y_anchor](strs)
        x_ += _XANCHOR[x_anchor](strs)

        # handle y overflow
        top_clip, bottom_clip = 0, None
        if clip_overflow_y:
            top_clip = max((self.top if clip_overflow_y == "inner" else self.top_outer) - y_, 0)
            bottom_clip = max((self.bottom if clip_overflow_y == "inner" else self.bottom_outer) - y_ + 1, 0)
        elif not (ignore_overflow or (0 <= y_ <= self.height_outer - len(strs))):
            raise errors.WindowOverflowError()

        # handle x overflow
        left_clip, right_clip = 0, None
        if clip_overflow_x:
            left_clip = max((self.left if clip_overflow_x == "inner" else self.left_outer) - x_, 0)
            right_clip = max((self.right if clip_overflow_x == "inner" else self.right_outer) - x_ + 1, 0)
        elif not (ignore_overflow or 0 <= x_ <= self.width_outer - max(len(s) for s in strs)):
            raise errors.WindowOverflowError()

        # shift base coordinates by overflow
        y_ += top_clip
        x_ += left_clip

        if attr is not None:
            if style_kwargs:
                raise ValueError("Cannot use explicit 'attr' together with style keyword arguments.")
            attr_ = attr
        else:
            # inherit from window style if any kwargs were provided
            attr_ = self.style.derive(**style_kwargs).attr

        # add row by row from y_ and down
        for i, row in enumerate(strs[top_clip:bottom_clip]):
            # NOTE: suppressing curses error due to exception when printing to bottom right corner
            # see https://github.com/python/cpython/issues/52490
            try:
                self.win.addstr(y_ + i, x_, row[left_clip:right_clip], attr_)
            except curses.error:
                pass

    @staticmethod
    def _infer_overflow_boundary(*xys: int | float | HorizontalPosition | VerticalPosition | None):
        # drop None params
        xys_ = [xy for xy in xys if xy is not None]
        return (
            # assume outer boundary if all values are ints or any explicit outer coordinate
            "outer"
            if all(isinstance(xy, int) for xy in xys_)
            or any(isinstance(xy, str) and xy.endswith("outer") for xy in xys_)
            # else default to inner boundary
            else "inner"
        )

    def get_y(self, y: int | float | VerticalPosition, inner: bool = True) -> int:
        """Get vertical position from float (relative to window) or named position."""
        if isinstance(y, float):
            t, h = (self.top, self.height) if inner else (self.top_outer, self.height_outer)
            return t + round(y * (h - 1))
        return y if isinstance(y, int) else getattr(self, _YTOPROP[y])

    def get_x(self, x: int | float | HorizontalPosition, inner: bool = True) -> int:
        """Get horizontal position from float (relative to window) or named position."""
        if isinstance(x, float):
            l, w = (self.left, self.width) if inner else (self.left_outer, self.width_outer)
            return l + round(x * (w - 1))
        return x if isinstance(x, int) else getattr(self, _XTOPROP[x])

    def clip_x(self, *xs: int, boundary: OverflowBoundary = "inner"):
        """Clip x values to overflow boundary."""
        l, r = (self.left, self.right) if boundary == "inner" else (self.left_outer, self.right_outer)
        return tuple(min(max(x, l), r) for x in xs)

    def clip_y(self, *ys: int, boundary: OverflowBoundary = "inner"):
        """Clip y values to overflow boundary."""
        t, b = (self.top, self.bottom) if boundary == "inner" else (self.top_outer, self.bottom_outer)
        return tuple(min(max(y, t), b) for y in ys)

    def y_overflows(self, *ys: int | VerticalPosition, boundary: OverflowBoundary = "inner"):
        """Test if y overflows the inner or outer window boundary."""
        if boundary == "inner":
            return not all((self.top <= self.get_y(y) <= self.bottom) for y in ys)
        else:
            return not all((self.top_outer <= self.get_y(y) <= self.bottom_outer) for y in ys)

    def x_overflows(self, *xs: int | HorizontalPosition, boundary: OverflowBoundary = "inner"):
        """Test if x overflows the inner or outer window boundary."""
        if boundary == "inner":
            return not all((self.left <= self.get_x(x) <= self.right) for x in xs)
        else:
            return not all((self.left_outer <= self.get_x(x) <= self.right_outer) for x in xs)

    @abstractmethod
    def noutrefresh(self):
        raise NotImplementedError

    def clear(self):
        if self._win:
            self._win.clear()

    @abstractmethod
    def init(self, left: int, top: int, width: int, height: int):
        raise NotImplementedError

    @abstractmethod
    def resize(self, left: int, top: int, width: int, height: int):
        raise NotImplementedError


@dataclass
class Window(AbstractWindow):
    def noutrefresh(self):
        if self._win:
            self._win.noutrefresh()
        return self

    def init(self, left: int, top: int, width: int, height: int):
        self._win = curses.newwin(height, width, top, left)
        return self

    def resize(self, left: int, top: int, width: int, height: int):
        if self._win:
            self._win.resize(height, width)
            self._win.mvwin(top, left)
        return self


@dataclass
class Pad(AbstractWindow):
    content: typing.Sequence[str] | None = None
    # content dimensions
    _content_width: int | None = field(default=None, repr=False)
    _content_height: int | None = field(default=None, repr=False)
    # coordinates defining subset of pad to display
    _top_shift: int = field(default=0, init=False, repr=False)
    _left_shift: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        if self.content is not None:
            # infer content width and height
            if self._content_height is None:
                self._content_height = len(self.content)
            if self._content_width is None:
                self._content_width = max(len(s) for s in self.content)

    def noutrefresh(self):
        if self._win:
            self._win.noutrefresh(self.top_shift, self.left_shift, self.top, self.left, self.bottom, self.right)
        return self

    def init(self, *args, **kwargs):
        # intrinsic pad size only depends on content size
        self._win = curses.newpad(self.content_height, self.content_width)
        # add content
        if self.content is not None:
            for i, line in enumerate(self.content):
                self._win.addstr(i, 0, line)
        return self

    def resize(self, *args, **kwargs):
        # pad is "resized" on refresh
        return self

    def shift(self, top: int | None = None, left: int | None = None):
        if top is not None:
            self._top_shift = top
        if left is not None:
            self._left_shift = left
        return self

    @property
    def content_width(self):
        if self._content_width is None:
            raise ValueError("Content width must be set before being accessed.")
        return self._content_width

    @property
    def content_height(self):
        if self._content_height is None:
            raise ValueError("Content height must be set before being accessed.")
        return self._content_height

    @property
    def top_shift(self):
        return self._top_shift

    @property
    def left_shift(self):
        return self._left_shift

    @property
    def content_top(self):
        """Top of content (y-coordinate)."""
        return 0

    @property
    def content_middle(self):
        """Vertical middle of content (y-coordinate)."""
        return self.content_height // 2

    @property
    def content_bottom(self):
        """Bottom of content (y-coordinate)."""
        return self.content_height - 1

    @property
    def content_left(self):
        """Left of content (x-coordinate)."""
        return 0

    @property
    def content_center(self):
        """Vertical center of content (x-coordinate)."""
        return self.content_right // 2

    @property
    def content_right(self):
        """Right of content (x-coordinate)."""
        return self.content_width - 1


@dataclass
class ScrollingPad(Pad):
    """Pad that keeps shifted position in the (vertical) middle of window area."""

    @property
    def top_shift(self):
        # compute the position to shift to s.t. the content:
        #   1. stays fixed at the top if shift is above the mid-point
        #   2. begins to scroll after shift reaches the mid-point
        #   3. stays fixed when the bottom of the content is visible
        offset = self.height / 2
        return max(
            min(
                self._top_shift,
                self.content_height - math.ceil(offset),
            )
            - math.floor(offset),
            0,
        )


@dataclass
class ScreenWindow(Window):
    def init(self, *args, **kwargs):
        self._win = curses.initscr()
        return self

    @property
    def stdscr(self):
        return self.win

    def resize(self, *args, **kwargs):
        # screen window cannot be resized
        pass
