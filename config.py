"""Application-wide paths and constants."""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "Study Planner"

# When running as a normal .py file, base the paths on this file's folder.
# When running as a PyInstaller .exe, __file__ points to a temporary folder
# that is wiped on every run, so the database must live next to the real exe
# (sys.executable); bundled read-only resources live in sys._MEIPASS.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR

DB_PATH = str(BASE_DIR / "study_planner.db")
ICON_PATH = RESOURCE_DIR / "assets" / "icons" / "icon.ico"

# Study-time input limits (minutes).
SPIN_MAX_MINUTES = 720
SPIN_STEP = 5

DATE_FORMAT = "yyyy-MM-dd"  # Qt display format (matches ISO dates in the DB)
