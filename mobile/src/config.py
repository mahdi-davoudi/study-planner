from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Study Planner"

# On a phone the app folder is read-only, so the database must live in the
# persistent data folder that Flet provides through this environment variable.
# (It is also set when you use `flet run` on your computer.)
_data_dir = os.getenv("FLET_APP_STORAGE_DATA")
BASE_DIR = Path(_data_dir) if _data_dir else Path(__file__).resolve().parent
BASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(BASE_DIR / "study_planner.db")

# Study-time input limits (minutes).
SPIN_MAX_MINUTES = 720
SPIN_STEP = 5
