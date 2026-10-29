"""'Reports' page: donut chart, per-subject table and summary statistics."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import DATE_FORMAT
from gui import theme
from gui.donut import DonutChart
from gui.widgets import Card, StatCard, muted_label, page_title, swatch_icon
from utils.helpers import minutes_to_hm_text

if TYPE_CHECKING:
    from database import DatabaseManager


def _to_qdate(day: date) -> QDate:
    return QDate(day.year, day.month, day.day)


class ReportPage(QWidget):
    def __init__(self, db: DatabaseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self._all_time = False
        self._build_ui()
        today = date.today()
        self._set_range(today.replace(day=1), today)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_title("Study Report"))

        # --- Date range ---
        range_card = Card("Date range")
        row = QHBoxLayout()
        row.setSpacing(8)
        self.from_edit = self._make_date_edit()
        self.to_edit = self._make_date_edit()
        row.addWidget(QLabel("From"))
        row.addWidget(self.from_edit)
        row.addSpacing(8)
        row.addWidget(QLabel("To"))
        row.addWidget(self.to_edit)
        row.addStretch(1)

        today = date.today()
        presets = (
            ("Today", lambda: self._set_range(date.today(), date.today())),
            ("7 days", lambda: self._set_range(date.today() - timedelta(days=6), date.today())),
            ("30 days", lambda: self._set_range(date.today() - timedelta(days=29), date.today())),
            ("This month", lambda: self._set_range(date.today().replace(day=1), date.today())),
            ("This year", lambda: self._set_range(today.replace(month=1, day=1), date.today())),
            ("All time", lambda: self._set_range(None, None)),
        )
        for text, handler in presets:
            button = QPushButton(text)
            button.setObjectName("chip")
            button.clicked.connect(handler)
            row.addWidget(button)
        range_card.add_layout(row)
        self.range_label = muted_label("", wrap=False)
        range_card.add(self.range_label)
        root.addWidget(range_card)

        # --- Chart + table ---
        middle = QHBoxLayout()
        middle.setSpacing(16)

        chart_card = Card("Study distribution")
        self.donut = DonutChart()
        chart_card.add(self.donut, 1)
        middle.addWidget(chart_card, 5)

        table_card = Card("Results")
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Subject", "Study time", "Share"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table_card.add(self.table, 1)
        middle.addWidget(table_card, 6)
        root.addLayout(middle, 1)

        # --- Statistics ---
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.total_card = StatCard("Total", theme.SUCCESS)
        self.average_card = StatCard("Average per subject", theme.ACCENT)
        self.most_card = StatCard("Most studied", theme.ORANGE, small=True)
        self.least_card = StatCard("Least studied", theme.MUTED, small=True)
        for card in (self.total_card, self.average_card, self.most_card, self.least_card):
            stats.addWidget(card, 1)
        root.addLayout(stats)

    def _make_date_edit(self) -> QDateEdit:
        edit = QDateEdit(QDate.currentDate())
        edit.setCalendarPopup(True)
        edit.setDisplayFormat(DATE_FORMAT)
        edit.setMaximumDate(QDate.currentDate())
        edit.setMinimumWidth(130)
        edit.dateChanged.connect(self._on_date_edited)
        return edit

    # ------------------------------------------------------------------
    # Range handling
    # ------------------------------------------------------------------
    def _set_range(self, start: date | None, end: date | None) -> None:
        """Apply a preset. ``None, None`` means all time."""
        self._all_time = start is None or end is None
        if start is not None and end is not None:
            for edit, value in ((self.from_edit, start), (self.to_edit, end)):
                edit.blockSignals(True)
                edit.setDate(_to_qdate(value))
                edit.blockSignals(False)
        self.refresh()

    def _on_date_edited(self) -> None:
        """Keep From <= To when the user edits either date."""
        self._all_time = False
        sender = self.sender()
        if self.from_edit.date() > self.to_edit.date():
            other = self.to_edit if sender is self.from_edit else self.from_edit
            other.blockSignals(True)
            other.setDate(sender.date())  # type: ignore[union-attr]
            other.blockSignals(False)
        self.refresh()

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        for edit in (self.from_edit, self.to_edit):
            edit.setMaximumDate(QDate.currentDate())

        if self._all_time:
            summary = self.db.get_subject_percentages()
            self.range_label.setText("Showing: all time")
        else:
            start = self.from_edit.date().toString("yyyy-MM-dd")
            end = self.to_edit.date().toString("yyyy-MM-dd")
            summary = self.db.get_subject_percentages(start, end)
            self.range_label.setText(f"Showing: {start}  →  {end}")
        self._apply_summary(summary)

    def _apply_summary(self, summary: list[dict]) -> None:
        colors = [
            QColor(theme.SLICE_COLORS[i % len(theme.SLICE_COLORS)])
            for i in range(len(summary))
        ]

        self.table.setRowCount(len(summary))
        for row, (item, color) in enumerate(zip(summary, colors)):
            name = QTableWidgetItem(swatch_icon(color), item["subject_name"])
            time_item = QTableWidgetItem(minutes_to_hm_text(item["total_minutes"]))
            share = QTableWidgetItem(f"{item['percentage']:.1f}%")
            for cell in (time_item, share):
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, time_item)
            self.table.setItem(row, 2, share)

        self.donut.set_items(
            [(i["subject_name"], i["total_minutes"], c) for i, c in zip(summary, colors)]
        )
        self._update_statistics(summary)

    def _update_statistics(self, summary: list[dict]) -> None:
        if not summary:
            for card in (self.total_card, self.average_card, self.most_card, self.least_card):
                card.set_value("No data")
            return

        total = sum(item["total_minutes"] for item in summary)
        most, least = summary[0], summary[-1]
        self.total_card.set_value(minutes_to_hm_text(total))
        self.average_card.set_value(minutes_to_hm_text(round(total / len(summary))))
        self.most_card.set_value(
            f"{most['subject_name']} ({minutes_to_hm_text(most['total_minutes'])})"
        )
        self.least_card.set_value(
            f"{least['subject_name']} ({minutes_to_hm_text(least['total_minutes'])})"
        )
