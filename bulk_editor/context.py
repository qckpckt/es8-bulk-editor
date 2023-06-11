"""Helper functions and related classes for the context object of the cli."""

from dataclasses import dataclass

from . import database as db


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


@dataclass
class AppContext:
    user_prefs: db.Es8Table
    templates: db.Es8Table
