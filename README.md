# Study Planner

A desktop study-tracking application built with **Tkinter** (via `ttkbootstrap`), designed to help you log study sessions per subject, visualize your progress, and review your history — with full support for Persian/Arabic (RTL) subject names.

## Features

- **Add Study** — log a study session with subject, date, and duration (hours/minutes), plus a GitHub-style **activity heatmap** showing daily study intensity across the year.
- **Subjects** — manage your subject list: add, rename, and delete subjects.
- **Reports** — view study distribution as a **donut chart** (matplotlib), filter by date range, see per-subject percentages, and check total/day-detail summaries. Includes correct rendering of Persian/Arabic subject names using `arabic-reshaper` and `python-bidi`.
- **Edit Logs** — browse saved records by date, edit durations inline, or delete entries.
- Dark UI theme (`darkly`) via `ttkbootstrap`, with a responsive layout that resizes charts on window resize.

## Project Structure

```
study_planner/
├── main.py                  # Application entry point
├── config.py                 # Paths and app-wide constants
├── database.py                # SQLite database manager (used by default)
├── mongodb_database.py     # MongoDB database manager (optional alternative backend)
├── requirements.txt
├── StudyPlanner.spec         # PyInstaller build spec
├── gui/
│   ├── main_window.py         # Main window / notebook tabs
│   ├── add_log_frame.py       # Add Study tab + heatmap widget
│   ├── manage_subjects_frame.py  # Subjects tab
│   ├── report_frame.py        # Reports tab + donut chart
│   └── edit_logs_frame.py     # Edit Logs tab
├── models/
│   └── subject.py             # Subject data model
├── utils/
│   └── helpers.py             # Date/time formatting helpers
└── assets/
    └── icons/                 # App icons
```

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`:
  - `matplotlib>=3.8`
  - `arabic-reshaper>=3.0`
  - `python-bidi>=0.6`
- `ttkbootstrap` (GUI toolkit)
- SQLite is used via Python's built-in `sqlite3` module — no separate database server needed.
- `pymongo` is only required if you switch to the optional MongoDB backend (see `mongodb_database.py`).

## Installation

```bash
git clone <repository-url>
cd study_planner
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

On first launch, a local SQLite database (`study_planner.db`) is created automatically in the project directory to store subjects and study logs. No separate database server setup is required.

> **Note:** The project also includes `mongodb_database.py`, an alternative `DatabaseManager` implementation backed by MongoDB, kept for reference/future use. It is **not** used by default — `main.py` imports from `database.py` (SQLite).

## Building a Standalone Executable

The project includes a `StudyPlanner.spec` file for packaging with [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller StudyPlanner.spec
```

The built executable will be placed in the `dist/` folder.

## Notes

- Persian/Arabic text shaping for chart legends is handled via `arabic_reshaper` + `python-bidi`, since matplotlib does not perform RTL shaping natively.
- The heatmap and donut chart are rebuilt dynamically when subjects or logs change, keeping all tabs in sync.

## License

Add your preferred license here (e.g., MIT).