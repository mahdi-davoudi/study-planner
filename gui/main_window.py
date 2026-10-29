"""Main window: sidebar navigation + stacked pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME, ICON_PATH
from gui.add_log_page import AddLogPage
from gui.edit_logs_page import EditLogsPage
from gui.report_page import ReportPage
from gui.subjects_page import SubjectsPage

if TYPE_CHECKING:
    from database import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 720)
        self.setMinimumSize(980, 640)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.add_page = AddLogPage(db)
        self.subjects_page = SubjectsPage(db)
        self.report_page = ReportPage(db)
        self.edit_page = EditLogsPage(db)
        self._pages: list[tuple[str, QWidget]] = [
            ("Add Study", self.add_page),
            ("Subjects", self.subjects_page),
            ("Reports", self.report_page),
            ("Edit Logs", self.edit_page),
        ]

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("root")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 18, 12, 12)
        brand = QLabel(APP_NAME)
        brand.setObjectName("brand")
        sub = QLabel("Track · Review · Improve")
        sub.setObjectName("brandSub")
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems([title for title, _page in self._pages])
        side_layout.addWidget(brand)
        side_layout.addWidget(sub)
        side_layout.addWidget(self.nav, 1)

        self.stack = QStackedWidget()
        for _title, page in self._pages:
            self.stack.addWidget(page)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.nav.setCurrentRow(0)

    def _connect_signals(self) -> None:
        self.add_page.logsChanged.connect(self.report_page.refresh)
        self.add_page.logsChanged.connect(self.edit_page.refresh)
        self.edit_page.logsChanged.connect(self.add_page.refresh)
        self.edit_page.logsChanged.connect(self.report_page.refresh)
        self.subjects_page.subjectsChanged.connect(self.add_page.refresh_subjects)
        self.subjects_page.subjectsChanged.connect(self.report_page.refresh)
        self.subjects_page.subjectsChanged.connect(self.edit_page.refresh)

    def _on_nav_changed(self, row: int) -> None:
        if row < 0:
            return
        self.stack.setCurrentIndex(row)
        # Pages may be stale (e.g. the date changed while the app stayed open).
        page = self._pages[row][1]
        page.refresh()  # type: ignore[attr-defined]
