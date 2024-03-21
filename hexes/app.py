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
        if not self.running is None:
            raise RuntimeError("Application has already been run.")
        try:
            self.running = True
            self.layout = Layout(self.screen)
            with self.screen as _:
                self.setup()
                self.layout.update()
                self.main()
        finally:
            self.running = False

    def main(self):
        self.refresh()
        while self.running:
            if (ch := self.screen.getch()) == curses.KEY_RESIZE:
                # handle resize
                self.on_resize()
            else:
                self.on_ch(ch)
            # refresh
            self.refresh()

    def on_resize(self):
        self.layout.update()
        self.screen.refresh()
        self.refresh()

    @abstractmethod
    def refresh(self):
        raise NotImplementedError

    @abstractmethod
    def setup(self):
        raise NotImplementedError

    @abstractmethod
    def on_ch(self, ch: int | None):
        raise NotImplementedError
