from __future__ import annotations

import curses
import typing
from dataclasses import dataclass, field

from benediction import errors
from benediction.core.node import Layout, Node, NodeSpecKwargs
from benediction.core.window import ScreenWindow
from benediction.style.color._color import reset_colors

CursorVisibility = typing.Literal[typing.Literal["invisible", "normal", "very"]]
_CURSOR_VISIBILITY: dict[CursorVisibility, int] = {
    "invisible": 0,
    "normal": 1,
    "very": 2,
}


@dataclass(slots=True)
class Screen:
    _node: ScreenNode | None = field(default=None, init=False)
    layouts: list[Layout] = field(default_factory=list, init=False)
    # screen flags
    nodelay: bool = False
    cursor_visibility: CursorVisibility = "normal"

    def __enter__(self):
        return self._setup()

    def __exit__(self, type, value, traceback) -> None:
        self._teardown()

    def clear(self):
        """Clear screen and all layouts."""
        # NOTE: screen window is cleared manually since it's the root (not cleared by layouts)
        self.stdscr.clear()
        for layout in self.layouts:
            layout.node.apply(lambda node: node.clear())

    def refresh(self):
        """Refresh screen."""
        self.stdscr.refresh()

    def noutrefresh(self):
        """Delayed refresh of screen and all layouts."""
        # NOTE: screen window is refreshed manually since it's the root (not refreshed by layouts)
        self.stdscr.noutrefresh()
        for layout in self.layouts:
            layout.node.apply(lambda node: node.noutrefresh())

    def update(self):
        """Update screen window and all layouts based on current screen size."""
        # NOTE: screen frame is updated manually since it's the root (not updated by layouts)
        height, width = self.stdscr.getmaxyx()
        self.node.update_frame()
        for layout in self.layouts:
            layout.node.update_frame(0, 0, height, width)

    def new_layout(self, **kwargs: typing.Unpack[NodeSpecKwargs]):
        """Return a new layout with the ScreenNode as its parent."""
        layout = Layout(self.node, **kwargs)
        self.layouts.append(layout)
        return layout

    def getch(self):
        return self.stdscr.getch()

    def _setup(self):
        node = ScreenNode()
        # initialize stdscr and make the frame take up the entire screen
        node.bind_window(ScreenWindow().init())
        node.update_frame()
        self._node = node
        # replicate initialization behavior of curses.wrapper
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        try:
            curses.start_color()
        except:
            pass
        # nodelay mode
        self.stdscr.nodelay(self.nodelay)
        # cursor visibility
        curses.curs_set(_CURSOR_VISIBILITY[self.cursor_visibility])
        # reset global color management state
        reset_colors()
        return self

    def _teardown(self):
        # replicate tear-down behavior of curses.wrapper
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        # unset nodelay
        self.stdscr.nodelay(False)
        # unset cursor option
        curses.curs_set(_CURSOR_VISIBILITY["normal"])
        # reset global color management state
        reset_colors()

    @property
    def stdscr(self):
        return self.node.window.internal

    @property
    def node(self):
        if not self._node:
            raise errors.ScreenError("Screen must be initialized before ScreenNode can be accessed.")
        return self._node


@dataclass(slots=True, repr=False)
class ScreenNode(Node):
    """Root Node of an Application containing a reference to the global ScreenWindow."""

    def update_frame(self, *args, **kwargs):
        # no args - screen always represents all available space
        height, width = self.window.internal.getmaxyx()
        self.frame.set_dimensions(0, 0, height, width)
