# Study Planner

A desktop app for tracking how much you study each subject, built with **Python, PySide6 (Qt) and SQLite**.
Log your daily study time, watch your progress on a GitHub-style activity heatmap, and review where your time goes with charts and statistics.

Persian (RTL) subject names are fully supported.

## Features

- **Add Study**: log minutes per subject for any day (up to today). Saving the same subject twice on one day adds the minutes to the existing record instead of creating a duplicate.
- **Activity heatmap**: the whole current year at a glance. Click a day to load its date and see what you studied; hover for a tooltip; scroll sideways with the mouse wheel on small windows.
- **Quick stats**: current streak, this week and this month. The streak keeps counting if you haven't studied *yet* today.
- **Subjects**: add, rename and delete subjects. Renaming also updates your past records, so history is never split in two.
- **Reports**: donut chart, per-subject table and summary statistics for any date range, with presets (Today, 7 days, 30 days, This month, This year, All time).
- **Edit Logs**: browse a day's records, change their duration or delete them.
- **Dark theme**, consistent across all pages.

## Requirements

- Python 3.10 or newer (developed on 3.12 and 3.14)
- [PySide6](https://pypi.org/project/PySide6/) (the only dependency)

## Installation

```bash
# 1. Clone or download the project, then enter its folder
cd study_planner

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 3. Install the dependency
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The database file `study_planner.db` is created automatically on the first run.

## Usage tips

| Action | How |
|---|---|
| Save the log | Click **Save Study Log** or press `Ctrl+Enter` |
| See what you studied on a day | Click that day on the heatmap |
| Scroll the heatmap sideways | Mouse wheel over the heatmap, or drag its scrollbar |
| Rename a subject | Double-click it on the **Subjects** page |
| Edit a saved record | Double-click it on the **Edit Logs** page |

Heatmap colours: no study, up to 30 min, up to 90 min, up to 3 h, more than 3 h.

## Tests

```bash
pip install pytest
pytest
```

The tests cover the database layer (streaks, renaming, merging records, percentages) and use an in-memory SQLite database, so they never touch your real data.

## Build a Windows executable

```bash
pip install pyinstaller
pyinstaller --clean StudyPlanner.spec
```

The result is `dist/StudyPlanner.exe` (a single file, no console window). The database is stored **next to the executable**, so keep `study_planner.db` in the same folder as the `.exe` if you move it.

## Data and backup

All data lives in one SQLite file, `study_planner.db`:

- When running from source, it is in the project folder.
- When running the built `.exe`, it is next to the executable.

To back up your data, copy that file while the app is closed. To move to another computer, copy it next to the app there.

> If your project folder is synced by OneDrive, Dropbox or Google Drive, close the app before syncing, or keep the database outside the synced folder. Cloud sync can conflict with a database file that is being written.

## Project structure

```
study_planner/
├── main.py                  # entry point
├── config.py                # paths and constants (DB location, input limits)
├── database.py              # SQLite layer: subjects, logs, reports, streak
├── requirements.txt
├── StudyPlanner.spec        # PyInstaller build configuration
├── assets/
│   └── icons/icon.ico
├── utils/
│   └── helpers.py           # time formatting helpers
├── gui/
│   ├── main_window.py       # sidebar navigation + pages
│   ├── theme.py             # dark palette and stylesheet
│   ├── widgets.py           # shared widgets (cards, stat cards, ...)
│   ├── heatmap.py           # yearly activity heatmap
│   ├── donut.py             # donut chart
│   ├── add_log_page.py      # "Add Study" page
│   ├── subjects_page.py     # "Subjects" page
│   ├── report_page.py       # "Reports" page
│   └── edit_logs_page.py    # "Edit Logs" page
└── tests/
    └── test_database.py
```

`database.py` and `utils/` have no GUI dependencies, so the logic can be tested and reused independently of the interface.

## Troubleshooting

- **`ModuleNotFoundError: PySide6`**: the virtual environment is not active, or `pip install -r requirements.txt` was not run.
- **No PySide6 wheel for your Python version**: create the virtual environment with Python 3.12 or 3.13.
- **The `.exe` closes immediately**: in `StudyPlanner.spec` set `console=True`, rebuild, and run the exe from a terminal to see the error.
- **Access denied while building**: close the running `StudyPlanner.exe` (and let cloud sync finish) before running PyInstaller.

## License

Add your license here.
