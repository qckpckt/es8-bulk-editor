"""Defaults for patch instance and accompanying helper functions.
"""


def default_values(n, multiple) -> tuple:
    """Create a list of n of length multiple"""
    return [n] * multiple


def text_to_ord(text: str):
    assert len(text) <= 16
    return [ord(i) for i in text]


DEFAULT_PATCH_NAME = text_to_ord("BOSS ES-8")
EIGHT_ZEROES = default_values(0, 8)
NINE_ZEROES = default_values(0, 9)
TWELVE_ZEROES = default_values(0, 12)
TWELVE_127S = default_values(127, 12)
TWELVE_80S = default_values(80, 12)
TWELVE_30S = default_values(30, 12)
TWELVE_SEVENS = default_values(7, 12)
TWELVE_TWOS = default_values(2, 12)
SIXTEEN_ZEROES = default_values(0, 16)
SIXTEEN_ONES = default_values(1, 16)
