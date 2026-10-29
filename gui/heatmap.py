"""GitHub-style yearly activity heatmap, painted with QPainter."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QScrollArea, QToolTip, QWidget

from gui import theme
from utils.helpers import minutes_to_hm_text

CELL = 12
GAP = 3
STEP = CELL + GAP
LEFT = 38          # room for the weekday labels
TOP = 22           # room for the month labels
FOOTER = 26        # room for the legend
RIGHT_PAD = 8
MIN_LABEL_GAP = 30  # minimum horizontal distance between two month labels
MIN_WIDTH = 220


def level_color(minutes: int) -> QColor:
    """Map a day's total minutes to one of the five heatmap colours."""
    if minutes <= 0:
        idx = 0
    elif minutes <= 30:
        idx = 1
    elif minutes <= 90:
        idx = 2
    elif minutes <= 180:
        idx = 3
    else:
        idx = 4
    return QColor(theme.HEAT_COLORS[idx])


class HeatmapWidget(QWidget):
    """Draws Jan 1 -> today as a grid of weeks (columns) x weekdays (rows)."""

    dayClicked = Signal(str)  # ISO date, e.g. "2026-10-25"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self._totals: dict[str, int] = {}
        self._selected: date | None = None
        self._hover: date | None = None
        self.set_data({}, date.today())

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def set_data(self, totals: dict[str, int], today: date | None = None) -> None:
        self._totals = totals
        self._today = today or date.today()
        self._jan1 = self._today.replace(month=1, day=1)
        # The grid starts on the Monday of the week that contains Jan 1.
        self._grid_start = self._jan1 - timedelta(days=self._jan1.weekday())
        self._weeks = (self._today - self._grid_start).days // 7 + 1
        width = max(MIN_WIDTH, LEFT + self._weeks * STEP + RIGHT_PAD)
        self.setFixedSize(width, TOP + 7 * STEP + FOOTER)
        self.update()

    def set_selected(self, day: date | None) -> None:
        self._selected = day
        self.update()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def _cell_rect(self, day: date) -> QRectF:
        offset = (day - self._grid_start).days
        col, row = divmod(offset, 7)
        return QRectF(LEFT + col * STEP, TOP + row * STEP, CELL, CELL)

    def _day_at(self, pos: QPointF) -> date | None:
        """The day under the mouse, or None when over a gap/outside the grid."""
        x, y = pos.x() - LEFT, pos.y() - TOP
        if x < 0 or y < 0:
            return None
        col, rx = divmod(int(x), STEP)
        row, ry = divmod(int(y), STEP)
        if rx >= CELL or ry >= CELL or row > 6:
            return None
        day = self._grid_start + timedelta(days=col * 7 + row)
        if day < self._jan1 or day > self._today:
            return None
        return day

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        small = QFont(self.font())
        small.setPointSizeF(8)
        painter.setFont(small)
        painter.setPen(QColor(theme.MUTED))

        # Weekday labels
        for row, label in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
            painter.drawText(
                QRectF(0, TOP + row * STEP, LEFT - 8, CELL),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        # Month labels: one per month, never closer than MIN_LABEL_GAP pixels.
        # The first column uses Jan 1 (not the padding Monday from December).
        last_month: int | None = None
        last_x = -MIN_LABEL_GAP
        for col in range(self._weeks):
            monday = self._grid_start + timedelta(days=7 * col)
            label_day = max(monday, self._jan1)
            x = LEFT + col * STEP
            if label_day.month != last_month and x - last_x >= MIN_LABEL_GAP:
                last_month, last_x = label_day.month, x
                painter.drawText(
                    QRectF(x, 0, 40, TOP - 6),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    label_day.strftime("%b"),
                )

        # Day cells
        painter.setPen(Qt.PenStyle.NoPen)
        day = self._jan1
        while day <= self._today:
            painter.setBrush(level_color(self._totals.get(day.isoformat(), 0)))
            painter.drawRoundedRect(self._cell_rect(day), 3, 3)
            day += timedelta(days=1)

        # Outlines: hover, selected, today (today drawn last so it stays visible)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for target, color, width in (
            (self._hover, theme.MUTED, 1.5),
            (self._selected, theme.TEXT, 2.0),
            (self._today, theme.ORANGE, 2.0),
        ):
            if target is not None and self._jan1 <= target <= self._today:
                painter.setPen(QPen(QColor(color), width))
                painter.drawRoundedRect(self._cell_rect(target).adjusted(-1, -1, 1, 1), 4, 4)

        self._paint_legend(painter)

    def _paint_legend(self, painter: QPainter) -> None:
        metrics = painter.fontMetrics()
        less, more = "Less", "More"
        square, spacing = CELL - 2, 4
        total = (
            metrics.horizontalAdvance(less) + 6
            + len(theme.HEAT_COLORS) * (square + spacing)
            + metrics.horizontalAdvance(more)
        )
        x = max(LEFT, self.width() - RIGHT_PAD - total)
        y = TOP + 7 * STEP + 6

        painter.setPen(QColor(theme.MUTED))
        painter.drawText(
            QRectF(x, y, metrics.horizontalAdvance(less), square),
            Qt.AlignmentFlag.AlignVCenter, less,
        )
        x += metrics.horizontalAdvance(less) + 6
        painter.setPen(Qt.PenStyle.NoPen)
        for color in theme.HEAT_COLORS:
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(x, y, square, square), 3, 3)
            x += square + spacing
        painter.setPen(QColor(theme.MUTED))
        painter.drawText(
            QRectF(x, y, metrics.horizontalAdvance(more) + 2, square),
            Qt.AlignmentFlag.AlignVCenter, more,
        )

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        day = self._day_at(event.position())
        if day != self._hover:
            self._hover = day
            self.update()
        if day is None:
            self.unsetCursor()
            QToolTip.hideText()
            return
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        minutes = self._totals.get(day.isoformat(), 0)
        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"{day.strftime('%a, %d %b %Y')}\nStudy time: {minutes_to_hm_text(minutes)}",
            self,
        )

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self._hover = None
        self.unsetCursor()
        QToolTip.hideText()
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        day = self._day_at(event.position())
        if day is not None:
            self.set_selected(day)
            self.dayClicked.emit(day.isoformat())


class HeatmapView(QScrollArea):
    """Horizontal scroll container for the heatmap.

    Always opens scrolled to the right edge so the most recent weeks (today)
    are visible, and lets the mouse wheel scroll sideways.
    """

    def __init__(self, heatmap: HeatmapWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.heatmap = heatmap
        self.setWidget(heatmap)
        self.setWidgetResizable(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.viewport().setAutoFillBackground(False)
        heatmap.setAutoFillBackground(False)
        self.setFixedHeight(
            heatmap.height() + self.horizontalScrollBar().sizeHint().height() + 2
        )

    def scroll_to_end(self) -> None:
        bar = self.horizontalScrollBar()
        bar.setValue(bar.maximum())

    def scroll_to_end_later(self) -> None:
        QTimer.singleShot(0, self.scroll_to_end)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        self.scroll_to_end_later()

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().showEvent(event)
        self.scroll_to_end_later()

    def wheelEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        bar = self.horizontalScrollBar()
        delta = event.angleDelta().y() or event.angleDelta().x()
        bar.setValue(bar.value() - delta)
        event.accept()
