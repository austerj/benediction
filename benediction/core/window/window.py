from __future__ import annotations

import curses
import math
import textwrap
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from benediction import errors
from benediction._utils import text
from benediction.core.frame import (
    HorizontalAnchor,
    HorizontalPosition,
    OverflowBoundary,
    VerticalAnchor,
    VerticalPosition,
)
from benediction.style import Style, StyleKwargs
from benediction.style.style import WindowStyleKwargs

if typing.TYPE_CHECKING:
    from benediction.core.frame import Frame


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

    __internal: "curses._CursesWindow | None" = field(default=None, init=False, repr=False)
    __frame: Frame | None = field(default=None, init=False)
    # styles
    __style: Style = field(default=Style.default, init=False, repr=False)

    @property
    def frame(self):
        """Frame controlling dimensions of AbstractWindow."""
        if self.__frame is None:
            raise errors.WindowError(f"No Frame has been bound to {self.__class__.__name__}.")
        return self.__frame

    @property
    def ready(self) -> bool:
        """Flag denoting if the window Frame is ready (has dimensions assigned)."""
        return self.frame.is_ready

    def bind_frame(self, frame: Frame | None):
        """Bind Frame to AbstractWindow."""
        self.__frame = frame
        return self

    def on_frame_update(self):
        # init / resize window or silently fail on error (e.g. screen overflow)
        try:
            if not self.__internal:
                self.init(self.frame.left, self.frame.top, self.frame.width, self.frame.height)
            else:
                self.resize(self.frame.left, self.frame.top, self.frame.width, self.frame.height)
            self.apply_style()
        except curses.error:
            pass

    def set_style(self, style: Style):
        """Assign new Style to window."""
        self.__style = style
        self.apply_style()
        return self

    def update_style(self, **kwargs: typing.Unpack[WindowStyleKwargs]):
        """Update existing Style of window."""
        return self.set_style(self.style.derive(**kwargs))

    def apply_style(self, style: Style | None = None):
        """Apply Style to window."""
        style = self.style if style is None else style
        if self.ready:
            self.internal.bkgd(style.win_ch, style.win_attr)
            if style.default_inner_fg is not None or style.default_inner_bg is not None:
                self.format("top", "left", "bottom", "right", fg=style.default_inner_fg, bg=style.default_inner_bg)

    @property
    def style(self):
        return self.__style

    @property
    def internal(self):
        """Internal curses window."""
        if self.__internal is None:
            raise errors.WindowNotInitializedError("Window must be initialized before being accessed.")
        return self.__internal

    def get_attr(
        self,
        style: Style | typing.Literal["default"] | None = None,
        attr: int | None = None,
        **kwargs: typing.Unpack[StyleKwargs],
    ):
        """Handle prioritization of style-related arguments and return integer representation of style."""
        if attr is not None:
            if kwargs or style:
                raise ValueError("Cannot use explicit 'attr' together with style arguments.")
            return attr
        # default to window style if no explicit object was provided
        style = self.style if style is None else Style.default if style == "default" else style
        # return mutated attr if kwargs were provided
        if kwargs:
            return style.derive(**kwargs).attr
        # else return attr from original Style object
        return style.attr

    def format(
        self,
        from_y: int | VerticalPosition,
        from_x: int | HorizontalPosition = "left",
        to_y: int | VerticalPosition | None = None,
        to_x: int | HorizontalPosition | None = "right",
        y_shift: int = 0,
        x_shift: int = 0,
        to_y_shift: int = 0,
        to_x_shift: int = 0,
        clip_overflow_y: OverflowBoundary | typing.Literal[False] | None = None,
        clip_overflow_x: OverflowBoundary | typing.Literal[False] | None = None,
        style: Style | typing.Literal["default"] | None = None,
        attr: int | None = None,
        **style_kwargs: typing.Unpack[StyleKwargs],
    ):
        """Change the formatting in a region of the window."""
        f = self.frame
        # infer overflow clipping
        clip_overflow_y = f._infer_overflow_boundary(from_y, to_y) if clip_overflow_y is None else clip_overflow_y
        clip_overflow_x = f._infer_overflow_boundary(from_x, to_x) if clip_overflow_x is None else clip_overflow_x

        # get region
        from_y_ = f.y(from_y) + y_shift
        from_x_ = f.x(from_x) + x_shift
        to_y_ = (from_y_ if to_y is None else f.y(to_y)) + to_y_shift
        to_x_ = (from_x_ if to_x is None else f.x(to_x)) + to_x_shift

        # handle overflow
        if clip_overflow_x:
            from_x_, to_x_ = f.clip_x(from_x_, to_x_, boundary=clip_overflow_x)
        elif f.x_overflows(from_x_, to_x_, boundary="outer"):
            raise errors.WindowOverflowError()
        if clip_overflow_y:
            from_y_, to_y_ = self.frame.clip_y(from_y_, to_y_, boundary=clip_overflow_y)
        elif f.y_overflows(from_y_, to_y_, boundary="outer"):
            raise errors.WindowOverflowError()

        # apply attribute to each row of region
        num = max(to_x_ - from_x_ + 1, 0)
        attr = self.get_attr(style, attr, **style_kwargs)
        for y in range(from_y_, to_y_ + 1):
            self.internal.chgat(y, from_x_, num, attr)

    def print(
        self,
        str_: typing.Sequence[str],
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
        style: Style | typing.Literal["default"] | None = None,
        attr: int | None = None,
        **style_kwargs: typing.Unpack[StyleKwargs],
    ):
        """Print a (multi-line) string to the window."""
        f = self.frame
        # infer overflow clipping
        clip_overflow_y = f._infer_overflow_boundary(y) if clip_overflow_y is None else clip_overflow_y
        clip_overflow_x = f._infer_overflow_boundary(x) if clip_overflow_x is None else clip_overflow_x

        # compute base coordinates
        inner_x = clip_overflow_x != "outer"
        inner_y = clip_overflow_y != "outer"
        y_: int = f.y(y, inner_y) + f.y(y_shift, inner_y)
        x_: int = f.x(x, inner_x) + f.x(x_shift, inner_x)

        # get anchors
        y_anchor = f.y_anchor(y)
        x_anchor = f.x_anchor(x)

        # infer wrapping method from other parameters
        wrap = wrap if wrap is not None else "simple" if isinstance(str_, str) or wrap_width is not None else False

        if wrap:
            if wrap_width is None:
                if not isinstance(str_, str):
                    raise ValueError("Cannot cannot infer wrap width unless argument is a string.")
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
                    r = f.right_outer if x_anchor.endswith("outer") else f.right
                    l = f.left_outer if x_anchor.endswith("outer") else f.left
                    wrap_width = min(
                        2 * (x_ - l) + 1,
                        2 * (r - x_),
                    )
                elif x_anchor == "right":
                    l = f.left_outer if x_anchor.endswith("outer") else f.left
                    wrap_width = x_ - l + 1
                else:
                    r = f.right_outer if x_anchor.endswith("outer") else f.right
                    wrap_width = r - x_ + 1
                wrap_width = max(wrap_width, 1)
            # apply wrap to (sequence of) strings
            if wrap == "textwrap":
                if not isinstance(str_, str):
                    raise ValueError("Cannot wrap non-string with 'textwrap': use 'simple'.")
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
            # not wrapping string - so just contain in tuple
            strs = (str_,)
        else:
            # proceed with sequence of strings provided as arg
            strs = str_

        # align text
        if alignment:
            strs = text.align(strs, alignment)

        # compute anchors
        strs_height, strs_width = len(strs), max(len(s) for s in strs)
        y_ = f.anchor_y(y_, strs_height, y_anchor)
        x_ = f.anchor_x(x_, strs_width, x_anchor)

        # handle y overflow
        top_clip, bottom_clip = 0, None
        if clip_overflow_y:
            top_clip = max((f.top if clip_overflow_y == "inner" else f.top_outer) - y_, 0)
            bottom_clip = max((f.bottom if clip_overflow_y == "inner" else f.bottom_outer) - y_ + 1, 0)
        elif not (ignore_overflow or (0 <= y_ <= f.height_outer - len(strs))):
            raise errors.WindowOverflowError()

        # handle x overflow
        left_clip, right_clip = 0, None
        if clip_overflow_x:
            left_clip = max((f.left if clip_overflow_x == "inner" else f.left_outer) - x_, 0)
            right_clip = max((f.right if clip_overflow_x == "inner" else f.right_outer) - x_ + 1, 0)
        elif not (ignore_overflow or 0 <= x_ <= f.width_outer - max(len(s) for s in strs)):
            raise errors.WindowOverflowError()

        # shift base coordinates by overflow
        y_ += top_clip
        x_ += left_clip

        # add row by row from y_ and down
        attr = self.get_attr(style, attr, **style_kwargs)
        for i, row in enumerate(strs[top_clip:bottom_clip]):
            # NOTE: suppressing curses error due to exception when printing to bottom right corner
            # see https://github.com/python/cpython/issues/52490
            try:
                self.internal.addstr(y_ + i, x_, row[left_clip:right_clip], attr)
            except curses.error:
                pass

    @abstractmethod
    def noutrefresh(self):
        raise NotImplementedError

    def clear(self):
        if self.__internal:
            self.__internal.clear()

    @abstractmethod
    def init(self, left: int, top: int, width: int, height: int):
        """Initialize internal curses Window."""
        raise NotImplementedError

    @abstractmethod
    def resize(self, left: int, top: int, width: int, height: int):
        """Resize internal curses Window."""
        raise NotImplementedError


