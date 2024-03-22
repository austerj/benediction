from __future__ import annotations

import curses
import math
import textwrap
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hexes import errors


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

    # absolute positions
    @property
    def abs_width(self):
        """Absolute width of window (ignoring padding)."""
        if self.__width is None:
            raise ValueError("Width must be set before being accessed.")
        return self.__width

    @property
    def abs_height(self):
        """Absolute height of window (ignoring padding)."""
        if self.__height is None:
            raise ValueError("Height must be set before being accessed.")
        return self.__height

    @property
    def abs_top(self):
        """Top of window (y-coordinate, absolute)."""
        if self.__top is None:
            raise ValueError("Vertical offset must be set before being accessed.")
        return self.__top

    @property
    def abs_middle(self):
        """Vertical middle of window (y-coordinate, absolute)."""
        return (self.abs_bottom - self.abs_top) // 2

    @property
    def abs_bottom(self):
        """Bottom of window (y-coordinate, absolute)."""
        return self.abs_top + self.abs_height - 1

    @property
    def abs_left(self):
        """Left of window (x-coordinate, absolute)."""
        if self.__left is None:
            raise ValueError("Horizontal offset must be set before being accessed.")
        return self.__left

    @property
    def abs_center(self):
        """Vertical center of window (x-coordinate, absolute)."""
        return (self.abs_right - self.abs_left) // 2

    @property
    def abs_right(self):
        """Right of window (x-coordinate, absolute)."""
        return self.abs_left + self.abs_width - 1

    # relative positions
    @property
    def width(self):
        """Width of window (with padding)."""
        return self.abs_width - (self.__padding_left + self.__padding_right)

    @property
    def height(self):
        """Height of window (with padding)."""
        return self.abs_height - (self.__padding_top + self.__padding_bottom)

    @property
    def top(self):
        """Top of window (y-coordinate, relative)."""
        return self.__padding_top

    @property
    def middle(self):
        """Vertical middle of window (y-coordinate, relative)."""
        return (self.bottom - self.top) // 2

    @property
    def bottom(self):
        """Bottom of window (y-coordinate, relative)."""
        return self.top + self.height - 1

    @property
    def left(self):
        """Left of window (x-coordinate, relative)."""
        return self.__padding_left

    @property
    def center(self):
        """Vertical center of window (x-coordinate, relative)."""
        return (self.right - self.left) // 2

    @property
    def right(self):
        """Right of window (x-coordinate, relative)."""
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

    def addstr(
        self,
        y: int | typing.Literal["top", "middle", "bottom"],
        x: int | typing.Literal["left", "center", "right"],
        str_: str | list[str],
        attr: int | None = None,
        width: int | None = None,
        clip_overflow: bool = True,
        overflow_padding: bool = False,
        **wrap_kwargs,
    ):
        w_width = self.abs_width if overflow_padding else self.width
        w_height = self.abs_height if overflow_padding else self.height
        if isinstance(str_, str):
            wrapped_str = textwrap.wrap(str_, w_width if width is None else width, **wrap_kwargs)
        else:
            wrapped_str = str_
        if not isinstance(y, int):
            if y == "middle":
                y = self.middle - math.ceil(len(wrapped_str) / 2) + 1
            elif y == "top":
                y = self.top
            elif y == "bottom":
                y = self.bottom - len(wrapped_str) + 1
        if not isinstance(x, int):
            if x == "center":
                x = self.center - math.ceil(max(len(s) for s in wrapped_str) / 2) + 1
            elif x == "right":
                x = self.right - max(len(s) for s in wrapped_str) + 1
            else:
                x = self.left
        if clip_overflow:
            # subset to rows that fit within window
            wrapped_str = wrapped_str[: w_height - y]
            # t_overflow = 0 if overflow_padding else max(self.top - y, 0)
            # b_overflow = (self.abs_bottom if overflow_padding else self.bottom) - x
            # wrapped_str = wrapped_str[t_overflow: b_overflow]
        # vertical overflow
        if y + len(wrapped_str) > w_height:
            raise errors.InsufficientSpaceError()
        for i, row in enumerate(wrapped_str):
            if clip_overflow:
                # subset to chars that fit within window
                l_overflow = 0 if overflow_padding else max(self.left - x, 0)
                r_overflow = (self.abs_right if overflow_padding else self.right) - x + 1
                row = row[l_overflow:r_overflow]
            # horizontal overflow
            if (not overflow_padding and (len(row) > self.right - x + 1 or x < self.left)) or len(
                row
            ) > self.abs_right - x + 1:
                raise errors.InsufficientSpaceError()
            # NOTE: suppressing curses error due to exception when printing to bottom right corner
            # see https://github.com/python/cpython/issues/52490
            try:
                if attr is not None:
                    self.win.addstr(y + i, x, row, attr)
                else:
                    self.win.addstr(y + i, x, row)
            except curses.error:
                pass

    @abstractmethod
    def noutrefresh(self):
        raise NotImplementedError

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
        self.win.clear()

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
        self.win.clear()

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
