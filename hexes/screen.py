import curses


class Screen:
    def __enter__(self):
        return self._setup()

    def __exit__(self, type, value, traceback) -> None:
        self._teardown()

    def refresh(self):
        self.stdscr.refresh()

    def getch(self):
        return self.stdscr.getch()

    def _setup(self):
        # replicate initialization behavior of curses.wrapper
        self._stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self._stdscr.keypad(True)
        try:
            curses.start_color()
        except:
            pass
        # hide cursor and enable default colors
        curses.curs_set(0)
        curses.use_default_colors()
        # initial clear and refresh
        self.stdscr.clear()
        self.stdscr.refresh()
        return self

    def _teardown(self):
        # replicate tear-down behavior of curses.wrapper
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        # reset cursor visibility
        curses.curs_set(1)

    @property
    def stdscr(self):
        if not self._stdscr:
            raise RuntimeError("Screen must be initialized before being accessed")
        return self._stdscr
