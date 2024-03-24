from hexes.text import align, simple_wrap

test_str = [
    "  HEYY",
    "WHAT TTT",
    "  SUP ",
]


def test_left_align():
    assert align(test_str, "left") == [
        "HEYY    ",
        "WHAT TTT",
        "SUP     ",
    ]

    assert align(test_str, "center") == [
        "  HEYY  ",
        "WHAT TTT",
        "  SUP   ",
    ]

    assert align(test_str, "right") == [
        "    HEYY",
        "WHAT TTT",
        "     SUP",
    ]


def test_simple_wrap():
    # lines below width are merged
    assert simple_wrap(test_str, 8) == [
        "  HEYY W",
        "HAT TTT ",
        " SUP ",
    ]

    # original (extra) whitespace is respected
    assert simple_wrap(test_str, 5) == [
        "  HEY",
        "Y WHA",
        "T TTT",
        "  SUP",
        " ",
    ]

    assert simple_wrap(test_str, 3) == [
        "  H",
        "EYY",
        "WHA",
        "T T",
        "TT ",
        " SU",
        "P ",
    ]

    assert simple_wrap(test_str, 2) == [
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
    ]

    # width of 1 (special case) produces sequence of individual characters
    assert simple_wrap(test_str, 1) == [
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
    ]
