"""Defaults for patch instance and accompanying helper functions.
"""
from pathlib import Path

from .mappings import text_to_ord


def values(n, multiple) -> list:
    """Create a list of n of length multiple"""
    return [n] * multiple


def local_storage() -> str:
    home_dir = Path.home()
    local_storage = home_dir / ".es8"
    local_storage.mkdir(parents=True, exist_ok=True)
    return str(local_storage)


def patch_filepath() -> str:
    script_path = Path(__file__).resolve()
    app_dir = script_path.parent
    return str(app_dir / "templates" / "global_defaults.json")


DEFAULT_PATCH_NAME = text_to_ord("BOSS ES-8")
EIGHT_ZEROES = values(0, 8)
NINE_ZEROES = values(0, 9)
TWELVE_ZEROES = values(0, 12)
TWELVE_127S = values(127, 12)
TWELVE_80S = values(80, 12)
TWELVE_30S = values(30, 12)
TWELVE_SEVENS = values(7, 12)
TWELVE_TWOS = values(2, 12)
SIXTEEN_ZEROES = values(0, 16)
SIXTEEN_ONES = values(1, 16)
