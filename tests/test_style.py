import curses

from benediction.style import Style


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


def test_inheritance():
    # bold style is bold
    parent_style = Style(bold=True)
    assert parent_style.attr == curses.A_BOLD

    # inheriting from parent style combines flags
    assert parent_style.inherit(italic=True).attr == curses.A_BOLD | curses.A_ITALIC

    # but disabling flag will replace parent flag
    assert parent_style.inherit(italic=True, bold=False).attr == curses.A_ITALIC
