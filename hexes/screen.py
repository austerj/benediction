import curses
import typing
from dataclasses import dataclass, field

from hexes.layout import Layout, LayoutKwargs
from hexes.style.color._color import reset_colors
from hexes.window import ScreenWindow


@dataclass(slots=True)
class Screen:
    _window: ScreenWindow | None = field(default=None, init=False)
    layouts: list[Layout] = field(default_factory=list)

    def __enter__(self):
        return self._setup()

    def __exit__(self, type, value, traceback) -> None:
        self._teardown()

    def clear(self):
        """Clear screen and all layouts."""
        # NOTE: screen window (root window) will not be cleared from within layout
        self.window.clear()
        for layout in self.layouts:
            layout.clear()

    def refresh(self):
        """Refresh screen."""
        self.stdscr.refresh()

    def noutrefresh(self):
        """Delayed refresh of screen and all layouts."""
        # NOTE: screen window (root window) will not be refreshed from within layout
        self.window.noutrefresh()
        for layout in self.layouts:
            layout.noutrefresh()

    def update(self):
        """Update screen window and all layouts based on current screen size."""
        height, width = self.stdscr.getmaxyx()
        # NOTE: screen window (root window) will not have dimensions set from within layout
        self.window.set_dimensions(0, 0, width, height)
        for layout in self.layouts:
            layout.update(0, 0, width, height)

    def new_layout(self, **kwargs: typing.Unpack[LayoutKwargs]):
        """Return a new layout managed by the screen."""
        layout = Layout(self.window, **kwargs)
        self.layouts.append(layout)
        return layout

    def getch(self):
        return self.stdscr.getch()

    def _setup(self):
        self._window = ScreenWindow().init()
        # replicate initialization behavior of curses.wrapper
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        try:
            curses.start_color()
        except:
            pass
        # reset global color management state
        reset_colors()
        return self

    def _teardown(self):
        # replicate tear-down behavior of curses.wrapper
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        # reset global color management state
        reset_colors()

    @property
    def window(self):
        if not self._window:
            raise RuntimeError("Screen must be initialized before window can be accessed.")
        return self._window

    @property
    def stdscr(self):
        return self.window.stdscr
