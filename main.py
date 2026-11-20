"""Entry point for the ES-8 bulk editor GUI.

Usage:  python main.py
If not already running inside the project's .venv, re-launches itself with it.
"""
import os
import sys
from pathlib import Path

VENV_PYTHON = Path(__file__).resolve().parent / ".venv" / "bin" / "python"

if sys.prefix == sys.base_prefix and VENV_PYTHON.exists():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

from bulk_editor.gui import main  # noqa: E402

if __name__ == "__main__":
    main()
