from __future__ import annotations
from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

DEFAULT_THEME = "dark"
FONT_FAMILIES = ["Segoe UI", "Tahoma", "Noto Sans Arabic", "Arial"]

# Palettes. Every key becomes a module-level constant (theme.BG, theme.CARD...).
PALETTES: dict[str, dict[str, object]] = {
    "dark": {  # GitHub-dark inspired
        "BG": "#0d1117",
        "SIDEBAR_BG": "#010409",
        "CARD": "#161b22",
        "CARD_ALT": "#11161d",
        "INPUT_BG": "#0d1117",
        "BORDER": "#30363d",
        "TEXT": "#e6edf3",
        "MUTED": "#8b949e",
        "ACCENT": "#2f81f7",
        "SUCCESS": "#3fb950",
        "WARNING": "#d29922",
        "ORANGE": "#f0ad4e",
        "DANGER": "#f85149",
        "HIGHLIGHT": "#1f6feb",
        "NAV_HOVER": "#161b22",
        "SELECT_NAV": "rgba(47,129,247,0.18)",
        "SELECT_ROW": "rgba(47,129,247,0.25)",
        "BTN_BG": "#21262d",
        "BTN_HOVER": "#30363d",
        "BTN_PRESSED": "#3b434c",
        "DISABLED_TEXT": "#6e7681",
        "DISABLED_BG": "#161b22",
        "SCROLL_HOVER": "#484f58",
        "PRIMARY": "#238636",
        "PRIMARY_BORDER": "#2ea043",
        "PRIMARY_HOVER": "#2ea043",
        "PRIMARY_DISABLED": "#1b2a20",
        "WARN_BG": "#9e6a03",
        "WARN_BORDER": "#bb8009",
        "WARN_HOVER": "#bb8009",
        "DANGER_BG": "#b62324",
        "DANGER_BORDER": "#da3633",
        "DANGER_HOVER": "#da3633",
        # Heatmap intensity levels: none, <=30m, <=90m, <=180m, >180m
        "HEAT_COLORS": ["#1c2128", "#0e4429", "#006d32", "#26a641", "#39d353"],
        # Donut chart slices (cycled when there are more subjects than colours)
        "SLICE_COLORS": [
            "#39d353", "#58a6ff", "#f0ad4e", "#e05780", "#a78bfa", "#2dd4bf",
            "#f97316", "#facc15", "#60a5fa", "#f472b6", "#4ade80", "#c084fc",
        ],
    },
    "light": {  # GitHub-light inspired
        "BG": "#f6f8fa",
        "SIDEBAR_BG": "#ffffff",
        "CARD": "#ffffff",
        "CARD_ALT": "#f6f8fa",
        "INPUT_BG": "#ffffff",
        "BORDER": "#d0d7de",
        "TEXT": "#1f2328",
        "MUTED": "#59636e",
        "ACCENT": "#0969da",
        "SUCCESS": "#1a7f37",
        "WARNING": "#9a6700",
        "ORANGE": "#bc4c00",
        "DANGER": "#cf222e",
        "HIGHLIGHT": "#0969da",
        "NAV_HOVER": "#eef1f4",
        "SELECT_NAV": "rgba(9,105,218,0.12)",
        "SELECT_ROW": "rgba(9,105,218,0.16)",
        "BTN_BG": "#f3f4f6",
        "BTN_HOVER": "#e6e9ed",
        "BTN_PRESSED": "#d8dce1",
        "DISABLED_TEXT": "#8c959f",
        "DISABLED_BG": "#f6f8fa",
        "SCROLL_HOVER": "#afb8c1",
        "PRIMARY": "#1f883d",
        "PRIMARY_BORDER": "#1a7f37",
        "PRIMARY_HOVER": "#1a7f37",
        "PRIMARY_DISABLED": "#dbeee0",
        "WARN_BG": "#bf8700",
        "WARN_BORDER": "#9a6700",
        "WARN_HOVER": "#9a6700",
        "DANGER_BG": "#cf222e",
        "DANGER_BORDER": "#a40e26",
        "DANGER_HOVER": "#a40e26",
        "HEAT_COLORS": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "SLICE_COLORS": [
            "#2da44e", "#0969da", "#bc4c00", "#bf3989", "#8250df", "#1b7c83",
            "#e16f24", "#bf8700", "#218bff", "#d1429a", "#1a7f37", "#a475f9",
        ],
    },
}

