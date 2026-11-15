"""Stopwatch state for the study timer (no GUI code).

The state is saved in the database settings table on every change and the
elapsed time is computed from the wall clock (time.time()). That makes the
timer survive the app going to the background or even being killed by
Android: when the app is opened again the time is simply recalculated.
"""

from __future__ import annotations

import time
from datetime import date

IDLE, RUNNING, PAUSED = "idle", "running", "paused"
ROUND_STEP_MINUTES = 5


def round_minutes(seconds: float, step: int = ROUND_STEP_MINUTES) -> int:
    """Round to the nearest multiple of `step` minutes (ties go up).

    With step=5: 2.4 min -> 0, 2.5 min -> 5, 7.4 min -> 5, 7.5 min -> 10.
    """
    return int(seconds / 60 / step + 0.5) * step


class StudyTimer:
    def __init__(self, db) -> None:  # db: DatabaseManager
        self.db = db
        self.state = IDLE
        self.subject_id: int | None = None
        self.subject_name = ""
        self.day = date.today().isoformat()
        self._accumulated = 0.0
        self._started_at: float | None = None
        self._load()

    # Persistence
    def _load(self) -> None:
        get = self.db.get_setting
        state = get("timer.state", IDLE)
        if state not in (RUNNING, PAUSED):
            return
        subject_id = get("timer.subject_id", "")
        started = get("timer.started_at", "")
        try:
            self._accumulated = float(get("timer.accumulated", "0") or 0)
            self._started_at = float(started) if started else None
            self.subject_id = int(subject_id) if subject_id else None
        except ValueError:
            self.reset()
            return
        self.state = state
        self.subject_name = get("timer.subject_name", "")
        self.day = get("timer.day", self.day)
        if self.state == RUNNING and self._started_at is None:
            self.reset()

    def _save(self) -> None:
        put = self.db.set_setting
        put("timer.state", self.state)
        put("timer.subject_id", "" if self.subject_id is None else self.subject_id)
        put("timer.subject_name", self.subject_name)
        put("timer.day", self.day)
        put("timer.accumulated", self._accumulated)
        put("timer.started_at", "" if self._started_at is None else self._started_at)

    # Controls
    def start(self, subject_id: int | None, subject_name: str) -> None:
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.day = date.today().isoformat()
        self._accumulated = 0.0
        self._started_at = time.time()
        self.state = RUNNING
        self._save()

    def pause(self) -> None:
        if self.state == RUNNING and self._started_at is not None:
            self._accumulated += max(0.0, time.time() - self._started_at)
            self._started_at = None
            self.state = PAUSED
            self._save()

    def resume(self) -> None:
        if self.state == PAUSED:
            self._started_at = time.time()
            self.state = RUNNING
            self._save()

    def elapsed(self) -> float:
        total = self._accumulated
        if self.state == RUNNING and self._started_at is not None:
            total += max(0.0, time.time() - self._started_at)
        return total

    def reset(self) -> None:
        self.state = IDLE
        self._accumulated = 0.0
        self._started_at = None
        self._save()
