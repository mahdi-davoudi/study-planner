"""'Add Study' page: stats, activity heatmap and the daily log form."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import DATE_FORMAT, SPIN_MAX_MINUTES, SPIN_STEP
from gui import theme
from gui.heatmap import HeatmapView, HeatmapWidget
from gui.widgets import (
    Card,
    NoWheelSpinBox,
    StatCard,
    align_visual_right,
    muted_label,
    page_title,
    scrollable,
)
from utils.helpers import minutes_to_hm_text

if TYPE_CHECKING:
    from database import DatabaseManager


class AddLogPage(QWidget):
    """Log today's study time per subject and browse the yearly activity."""

    logsChanged = Signal()

    def __init__(self, db: DatabaseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self._spins: dict[int, NoWheelSpinBox] = {}
        self._build_ui()
        self.refresh_subjects()
        self.refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header: title on the left, quick stats on the right.
        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(page_title("Add Study Log"))
        header.addStretch(1)
        self.streak_card = StatCard("Streak", theme.ORANGE)
        self.week_card = StatCard("This week", theme.ACCENT)
        self.month_card = StatCard("This month", theme.SUCCESS)
        for card in (self.streak_card, self.week_card, self.month_card):
            card.setFixedWidth(150)
            header.addWidget(card)
        root.addLayout(header)

        # Full-width heatmap so the whole year is visible on a normal window.
        self.heatmap_card = Card("Study Activity")
        self.heatmap = HeatmapWidget()
        self.heatmap_view = HeatmapView(self.heatmap)
        self.heatmap.dayClicked.connect(self._on_day_clicked)
        self.heatmap_card.add(self.heatmap_view)
        root.addWidget(self.heatmap_card)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        self.details_card = Card("Day details")
        self.details_label = QLabel(
            "Click a day on the heatmap to load its date and see what was studied."
        )
        self.details_label.setTextFormat(Qt.TextFormat.PlainText)
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.details_card.add(scrollable(self.details_label), 1)
        body.addWidget(self.details_card, 2)

        right = QVBoxLayout()
        body.addLayout(right, 3)
        self._build_right(right)

    def _build_right(self, right: QVBoxLayout) -> None:
        card = Card("Log study time")

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Date"))
        date_row.addStretch(1)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat(DATE_FORMAT)
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(140)
        date_row.addWidget(self.date_edit)
        card.add_layout(date_row)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 6, 0)
        self._rows_layout.setSpacing(6)
        card.add(scrollable(self._rows_container), 1)

        self.save_btn = QPushButton("Save Study Log")
        self.save_btn.setObjectName("primary")
        self.save_btn.setShortcut("Ctrl+Return")
        self.save_btn.clicked.connect(self.submit)
        card.add(self.save_btn)

        self.status_label = muted_label("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.status_label)

        right.addWidget(card, 1)

    # ------------------------------------------------------------------
    # Subjects form
    # ------------------------------------------------------------------
    def refresh_subjects(self) -> None:
        """Rebuild the subject rows, keeping minutes already typed in."""
        previous = {sid: spin.value() for sid, spin in self._spins.items()}
        self._spins.clear()

        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        subjects = self.db.get_subjects()
        self.save_btn.setEnabled(bool(subjects))

        if not subjects:
            self._rows_layout.addWidget(
                muted_label("No subjects yet. Add some from the Subjects page first.")
            )
            self._rows_layout.addStretch(1)
            return

        for subject in subjects:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)

            name = QLabel(subject["name"])
            name.setTextFormat(Qt.TextFormat.PlainText)
            name.setWordWrap(True)
            align_visual_right(name)
            layout.addWidget(name, 1)

            spin = NoWheelSpinBox()
            spin.setRange(0, SPIN_MAX_MINUTES)
            spin.setSingleStep(SPIN_STEP)
            spin.setSuffix(" min")
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setFixedWidth(120)
            spin.setValue(previous.get(subject["_id"], 0))
            layout.addWidget(spin)

            self._spins[subject["_id"]] = spin
            self._rows_layout.addWidget(row)
        self._rows_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Stats / heatmap
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        today = date.today()
        self.date_edit.setMaximumDate(QDate.currentDate())

        streak = self.db.get_current_streak()
        self.streak_card.set_value(f"{streak} day{'s' if streak != 1 else ''}")
        self.week_card.set_value(minutes_to_hm_text(self.db.get_week_total()))
        self.month_card.set_value(minutes_to_hm_text(self.db.get_month_total()))

        jan1 = today.replace(month=1, day=1)
        totals = self.db.get_daily_totals(jan1.isoformat(), today.isoformat())
        self.heatmap.set_data(totals, today)
        self.heatmap_card.set_title(f"Study Activity ({today.year})")
        self.heatmap_view.scroll_to_end_later()

        # Keep the details panel in sync with the date currently selected.
        if self.heatmap._selected is not None:
            self._show_day_details(self.heatmap._selected.isoformat())

    def _on_day_clicked(self, iso: str) -> None:
        self.date_edit.setDate(QDate.fromString(iso, "yyyy-MM-dd"))
        self._show_day_details(iso)

    def _show_day_details(self, iso: str) -> None:
        logs = self.db.get_logs_by_date(iso)
        self.details_card.set_title(f"Day details - {iso}")
        if not logs:
            self.details_label.setText("No study records for this day.")
            return
        lines = [
            f"•  {log['subject_name']}: {minutes_to_hm_text(log['duration_minutes'])}"
            for log in logs
        ]
        total = sum(log["duration_minutes"] for log in logs)
        lines.append(f"\nTotal: {minutes_to_hm_text(total)}")
        self.details_label.setText("\n".join(lines))

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def submit(self) -> None:
        subjects = {s["_id"]: s["name"] for s in self.db.get_subjects()}
        entries = [
            {
                "subject_id": sid,
                "subject_name": subjects[sid],
                "duration_minutes": spin.value(),
            }
            for sid, spin in self._spins.items()
            if spin.value() > 0 and sid in subjects
        ]
        if not entries:
            self._set_status("Enter minutes for at least one subject.", theme.WARNING)
            return

        iso = self.date_edit.date().toString("yyyy-MM-dd")
        count = self.db.add_logs_bulk(iso, entries)
        total = sum(e["duration_minutes"] for e in entries)

        for spin in self._spins.values():
            spin.setValue(0)

        self._set_status(
            f"Saved {count} subject{'s' if count != 1 else ''} for {iso} "
            f"(total {minutes_to_hm_text(total)}).",
            theme.SUCCESS,
        )
        self.heatmap.set_selected(date.fromisoformat(iso))
        self.refresh()
        self._show_day_details(iso)
        self.logsChanged.emit()

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(text)