# Declarations for IDEs / type checkers; the values are set by _activate().
BG: str
SIDEBAR_BG: str
CARD: str
CARD_ALT: str
INPUT_BG: str
BORDER: str
TEXT: str
MUTED: str
ACCENT: str
SUCCESS: str
WARNING: str
ORANGE: str
DANGER: str
HIGHLIGHT: str
NAV_HOVER: str
SELECT_NAV: str
SELECT_ROW: str
BTN_BG: str
BTN_HOVER: str
BTN_PRESSED: str
DISABLED_TEXT: str
DISABLED_BG: str
SCROLL_HOVER: str
PRIMARY: str
PRIMARY_BORDER: str
PRIMARY_HOVER: str
PRIMARY_DISABLED: str
WARN_BG: str
WARN_BORDER: str
WARN_HOVER: str
DANGER_BG: str
DANGER_BORDER: str
DANGER_HOVER: str
HEAT_COLORS: list[str]
SLICE_COLORS: list[str]


def _activate(name: str) -> None:
    globals().update(PALETTES[name])


def build_stylesheet() -> str:
    return f"""
* {{
    font-family: "Segoe UI", "Tahoma", "Noto Sans Arabic", "Arial";
}}
QMainWindow, QWidget#root {{ background: {BG}; }}
QToolTip {{
    background: {CARD}; color: {TEXT};
    border: 1px solid {BORDER}; padding: 6px 8px;
}}

/* ---- Sidebar ---- */
QWidget#sidebar {{ background: {SIDEBAR_BG}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ font-size: 13pt; font-weight: 700; color: {TEXT}; padding: 6px 8px 0 8px; }}
QLabel#brandSub {{ color: {MUTED}; font-size: 8pt; padding: 0 8px 10px 8px; }}
QListWidget#nav {{ background: transparent; border: none; outline: none; }}
QListWidget#nav::item {{
    padding: 11px 14px; margin: 2px 0; border-radius: 8px; color: {MUTED};
}}
QListWidget#nav::item:hover:!selected {{ background: {NAV_HOVER}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: {SELECT_NAV}; color: {TEXT}; }}

/* ---- Language / theme buttons ---- */
QToolButton#langBtn, QToolButton#themeBtn {{
    background: transparent; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 4px 8px; color: {MUTED}; font-weight: 600;
}}
QToolButton#langBtn:hover, QToolButton#themeBtn:hover {{
    background: {NAV_HOVER}; color: {TEXT};
}}

/* ---- Typography ---- */
QLabel {{ background: transparent; }}
QLabel#pageTitle {{ font-size: 20pt; font-weight: 700; }}
QLabel#cardTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#statCaption {{ color: {MUTED}; font-size: 9pt; }}
QLabel#statValue {{ font-size: 16pt; font-weight: 700; }}
QLabel#statValueSmall {{ font-size: 11pt; font-weight: 700; }}

/* ---- Cards ---- */
QFrame#card {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
}}
QFrame#card QLabel {{ border: none; }}

/* ---- Buttons ---- */
QPushButton {{
    background: {BTN_BG}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 7px 14px; color: {TEXT};
}}
QPushButton:hover {{ background: {BTN_HOVER}; }}
QPushButton:pressed {{ background: {BTN_PRESSED}; }}
QPushButton:disabled {{ color: {DISABLED_TEXT}; background: {DISABLED_BG}; }}
QPushButton#primary {{
    background: {PRIMARY}; border-color: {PRIMARY_BORDER}; color: white; font-weight: 600;
    padding: 9px 18px;
}}
QPushButton#primary:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton#primary:disabled {{
    background: {PRIMARY_DISABLED}; border-color: {PRIMARY_DISABLED}; color: {DISABLED_TEXT};
}}
QPushButton#warning {{ background: {WARN_BG}; border-color: {WARN_BORDER}; color: white; }}
QPushButton#warning:hover {{ background: {WARN_HOVER}; }}
QPushButton#danger {{ background: {DANGER_BG}; border-color: {DANGER_BORDER}; color: white; }}
QPushButton#danger:hover {{ background: {DANGER_HOVER}; }}
QPushButton#chip {{ padding: 5px 12px; border-radius: 14px; }}

/* ---- Inputs (spin boxes / date edits keep the native Fusion look) ---- */
QLineEdit {{
    background: {INPUT_BG}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 7px 10px; selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

/* ---- Tables ---- */
QTableWidget {{
    background: transparent; alternate-background-color: {CARD_ALT};
    border: none; outline: none; gridline-color: transparent;
    selection-background-color: {SELECT_ROW}; selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 6px 8px; border: none; }}
QHeaderView::section {{
    background: {CARD}; color: {MUTED}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 8px; font-weight: 600;
}}
QTableCornerButton::section {{ background: {CARD}; border: none; }}

/* ---- Scroll areas / bars ---- */
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 5px; min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{ background: {SCROLL_HOVER}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 5px; min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: {SCROLL_HOVER}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
"""


