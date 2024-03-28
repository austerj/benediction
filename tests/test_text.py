from benediction.text import align, simple_wrap

test_strs = (
    "  HEYY",
    "WHAT TTT",
    "  SUP ",
)
test_str = "ABC DEFG  HI JKLMN O PQ"


def test_align():
    assert align(test_strs, "left") == (
        "HEYY    ",
        "WHAT TTT",
        "SUP     ",
    )

    assert align(test_strs, "center") == (
        "  HEYY  ",
        "WHAT TTT",
        "  SUP   ",
    )

    assert align(test_strs, "right") == (
        "    HEYY",
        "WHAT TTT",
        "     SUP",
    )


def test_simple_wrap():
    # lines below width are merged
    assert simple_wrap(test_strs, 8) == (
        "  HEYY W",
        "HAT TTT ",
        " SUP ",
    )

    # original (extra) whitespace is respected
    assert simple_wrap(test_strs, 5) == (
        "  HEY",
        "Y WHA",
        "T TTT",
        "  SUP",
        " ",
    )

    assert simple_wrap(test_strs, 3) == (
        "  H",
        "EYY",
        "WHA",
        "T T",
        "TT ",
        " SU",
        "P ",
    )

    assert simple_wrap(test_strs, 2) == (
        "  ",
        "HE",
        "YY",
        "WH",
        "AT",
        "TT",
        "T ",
        " S",
        "UP",
        " ",
    )

    # width of 1 (special case) produces sequence of individual characters
    assert simple_wrap(test_strs, 1) == (
        " ",
        " ",
        "H",
        "E",
        "Y",
        "Y",
        "W",
        "H",
        "A",
        "T",
        " ",
        "T",
        "T",
        "T",
        " ",
        " ",
        "S",
        "U",
        "P",
        " ",
    )

    # wrapping single string works as expected
    assert simple_wrap(test_str, 4) == (
        "ABC ",
        "DEFG",
        " HI ",
        "JKLM",
        "N O ",
        "PQ",
    )

    assert simple_wrap(test_str, 5) == (
        "ABC D",
        "EFG  ",
        "HI JK",
        "LMN O",
        "PQ",
    )

    # whitespace is left intact
    assert simple_wrap(" ", 5) == (" ",)
    assert simple_wrap("    ", 3) == ("   ", " ")
