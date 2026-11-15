from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import Card, page_title
from i18n import tr

if TYPE_CHECKING:
    from database import DatabaseManager


class SubjectsPage(QWidget):
    subjectsChanged = Signal()

    def __init__(self, db: DatabaseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self._subjects: list[dict] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)
        root.addWidget(page_title(tr("sub.title")))

        add_card = Card(tr("sub.add_card"))
        add_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("sub.placeholder"))
        self.name_edit.returnPressed.connect(self.add_subject)
        add_btn = QPushButton(tr("sub.add_btn"))
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.add_subject)
        add_row.addWidget(self.name_edit, 1)
        add_row.addWidget(add_btn)
        add_card.add_layout(add_row)
        root.addWidget(add_card)

        list_card = Card(tr("sub.list_card"))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr("sub.col_name"), tr("sub.col_added")])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemDoubleClicked.connect(lambda _item: self.rename_selected())
        self.table.itemSelectionChanged.connect(self._update_buttons)
        list_card.add(self.table, 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.rename_btn = QPushButton(tr("sub.rename"))
        self.rename_btn.clicked.connect(self.rename_selected)
        self.delete_btn = QPushButton(tr("sub.delete"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_selected)
        actions.addWidget(self.rename_btn)
        actions.addWidget(self.delete_btn)
        list_card.add_layout(actions)
        root.addWidget(list_card, 1)
        self._update_buttons()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._subjects = self.db.get_subjects()
        self.table.setRowCount(len(self._subjects))
        for row, subject in enumerate(self._subjects):
            name_item = QTableWidgetItem(subject["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, subject["_id"])
            added = QTableWidgetItem(str(subject.get("created_at", ""))[:10])
            added.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, added)
        self._update_buttons()

    def _update_buttons(self) -> None:
        has_selection = self._selected_subject() is not None
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _selected_subject(self) -> dict | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._subjects) and self.table.selectedItems():
            return self._subjects[row]
        return None

    # ------------------------------------------------------------------
    def add_subject(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, tr("common.error"), tr("sub.enter_name"))
            return
        if name in {s["name"] for s in self.db.get_subjects()}:
            QMessageBox.information(self, tr("common.notice"), tr("sub.exists"))
            return
        self.db.add_subject(name)
        self.name_edit.clear()
        self.refresh()
        self.subjectsChanged.emit()

    def rename_selected(self) -> None:
        subject = self._selected_subject()
        if subject is None:
            return
        new_name, ok = QInputDialog.getText(
            self,
            tr("sub.rename_title"),
            tr("sub.new_name"),
            QLineEdit.EchoMode.Normal,
            subject["name"],
        )
        new_name = new_name.strip()
        if not ok or not new_name or new_name == subject["name"]:
            return
        if not self.db.rename_subject(subject["_id"], new_name):
            QMessageBox.warning(self, tr("common.error"), tr("sub.exists_other"))
            return
        self.refresh()
        self.subjectsChanged.emit()

    def delete_selected(self) -> None:
        subject = self._selected_subject()
        if subject is None:
            return
        answer = QMessageBox.question(
            self,
            tr("common.confirm_delete"),
            tr("sub.delete_q", name=subject["name"]),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.db.delete_subject(subject["_id"])
        self.refresh()
        self.subjectsChanged.emit()