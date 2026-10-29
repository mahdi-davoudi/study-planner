"""Dark theme: colour constants, application palette and the global stylesheet."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# --- Colours (GitHub-dark inspired) -----------------------------------------
BG = "#0d1117"
SIDEBAR_BG = "#010409"
CARD = "#161b22"
CARD_ALT = "#11161d"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#2f81f7"
SUCCESS = "#3fb950"
WARNING = "#d29922"
ORANGE = "#f0ad4e"
DANGER = "#f85149"

# Heatmap intensity levels: none, <=30m, <=90m, <=180m, >180m
HEAT_COLORS = ["#1c2128", "#0e4429", "#006d32", "#26a641", "#39d353"]

# Donut chart slices (cycled when there are more subjects than colours)
SLICE_COLORS = [
    "#39d353", "#58a6ff", "#f0ad4e", "#e05780", "#a78bfa", "#2dd4bf",
    "#f97316", "#facc15", "#60a5fa", "#f472b6", "#4ade80", "#c084fc",
]

FONT_FAMILIES = ["Segoe UI", "Tahoma", "Noto Sans Arabic", "Arial"]

STYLESHEET = f"""
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
QListWidget#nav::item:hover:!selected {{ background: {CARD}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: rgba(47,129,247,0.18); color: {TEXT}; }}

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
    background: #21262d; border: 1px solid {BORDER};
    border-radius: 8px; padding: 7px 14px; color: {TEXT};
}}
QPushButton:hover {{ background: {BORDER}; }}
QPushButton:pressed {{ background: #3b434c; }}
QPushButton:disabled {{ color: #6e7681; background: #161b22; }}
QPushButton#primary {{
    background: #238636; border-color: #2ea043; color: white; font-weight: 600;
    padding: 9px 18px;
}}
QPushButton#primary:hover {{ background: #2ea043; }}
QPushButton#primary:disabled {{ background: #1b2a20; border-color: #1b2a20; color: #6e7681; }}
QPushButton#warning {{ background: #9e6a03; border-color: #bb8009; color: white; }}
QPushButton#warning:hover {{ background: #bb8009; }}
QPushButton#danger {{ background: #b62324; border-color: #da3633; color: white; }}
QPushButton#danger:hover {{ background: #da3633; }}
QPushButton#chip {{ padding: 5px 12px; border-radius: 14px; }}

/* ---- Inputs (spin boxes / date edits keep the native Fusion look) ---- */
QLineEdit {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 7px 10px; selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

/* ---- Tables ---- */
QTableWidget {{
    background: transparent; alternate-background-color: {CARD_ALT};
    border: none; outline: none; gridline-color: transparent;
    selection-background-color: rgba(47,129,247,0.25); selection-color: {TEXT};
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
QScrollBar::handle:vertical:hover {{ background: #484f58; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {BORDER}; border-radius: 5px; min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{ background: #484f58; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
"""


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CARD))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
    palette.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText,
                 QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#6e7681"))
    return palette


def apply_theme(app: QApplication) -> None:
    """Install the Fusion style, dark palette, default font and stylesheet."""
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    font = QFont()
    font.setFamilies(FONT_FAMILIES)
    font.setPointSize(10)
    app.setFont(font)
    app.setStyleSheet(STYLESHEET)
