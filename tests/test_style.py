import curses

from hexes.style import Style


# NOTE: unable to test colors as this requires initscr to register pairs
def test_flag_equivalence():
    # empty style is 0
    assert Style().attr == 0

    # style with no colors and bold flag is equivalent to bold flag
    assert Style(bold=True).attr == curses.A_BOLD

    # false flags do nothing
    assert Style(bold=True, invisible=False).attr == curses.A_BOLD

    # style with no colors and multiple flags is equivalent to bitwise or of flags
    assert Style(bold=True, italic=True).attr == curses.A_BOLD | curses.A_ITALIC