@dataclass
class Window(AbstractWindow):
    def noutrefresh(self):
        if self.__internal:
            self.__internal.noutrefresh()
        return self

    def init(self, left: int, top: int, width: int, height: int):
        self.__internal = curses.newwin(height, width, top, left)
        return self

    def resize(self, left: int, top: int, width: int, height: int):
        if self.__internal:
            self.__internal.resize(height, width)
            self.__internal.mvwin(top, left)
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
        if self.__internal:
            f = self.frame
            # using absolute values since pad coordinates are relative to screen
            self.__internal.noutrefresh(
                self.top_shift,
                self.left_shift,
                f.top_abs + f.padding_top,
                f.left_abs + f.padding_left,
                f.bottom_abs - f.padding_bottom,
                f.right_abs - f.padding_right,
            )
        return self

    def init(self, left: int, top: int, width: int, height: int):
        # we use max values to ensure that the pad does not underflow the normal dimensions
        self.__internal = curses.newpad(max(self.content_height, height), max(self.content_width, width))
        # add content
        if self.content is not None:
            for i, line in enumerate(self.content):
                self.__internal.addstr(i, 0, line)
        return self

    def resize(self, left: int, top: int, width: int, height: int):
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
        offset = self.frame.height / 2
        return max(
            min(
                self._top_shift,
                self.content_height - math.ceil(offset),
            )
            - math.floor(offset),
            0,
        )


# TODO (?): restructure to root ScreenNode (with bound window / frame by default)
@dataclass
class ScreenWindow(Window):
    def init(self, *args, **kwargs):
        self.__internal = curses.initscr()
        return self

    @property
    def stdscr(self):
        return self.internal

    def resize(self, *args, **kwargs):
        # screen window cannot be resized
        pass
