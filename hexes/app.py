from __future__ import annotations

import curses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hexes.screen import Screen


@dataclass
class Application(ABC):
    screen: Screen = field(default_factory=Screen, init=False, repr=False)
    running: bool | None = field(default=None, init=False)

    def run(self):
        """Run application."""
        if not self.running is None:
            raise RuntimeError("Application has already been run.")
        try:
            self.running = True
            with self.screen as _:
                self.setup()
                self.screen.update()
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
        """Respond to terminal resize event."""
        self.screen.clear()
        self.screen.update()
        self.screen.noutrefresh()

    def new_layout(self, **kwargs):
        """Return a new layout managed by the application screen."""
        return self.screen.new_layout(**kwargs)

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
