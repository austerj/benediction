import pytest

from benediction import errors
from benediction.window import Window


def test_overflow():
    w = Window()
    height, width = 10, 10

    # raises error due to missing initscr - can test overflow detection by avoiding reaching
    # internal curses window access via triggering prior validation exceptions
    try:
        w.set_dimensions(0, 0, width, height)
    except:
        pass

    with pytest.raises(errors.WindowOverflowError):
        # set width explicitly to suppress auto wrap (horizontal overflow)
        w.print("a" * (width + 1), wrap_width=(width + 1), clip_overflow_x=False)

    with pytest.raises(errors.WindowOverflowError):
        # more chars than available on window (vertical overflow)
        w.print("a" * (height * width + 1), clip_overflow_y=False)

    with pytest.raises(errors.WindowNotInitializedError):
        # runtime error (due to missing initscr) - but no overflow
        w.print("a" * width, wrap_width=width)

    with pytest.raises(errors.WindowNotInitializedError):
        # no overflow due to clipping
        w.print("a" * (width + 1), wrap_width=(width + 1))
