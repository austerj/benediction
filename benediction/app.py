from __future__ import annotations

import curses
import time
import typing
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import _GeneratorContextManager, contextmanager
from dataclasses import dataclass, field

from benediction import errors
from benediction.layout import LayoutKwargs
from benediction.screen import CursorVisibility, Screen

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
    _screen: Screen | None = field(default=None, init=False, repr=False)
    running: bool | None = field(default=None, init=False)
    # behavior flags
    allow_rerun: typing.ClassVar[bool] = False
    cursor_visibility: typing.ClassVar[CursorVisibility] = "invisible"
    refresh_rate: typing.ClassVar[int | None] = None
    # assign errors to be ignored during main loop
    suppress_errors: typing.ClassVar[
        typing.Sequence[typing.Type[Exception] | ErrorType] | typing.Type[Exception] | ErrorType | typing.Literal[False]
    ] = "benediction"
    # internal error handling stuff
    __error_handler: typing.ClassVar[typing.Callable[..., _GeneratorContextManager[None]]]
    __debugging = False

    def __init_subclass__(cls) -> None:
        # infer errors to be suppressed from "public" class variable
        if cls.suppress_errors:
            if isinstance(cls.suppress_errors, str):
                suppressed_errors = (_ERRORS[cls.suppress_errors],)
            elif isinstance(cls.suppress_errors, Sequence):
                suppressed_errors = tuple(
                    _ERRORS[error_type] if isinstance(error_type, str) else error_type
                    for error_type in cls.suppress_errors
                )
            else:
                suppressed_errors = cls.suppress_errors
        else:
            suppressed_errors = tuple()

        # suppress errors if not debugging
        @contextmanager
        def error_handler(self: Application):
            try:
                yield
            except suppressed_errors as e:
                if self.__debugging:
                    raise e

        cls.__error_handler = error_handler

        return super().__init_subclass__()

    @property
    def screen(self):
        if not self._screen:
            raise errors.ScreenError("Cannot access screen before running.")
        return self._screen

    def run(self):
        """Run application."""
        if not (self.allow_rerun or self.running is None):
            raise RuntimeError("Application has already been run.")
        try:
            # flag running and initialize screen
            self.running = True
            self._screen = Screen(
                nodelay=self.refresh_rate is not None,
                cursor_visibility=self.cursor_visibility,
            )
            # run main loop after setup
            with self.screen as _:
                self.setup()
                self._main()
        finally:
            # unset running flag and delete screen
            self.running = False
            del self._screen

    def debug(self):
        """Debug application (ignoring suppression of errors)."""
        try:
            self.__debugging = True
            self.run()
        finally:
            self.__debugging = False

    def _main(self):
        """Main application refresh loop."""
        # initial screen and app refresh
        with self.__error_handler():
            self._on_resize()
            self._refresh()
        while self.running:
            with self.__error_handler():
                if (ch := self.screen.getch()) == curses.KEY_RESIZE:
                    # handle resize
                    self._on_resize()
                else:
                    self.on_ch(ch)
                # main loop app refresh
                self._refresh()
                # delay next frame according to refresh rate
                if isinstance(self.refresh_rate, int) and self.refresh_rate > 0:
                    time.sleep(1 / self.refresh_rate)

    def _on_resize(self):
        """Respond to terminal resize event."""
        self.screen.clear()
        self.screen.update()

    def _refresh(self):
        """Refresh physical screen."""
        self._noutrefresh()
        curses.doupdate()

    def _noutrefresh(self):
        """Refresh virtual screen."""
        self.update()
        self.screen.noutrefresh()

    def new_layout(
        self,
        space_y: int | float | None = None,
        space_x: int | float | None = None,
        **kwargs: typing.Unpack[LayoutKwargs],
    ):
        """Return a new layout managed by the application screen."""
        return self.screen.new_layout(space_y, space_x, **kwargs)

    def exit(self):
        """Break out from main loop."""
        self.running = False

    @abstractmethod
    def update(self):
        """Update virtual screen in main loop."""
        raise NotImplementedError

    @abstractmethod
    def setup(self):
        """Application state setup prior to main loop."""
        raise NotImplementedError

    @abstractmethod
    def on_ch(self, ch: int | None):
        """Respond to character press (e.g. update application state)"""
        raise NotImplementedError
