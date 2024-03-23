from __future__ import annotations

import curses
import math
import textwrap
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hexes import errors, text

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
            else:
                self.resize(left, top, width, height)
        except curses.error:
            pass

    @property
    def win(self):
        if self._win is None:
            raise errors.WindowNotInitializedError("Window must be initialized before being accessed.")
        return self._win

    def chgat(
        self,
        from_y: int | VerticalPosition,
        from_x: int | HorizontalPosition,
        to_y: int | VerticalPosition | None,
        to_x: int | HorizontalPosition | None,
        attr: int,
        y_shift: int = 0,
        x_shift: int = 0,
        to_y_shift: int = 0,
        to_x_shift: int = 0,
    ):
        """Set the attributes in a region."""
        # get region
        from_y_ = self.get_y(from_y) + y_shift
        from_x_ = self.get_x(from_x) + x_shift
        to_y_ = (from_y_ if to_y is None else self.get_y(to_y)) + to_y_shift
        to_x_ = (from_x_ if to_x is None else self.get_x(to_x)) + to_x_shift

        if self.y_overflows(from_y_, to_y_, boundary="outer") or self.x_overflows(from_x_, to_x_, boundary="outer"):
            raise errors.WindowOverflowError

        # apply attribute to each row of region
        num = max(to_x_ - from_x_ + 1, 0)
        for y in range(from_y_, to_y_ + 1):
            self.win.chgat(y, from_x_, num, attr)

    def addstr(
        self,
        str_: str | list[str],
        attr: int | None = None,
        y: int | VerticalPosition = "top",
        x: int | HorizontalPosition = "left",
        y_anchor: VerticalAnchor | None = None,
        x_anchor: HorizontalAnchor | None = None,
        y_shift: int = 0,
        x_shift: int = 0,
        clip_overflow_y: OverflowBoundary | typing.Literal[False] | None = None,
        clip_overflow_x: OverflowBoundary | typing.Literal[False] | None = None,
        ignore_overflow: bool = False,
        text_alignment: text.HorizontalAlignment | None = "left",
        wrap_width: int | None = None,
        **wrap_kwargs,
    ):
        """Add a (multi-line) string to the window."""
        # infer overflow clipping
        if clip_overflow_y is None:
            clip_overflow_y = False if isinstance(y, int) else "outer" if y.endswith("outer") else "inner"
        if clip_overflow_x is None:
            clip_overflow_x = False if isinstance(x, int) else "outer" if x.endswith("outer") else "inner"

        # wrap text
        # TODO: infer narrower width based on position / anchor, TBD
        if isinstance(str_, str):
            strs = textwrap.wrap(
                str_,
                wrap_width
                if wrap_width is not None
                else self.width
                if clip_overflow_x == "inner"
                else self.width_outer,
                **wrap_kwargs,
            )
        else:
            strs = str_

        # align text
        if text_alignment is not None:
            strs = text.align(strs, text_alignment)

        # compute anchors
        y_anchor_ = _YANCHOR[y_anchor if y_anchor is not None else _YDEFAULTANCHOR[y] if isinstance(y, str) else "top"](
            strs
        )
        x_anchor_ = _XANCHOR[
            x_anchor if x_anchor is not None else _XDEFAULTANCHOR[x] if isinstance(x, str) else "left"
        ](strs)

        # compute base coordinates
        y_: int = self.get_y(y) + y_anchor_ + y_shift
        x_: int = self.get_x(x) + x_anchor_ + x_shift

        # handle y overflow
        top_clip = 0
        bottom_clip = None
        if clip_overflow_y:
            top_clip = max((self.top if clip_overflow_y == "inner" else self.top_outer) - y_, 0)
            bottom_clip = max((self.bottom if clip_overflow_y == "inner" else self.bottom_outer) - y_ + 1, 0)
        elif not (ignore_overflow or (0 <= y_ <= self.height_outer - len(strs))):
            raise errors.WindowOverflowError()

        # handle x overflow
        left_clip = 0
        right_clip = None
        if clip_overflow_x:
            left_clip = max((self.left if clip_overflow_x == "inner" else self.left_outer) - x_, 0)
            right_clip = max((self.right if clip_overflow_x == "inner" else self.right_outer) - x_ + 1, 0)
        elif not (ignore_overflow or 0 <= x_ <= self.width_outer - max(len(s) for s in strs)):
            raise errors.WindowOverflowError()

        # shift base coordinates by overflow
        y_ += top_clip
        x_ += left_clip

        # add row by row from y_ and down
        for i, row in enumerate(strs[top_clip:bottom_clip]):
            # NOTE: suppressing curses error due to exception when printing to bottom right corner
            # see https://github.com/python/cpython/issues/52490
            try:
                if attr is not None:
                    self.win.addstr(y_ + i, x_, row[left_clip:right_clip], attr)
                else:
                    self.win.addstr(y_ + i, x_, row[left_clip:right_clip])
            except curses.error:
                pass

    def get_y(self, y: int | VerticalPosition):
        return y if isinstance(y, int) else getattr(self, _YTOPROP[y])

    def get_x(self, x: int | HorizontalPosition):
        return x if isinstance(x, int) else getattr(self, _XTOPROP[x])

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
        self.win.clear()

    @abstractmethod
    def init(self, left: int, top: int, width: int, height: int):
        raise NotImplementedError

    @abstractmethod
    def resize(self, left: int, top: int, width: int, height: int):
        raise NotImplementedError


@dataclass
class Window(AbstractWindow):
    def noutrefresh(self):
        self.win.noutrefresh()

    def init(self, left: int, top: int, width: int, height: int):
        self._win = curses.newwin(height, width, top, left)

    def resize(self, left: int, top: int, width: int, height: int):
        self.win.resize(height, width)
        self.win.mvwin(top, left)


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
        self.win.noutrefresh(self.top_shift, self.left_shift, self.top, self.left, self.bottom, self.right)

    def init(self, *args, **kwargs):
        # intrinsic pad size only depends on content size
        self._win = curses.newpad(self.content_height, self.content_width)
        # add content
        if self.content is not None:
            for i, line in enumerate(self.content):
                self._win.addstr(i, 0, line)

    def resize(self, *args, **kwargs):
        # pad is "resized" on refresh
        pass

    def shift(self, top: int | None = None, left: int | None = None):
        if top is not None:
            self._top_shift = top
        if left is not None:
            self._left_shift = left

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
