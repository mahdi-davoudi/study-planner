from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import DATE_FORMAT, SPIN_MAX_MINUTES, SPIN_STEP
from gui.widgets import Card, muted_label, page_title
from i18n import manager, tr
from utils.helpers import minutes_to_hm_text

if TYPE_CHECKING:
    from database import DatabaseManager


class EditLogsPage(QWidget):
    logsChanged = Signal()

    def __init__(self, db: DatabaseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self._logs: list[dict] = []
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_title(tr("edit.title")))

        controls = Card(tr("edit.day_card"))
        row = QHBoxLayout()
        row.setSpacing(8)
        # In a right-to-left layout the first widget sits on the right, so the
        # arrows must point the other way to keep "previous/next" intuitive.
        rtl = manager.is_rtl
        prev_btn = QPushButton("›" if rtl else "‹")
        prev_btn.setFixedWidth(40)
        prev_btn.clicked.connect(lambda: self._shift_day(-1))
        next_btn = QPushButton("‹" if rtl else "›")
        next_btn.setFixedWidth(40)
        next_btn.clicked.connect(lambda: self._shift_day(1))
        today_btn = QPushButton(tr("common.today"))
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat(DATE_FORMAT)
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(140)
        self.date_edit.dateChanged.connect(lambda _d: self.refresh())

        for widget in (prev_btn, self.date_edit, next_btn, today_btn):
            row.addWidget(widget)
        row.addStretch(1)
        controls.add_layout(row)
        root.addWidget(controls)

        table_card = Card(tr("edit.records_card"))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr("rep.col_subject"), tr("rep.col_time")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemDoubleClicked.connect(lambda _i: self.edit_selected())
        self.table.itemSelectionChanged.connect(self._update_buttons)
        table_card.add(self.table, 1)

        self.empty_label = muted_label(tr("edit.empty"))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_card.add(self.empty_label)

        actions = QHBoxLayout()
        actions.addWidget(muted_label(tr("edit.tip"), wrap=False))
        actions.addStretch(1)
        self.edit_btn = QPushButton(tr("edit.edit_btn"))
        self.edit_btn.setObjectName("warning")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton(tr("edit.delete_btn"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_selected)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        table_card.add_layout(actions)
        root.addWidget(table_card, 1)
        self._update_buttons()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self.date_edit.setMaximumDate(QDate.currentDate())
        iso = self.date_edit.date().toString("yyyy-MM-dd")
        self._logs = self.db.get_logs_by_date(iso)

        self.table.setRowCount(len(self._logs))
        for row, log in enumerate(self._logs):
            name = QTableWidgetItem(log["subject_name"])
            name.setData(Qt.ItemDataRole.UserRole, log["_id"])
            time_item = QTableWidgetItem(minutes_to_hm_text(log["duration_minutes"]))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, time_item)

        self.empty_label.setVisible(not self._logs)
        self._update_buttons()

    def _shift_day(self, days: int) -> None:
        self.date_edit.setDate(self.date_edit.date().addDays(days))

    def _update_buttons(self) -> None:
        has_selection = self._selected_log() is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _selected_log(self) -> dict | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._logs) and self.table.selectedItems():
            return self._logs[row]
        return None

    def delete_selected(self) -> None:
        log = self._selected_log()
        if log is None:
            return
        answer = QMessageBox.question(
            self,
            tr("common.confirm_delete"),
            tr(
                "edit.delete_q",
                name=log["subject_name"],
                time=minutes_to_hm_text(log["duration_minutes"]),
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_log(log["_id"])
        self.refresh()
        self.logsChanged.emit()

    def edit_selected(self) -> None:
        log = self._selected_log()
        if log is None:
            return
        minutes, ok = QInputDialog.getInt(
            self,
            tr("edit.dialog_title"),
            tr("edit.minutes_prompt", name=log["subject_name"]),
            int(log["duration_minutes"]),
            1,
            SPIN_MAX_MINUTES,
            SPIN_STEP,
        )
        if not ok or minutes == log["duration_minutes"]:
            return
        self.db.update_log_duration(log["_id"], minutes)
        self.refresh()
        self.logsChanged.emit()