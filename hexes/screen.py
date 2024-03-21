import curses


class Screen:
    def __enter__(self):
        return self._setup()

    def __exit__(self, type, value, traceback) -> None:
        self._teardown()

    def clear(self):
        self.stdscr.clear()

    def noutrefresh(self):
        self.stdscr.noutrefresh()

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
        return self

    def _teardown(self):
        # replicate tear-down behavior of curses.wrapper
        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    @property
    def stdscr(self):
        if not self._stdscr:
            raise RuntimeError("Screen must be initialized before being accessed")
        return self._stdscr
