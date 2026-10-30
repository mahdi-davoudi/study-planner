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
from gui.widgets import globe_icon, theme_icon
from i18n import LANGUAGES, manager, tr

if TYPE_CHECKING:
    from database import DatabaseManager

SIDEBAR_WIDTH = 220


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseManager) -> None:
        super().__init__()
        self.db = db
        self.resize(1180, 720)
        self.setMinimumSize(980, 640)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._build_content()
        # Language and theme changes both rebuild the UI (texts / colours are read at build time).
        manager.languageChanged.connect(self._on_appearance_changed)
        theme.manager.themeChanged.connect(self._on_appearance_changed)

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

    def _on_appearance_changed(self, _value: str) -> None:
        # Rebuild after the button's click handler has returned, because the
        # button that was clicked belongs to the widget tree being replaced.
        QTimer.singleShot(0, self._rebuild)

    def _rebuild(self) -> None:
        row = max(self.nav.currentRow(), 0)
        self._build_content()  # setCentralWidget() schedules the old tree for deletion
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
        if manager.is_rtl:  # the sidebar sits on the right, so the divider moves too
            sidebar.setStyleSheet(
                "QWidget#sidebar { border-right: none; "
                f"border-left: 1px solid {theme.BORDER}; }}"
            )
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 18, 12, 12)

        # Header: brand + tagline, then the language and theme buttons.
        titles = QVBoxLayout()
        titles.setSpacing(0)
        brand = QLabel(tr("app.name"))
        brand.setObjectName("brand")
        sub = QLabel(tr("app.tagline"))
        sub.setObjectName("brandSub")
        titles.addWidget(brand)
        titles.addWidget(sub)
        side_layout.addLayout(titles)

        tools = QHBoxLayout()
        tools.setContentsMargins(8, 0, 8, 8)
        tools.setSpacing(6)
        tools.addWidget(self._make_language_button())
        tools.addWidget(self._make_theme_button())
        tools.addStretch(1)
        side_layout.addLayout(tools)

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

    def _make_theme_button(self) -> QToolButton:
        to_light = theme.manager.is_dark
        button = QToolButton()
        button.setObjectName("themeBtn")
        button.setIcon(theme_icon("sun" if to_light else "moon", theme.TEXT))
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tr("theme.to_light" if to_light else "theme.to_dark"))
        button.clicked.connect(lambda _checked=False: theme.manager.toggle())
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
        page.refresh()  # type: ignore[attr-defined]