from __future__ import annotations
import unicodedata
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui import theme


def page_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("pageTitle")
    return label


def muted_label(text: str = "", wrap: bool = True) -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    label.setWordWrap(wrap)
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label


def is_rtl_text(text: str) -> bool:
    """True when the first letter of the text is from a right-to-left script."""
    for char in text:
        if char.isalpha():
            return unicodedata.bidirectional(char) in ("R", "AL")
    return False


def align_visual_right(label: QLabel) -> None:
    """Put the label's text at the visual right edge, for Persian and Latin alike.

    Qt flips Left/Right for right-to-left paragraphs, so the flag must depend
    on the text direction to get a consistent result.
    """
    side = (
        Qt.AlignmentFlag.AlignLeft
        if is_rtl_text(label.text())
        else Qt.AlignmentFlag.AlignRight
    )
    label.setAlignment(side | Qt.AlignmentFlag.AlignVCenter)


def swatch_icon(color: str | QColor, size: int = 12) -> QIcon:
    """A small rounded colour square used as a legend marker in tables."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(0, 0, size, size, 3, 3)
    painter.end()
    return QIcon(pixmap)

def globe_icon(color: str, size: int = 18) -> QIcon:
    """Simple globe icon (circle + meridian + equator) drawn with QPainter."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color), 1.4))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(1.5, 1.5, size - 3, size - 3))
    p.drawEllipse(QRectF(size * 0.33, 1.5, size * 0.34, size - 3))
    p.drawLine(QPointF(1.5, size / 2), QPointF(size - 1.5, size / 2))
    p.end()
    return QIcon(pixmap)

class Card(QFrame):
    """Rounded panel with an optional title and a vertical body layout."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 16)
        self._layout.setSpacing(10)
        self._title = QLabel(title)
        self._title.setObjectName("cardTitle")
        self._title.setVisible(bool(title))
        self._layout.addWidget(self._title)

    def set_title(self, title: str) -> None:
        self._title.setText(title)
        self._title.setVisible(bool(title))

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self._layout.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0) -> None:  # type: ignore[no-untyped-def]
        self._layout.addLayout(layout, stretch)


class StatCard(QFrame):
    """A caption with a big value underneath (e.g. "This week" / "3h 20m")."""

    def __init__(
        self,
        caption: str,
        color: str = theme.TEXT,
        small: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self._caption = QLabel(caption)
        self._caption.setObjectName("statCaption")
        self._value = QLabel("-")
        self._value.setObjectName("statValueSmall" if small else "statValue")
        self._value.setTextFormat(Qt.TextFormat.PlainText)
        self._value.setWordWrap(small)
        self._value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._value.setStyleSheet(f"color: {color};")

        layout.addWidget(self._caption)
        layout.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class NoWheelSpinBox(QSpinBox):
    """Spin box that ignores the mouse wheel unless it has keyboard focus.

    Prevents values from changing by accident while scrolling a list of them.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


def scrollable(widget: QWidget) -> QScrollArea:
    """Wrap a widget in a transparent, borderless vertical scroll area."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(widget)
    area.viewport().setAutoFillBackground(False)
    widget.setAutoFillBackground(False)
    return area
