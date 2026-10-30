from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from config import ICON_PATH
from gui import theme
from gui.add_log_page import AddLogPage
from gui.edit_logs_page import EditLogsPage
from gui.report_page import ReportPage
from gui.subjects_page import SubjectsPage
from gui.widgets import globe_icon
from i18n import LANGUAGES, manager, tr

if TYPE_CHECKING:
    from database import DatabaseManager

SIDEBAR_WIDTH = 240 


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.db = db
        self.resize(1180, 720)
        self.setMinimumSize(980, 640)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._build_content()
        manager.languageChanged.connect(self._on_language_changed)

    # (Re)building everything that contains translated text
    def _build_content(self) -> None:
        self.setWindowTitle(tr("app.name"))
        self.add_page = AddLogPage(self.db)
        self.subjects_page = SubjectsPage(self.db)
        self.report_page = ReportPage(self.db)
        self.edit_page = EditLogsPage(self.db)
        self._pages: list[tuple[str, QWidget]] = [
            (tr("nav.add"), self.add_page),
            (tr("nav.subjects"), self.subjects_page),
            (tr("nav.reports"), self.report_page),
            (tr("nav.edit"), self.edit_page),
        ]
        self._build_ui()
        self._connect_signals()

    def _on_language_changed(self, _language: str) -> None:
        QTimer.singleShot(0, self._rebuild)

    def _rebuild(self) -> None:
        row = max(self.nav.currentRow(), 0)
        self._build_content()  
        self.nav.setCurrentRow(row)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("root")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        if manager.is_rtl:  
            sidebar.setStyleSheet(
                "QWidget#sidebar { border-right: none; "
                f"border-left: 1px solid {theme.BORDER}; }}"
            )
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 18, 12, 12)

        # Header: brand + tagline on one side, language button on the other.
        header = QHBoxLayout()
        header.setSpacing(6)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        brand = QLabel(tr("app.name"))
        brand.setObjectName("brand")
        sub = QLabel(tr("app.tagline"))
        sub.setObjectName("brandSub")
        titles.addWidget(brand)
        titles.addWidget(sub)
        header.addLayout(titles, 1)
        header.addWidget(self._make_language_button(), 0, Qt.AlignmentFlag.AlignTop)
        side_layout.addLayout(header)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.addItems([title for title, _page in self._pages])
        side_layout.addWidget(self.nav, 1)

        self.stack = QStackedWidget()
        for _title, page in self._pages:
            self.stack.addWidget(page)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.nav.setCurrentRow(0)

    def _make_language_button(self) -> QToolButton:
        button = QToolButton()
        button.setObjectName("langBtn")
        button.setIcon(globe_icon(theme.TEXT))
        button.setIconSize(QSize(18, 18))
        button.setText(tr("lang.short"))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tr("lang.switch_to", name=LANGUAGES[manager.other_language]))
        button.clicked.connect(lambda _checked=False: manager.toggle())
        return button

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
        page.refresh()  