def _build_palette() -> QPalette:
    palette = QPalette()
    role = QPalette.ColorRole
    palette.setColor(role.Window, QColor(BG))
    palette.setColor(role.WindowText, QColor(TEXT))
    palette.setColor(role.Base, QColor(INPUT_BG))
    palette.setColor(role.AlternateBase, QColor(CARD))
    palette.setColor(role.Text, QColor(TEXT))
    palette.setColor(role.Button, QColor(BTN_BG))
    palette.setColor(role.ButtonText, QColor(TEXT))
    palette.setColor(role.ToolTipBase, QColor(CARD))
    palette.setColor(role.ToolTipText, QColor(TEXT))
    palette.setColor(role.Highlight, QColor(HIGHLIGHT))
    palette.setColor(role.HighlightedText, QColor("white"))
    palette.setColor(role.PlaceholderText, QColor(MUTED))
    palette.setColor(role.Link, QColor(ACCENT))
    for disabled_role in (role.Text, role.WindowText, role.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, disabled_role, QColor(DISABLED_TEXT))
    return palette


class ThemeManager(QObject):

    themeChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("StudyPlanner", "StudyPlanner")
        saved = str(self._settings.value("theme", DEFAULT_THEME))
        self._name = saved if saved in PALETTES else DEFAULT_THEME
        _activate(self._name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_dark(self) -> bool:
        return self._name == "dark"

    @property
    def other_theme(self) -> str:
        return "light" if self.is_dark else "dark"

    def apply(self, app: QApplication | None = None) -> None:
        app = app or QApplication.instance()  # type: ignore[assignment]
        if not isinstance(app, QApplication):
            return
        hints = app.styleHints()
        if hasattr(hints, "setColorScheme"):  # Qt >= 6.8: native title bar follows the theme
            hints.setColorScheme(
                Qt.ColorScheme.Dark if self.is_dark else Qt.ColorScheme.Light
            )
        app.setStyle("Fusion")
        app.setPalette(_build_palette())
        font = QFont()
        font.setFamilies(FONT_FAMILIES)
        font.setPointSize(10)
        app.setFont(font)
        app.setStyleSheet(build_stylesheet())

    def set_theme(self, name: str) -> None:
        if name == self._name or name not in PALETTES:
            return
        self._name = name
        self._settings.setValue("theme", name)
        _activate(name)
        self.apply()
        self.themeChanged.emit(name)

    def toggle(self) -> None:
        self.set_theme(self.other_theme)


manager = ThemeManager()


def apply_theme(app: QApplication) -> None:
    manager.apply(app)