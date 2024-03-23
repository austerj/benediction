import curses
from dataclasses import dataclass, field

from hexes.layout import Layout
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
        self.stdscr.clear()
        for layout in self.layouts:
            layout.clear()

    def refresh(self):
        """Refresh screen."""
        self.stdscr.refresh()

    def noutrefresh(self):
        """Delayed refresh of screen and all layouts."""
        self.stdscr.noutrefresh()
        for layout in self.layouts:
            layout.noutrefresh()

    def update(self):
        """Update screen window and all layouts based on current screen size."""
        height, width = self.stdscr.getmaxyx()
        self.window.set_dimensions(0, 0, width, height)
        for layout in self.layouts:
            layout.update(0, 0, height, width)

    def new_layout(self, **kwargs):
        """Return a new layout managed by the screen."""
        layout = Layout(**kwargs)
        self.layouts.append(layout)
        return layout

    def getch(self):
        return self.stdscr.getch()

    def _setup(self):
        # replicate initialization behavior of curses.wrapper
        self._window = ScreenWindow().init()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        try:
            curses.start_color()
        except:
            pass
        # setting _win manually - cannot initialize screen window outside initscr
        return self

    def _teardown(self):
        # replicate tear-down behavior of curses.wrapper
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    @property
    def window(self):
        if not self._window:
            raise RuntimeError("Screen must be initialized before window can be accessed.")
        return self._window

    @property
    def stdscr(self):
        return self.window.stdscr
