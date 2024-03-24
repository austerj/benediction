from __future__ import annotations

import curses
import typing
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

from benediction import errors
from benediction.layout import LayoutKwargs
from benediction.screen import Screen

ErrorType = typing.Literal["curses", "benediction", "all", "layout", "window"]
_ERRORS: dict[ErrorType, typing.Type[Exception]] = {
    "curses": curses.error,
    "benediction": errors.BenedictionError,
    "all": Exception,
    "layout": errors.LayoutError,
    "window": errors.WindowError,
}


@dataclass
class Application(ABC):
    screen: Screen = field(default_factory=Screen, init=False, repr=False)
    running: bool | None = field(default=None, init=False)
    allow_rerun: typing.ClassVar[bool] = False
    # assign errors to be ignored during main loop
    suppress_errors: typing.ClassVar[
        typing.Sequence[typing.Type[Exception] | ErrorType] | typing.Type[Exception] | ErrorType | typing.Literal[False]
    ] = False
    __suppressed_errors: typing.ClassVar[tuple[typing.Type[Exception], ...]] = tuple()

    def __init_subclass__(cls) -> None:
        # infer errors to be suppressed from "public" class variable
        if cls.suppress_errors:
            if isinstance(cls.suppress_errors, str):
                cls.__suppressed_errors = (_ERRORS[cls.suppress_errors],)
            elif isinstance(cls.suppress_errors, Sequence):
                cls.__suppressed_errors = tuple(
                    _ERRORS[error_type] if isinstance(error_type, str) else error_type
                    for error_type in cls.suppress_errors
                )
            else:
                cls.__suppressed_errors = (cls.suppress_errors,)
        return super().__init_subclass__()

    def run(self):
        """Run application."""
        if not (self.allow_rerun or self.running is None):
            raise RuntimeError("Application has already been run.")
        try:
            self.running = True
            with self.screen as _:
                self.setup()
                self.main()
        finally:
            self.running = False

    def main(self):
        """Main application refresh loop."""
        # initial screen and app refresh
        try:
            self.screen.update()
            self.refresh()
        except self.__suppressed_errors:
            pass
        while self.running:
            try:
                if (ch := self.screen.getch()) == curses.KEY_RESIZE:
                    # handle resize
                    self.on_resize()
                else:
                    self.on_ch(ch)
                # main loop app refresh
                self.refresh()
            except self.__suppressed_errors:
                pass

    def on_resize(self):
        """Respond to terminal resize event."""
        self.screen.clear()
        self.screen.update()
        self.screen.noutrefresh()

    def new_layout(self, **kwargs: typing.Unpack[LayoutKwargs]):
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
