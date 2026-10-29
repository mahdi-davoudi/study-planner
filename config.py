import os
import sys

# When running as a normal .py file, base the path on this file's folder.
# When running as a PyInstaller .exe, __file__ points to a temporary
# extraction folder that gets wiped every run — so use the real exe's
# location instead (sys.executable), otherwise the database would reset
# every time the program is closed and reopened.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "study_planner.db")

