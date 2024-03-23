from hexes.text import align

test_str = [
    "  HEYY",
    "WHATTTTT",
    "  SUP ",
]


def test_left_align():
    assert align(test_str, "left") == [
        "HEYY    ",
        "WHATTTTT",
        "SUP     ",
    ]

    assert align(test_str, "center") == [
        "  HEYY  ",
        "WHATTTTT",
        "  SUP   ",
    ]

    assert align(test_str, "right") == [
        "    HEYY",
        "WHATTTTT",
        "     SUP",
    ]
