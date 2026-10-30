from __future__ import annotations

import time
from datetime import date
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui import theme
from gui.widgets import Card, muted_label, page_title
from i18n import localize_digits, tr
from utils.helpers import minutes_to_hm_text

if TYPE_CHECKING:
    from database import DatabaseManager

ROUND_STEP_MINUTES = 5

IDLE, RUNNING, PAUSED = "idle", "running", "paused"


def round_minutes(seconds: float, step: int = ROUND_STEP_MINUTES) -> int:
    """Round to the nearest multiple of `step` minutes (ties go up).

    Examples (step=5): 2.4 min -> 0, 2.5 min -> 5, 7.4 min -> 5, 7.5 min -> 10.
    """
    return int(seconds / 60 / step + 0.5) * step


class StudyTimer:
    """Stopwatch state. Lives in MainWindow so it survives UI rebuilds
    (language / theme changes). It has no GUI dependencies."""

    def __init__(self) -> None:
        self.state = IDLE
        self.subject_id: int | None = None
        self.subject_name = ""
        self.day: date = date.today()
        self._accumulated = 0.0
        self._started_at: float | None = None

    def start(self, subject_id: int | None, subject_name: str) -> None:
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.day = date.today()
        self._accumulated = 0.0
        self._started_at = time.monotonic()
        self.state = RUNNING

    def pause(self) -> None:
        if self.state == RUNNING and self._started_at is not None:
            self._accumulated += time.monotonic() - self._started_at
            self._started_at = None
            self.state = PAUSED

    def resume(self) -> None:
        if self.state == PAUSED:
            self._started_at = time.monotonic()
            self.state = RUNNING

    def elapsed(self) -> float:
        total = self._accumulated
        if self.state == RUNNING and self._started_at is not None:
            total += time.monotonic() - self._started_at
        return total

    def reset(self) -> None:
        self.state = IDLE
        self._accumulated = 0.0
        self._started_at = None


class TimerPage(QWidget):

    logsChanged = Signal()

    def __init__(
        self, db: DatabaseManager, timer: StudyTimer, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.timer = timer
        self._build_ui()
        self.refresh_subjects()

        self._tick = QTimer(self)
        self._tick.setInterval(200)
        self._tick.timeout.connect(self._update_display)
        self._tick.start()
        self._update_display()

    # UI
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_title(tr("timer.title")))

        card = Card(tr("timer.card"))
        card.setMaximumWidth(640)

        subject_row = QHBoxLayout()
        subject_row.addWidget(QLabel(tr("timer.subject")))
        self.combo = QComboBox()
        self.combo.setMinimumWidth(240)
        subject_row.addWidget(self.combo, 1)
        card.add_layout(subject_row)

        self.display = QLabel("00:00:00")
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.display.setStyleSheet(
            f"font-size: 54pt; font-weight: 700; color: {theme.TEXT};"
        )
        card.add(self.display)

        self.state_label = muted_label("")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.state_label)

        self.preview_label = QLabel("")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {theme.ACCENT}; font-weight: 600;")
        card.add(self.preview_label)

        buttons = QHBoxLayout()
        self.main_btn = QPushButton(tr("timer.start"))
        self.main_btn.setObjectName("primary")
        self.main_btn.clicked.connect(self._on_main_clicked)
        self.stop_btn = QPushButton(tr("timer.stop"))
        self.stop_btn.setObjectName("warning")
        self.stop_btn.clicked.connect(self._on_stop)
        self.discard_btn = QPushButton(tr("timer.discard"))
        self.discard_btn.clicked.connect(self._on_discard)
        buttons.addWidget(self.main_btn, 2)
        buttons.addWidget(self.stop_btn, 2)
        buttons.addWidget(self.discard_btn, 1)
        card.add_layout(buttons)

        self.status_label = muted_label("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.status_label)

        root.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

    # Subjects
    def refresh_subjects(self) -> None:
        current = self.timer.subject_id if self.timer.state != IDLE else self.combo.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        for subject in self.db.get_subjects():
            self.combo.addItem(subject["name"], subject["_id"])
        index = self.combo.findData(current)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        self.combo.blockSignals(False)
        self._update_controls()

    def refresh(self) -> None:
        self.refresh_subjects()
        self._update_display()

    # State -> widgets
    def _update_controls(self) -> None:
        state = self.timer.state
        has_subjects = self.combo.count() > 0

        self.combo.setEnabled(state == IDLE and has_subjects)
        self.stop_btn.setEnabled(state != IDLE)
        self.discard_btn.setEnabled(state != IDLE)

        if state == IDLE:
            self.main_btn.setText(tr("timer.start"))
            self.main_btn.setEnabled(has_subjects)
            self.state_label.setText(
                tr("timer.idle") if has_subjects else tr("add.no_subjects")
            )
        elif state == RUNNING:
            self.main_btn.setText(tr("timer.pause"))
            self.main_btn.setEnabled(True)
            self.state_label.setText(tr("timer.running", name=self.timer.subject_name))
        else:
            self.main_btn.setText(tr("timer.resume"))
            self.main_btn.setEnabled(True)
            self.state_label.setText(tr("timer.paused", name=self.timer.subject_name))

    def _update_display(self) -> None:
        seconds = int(self.timer.elapsed())
        hours, rest = divmod(seconds, 3600)
        minutes, secs = divmod(rest, 60)
        self.display.setText(localize_digits(f"{hours:02d}:{minutes:02d}:{secs:02d}"))

        if self.timer.state == IDLE:
            self.preview_label.setText("")
        else:
            rounded = round_minutes(seconds)
            self.preview_label.setText(
                tr("timer.preview", time=minutes_to_hm_text(rounded))
            )

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)

    # Actions
    def _on_main_clicked(self) -> None:
        state = self.timer.state
        if state == IDLE:
            subject_id = self.combo.currentData()
            if subject_id is None:
                return
            self.timer.start(subject_id, self.combo.currentText())
            self.status_label.setText("")
        elif state == RUNNING:
            self.timer.pause()
        else:
            self.timer.resume()
        self._update_controls()
        self._update_display()

    def _on_stop(self) -> None:
        if self.timer.state == IDLE:
            return
        seconds = self.timer.elapsed()
        day = self.timer.day
        subject_id = self.timer.subject_id
        fallback_name = self.timer.subject_name
        self.timer.reset()
        self._update_controls()
        self._update_display()

        minutes = round_minutes(seconds)
        if minutes <= 0:
            self._set_status(tr("timer.too_short"), theme.WARNING)
            return

        # The subject may have been renamed or deleted while the timer ran.
        subjects = {s["_id"]: s["name"] for s in self.db.get_subjects()}
        if subject_id not in subjects:
            subject_id = None
        name = subjects.get(subject_id, fallback_name)

        iso = day.isoformat()
        self.db.add_logs_bulk(
            iso,
            [{"subject_id": subject_id, "subject_name": name, "duration_minutes": minutes}],
        )
        day_total = sum(
            log["duration_minutes"]
            for log in self.db.get_logs_by_date(iso)
            if log["subject_id"] == subject_id and log["subject_name"] == name
        )
        self._set_status(
            tr(
                "timer.saved",
                time=minutes_to_hm_text(minutes),
                name=name,
                total=minutes_to_hm_text(day_total),
            ),
            theme.SUCCESS,
        )
        self.logsChanged.emit()

    def _on_discard(self) -> None:
        if self.timer.state == IDLE:
            return
        answer = QMessageBox.question(
            self, tr("common.notice"), tr("timer.discard_q")
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.timer.reset()
        self._update_controls()
        self._update_display()