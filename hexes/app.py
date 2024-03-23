from __future__ import annotations

import curses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hexes.layout import Layout
from hexes.screen import Screen


@dataclass
class Application(ABC):
    screen: Screen = field(default_factory=Screen, init=False, repr=False)
    layout: Layout = field(init=False, repr=False)
    running: bool | None = field(default=None, init=False)

    def run(self):
        """Run application."""
        if not self.running is None:
            raise RuntimeError("Application has already been run.")
        try:
            self.running = True
            self.layout = Layout()
            with self.screen as _:
                self.setup()
                self.update_layout()
                self.main()
        finally:
            self.running = False

    def main(self):
        """Main application refresh loop."""
        # initial app refresh
        self.refresh()
        while self.running:
            if (ch := self.screen.getch()) == curses.KEY_RESIZE:
                # handle resize
                self.on_resize()
            else:
                self.on_ch(ch)
            # main loop app refresh
            self.refresh()

    def on_resize(self):
        self.update_layout()

    def update_layout(self):
        """Update layout and clear screen."""
        self.screen.clear()
        self.screen.noutrefresh()
        height, width = self.screen.stdscr.getmaxyx()
        self.layout.update(0, 0, height, width)
        self.layout.noutrefresh()
        self.layout.clear()

    @abstractmethod
    def refresh(self):
        """Refresh based on current application state."""
        raise NotImplementedError

    @abstractmethod
    def setup(self):
        """Application state setup prior to main refresh loop."""
        raise NotImplementedError

    @abstractmethod
    def on_ch(self, ch: int | None):
        """Respond to character press (e.g. update internal state of application.)"""
        raise NotImplementedError
