"""Donut chart painted with QPainter (no matplotlib, correct RTL text)."""

from __future__ import annotations

import html
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from gui import theme
from utils.helpers import minutes_to_hm_text

Item = tuple[str, int, QColor]  # (subject name, minutes, colour)


class DonutChart(QWidget):
    """Shows each subject's share of the total study time as a ring."""

    HOLE_RATIO = 0.62

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(240, 240)
        self._items: list[Item] = []
        self._total = 0

    def set_items(self, items: list[Item]) -> None:
        self._items = [item for item in items if item[1] > 0]
        self._total = sum(item[1] for item in self._items)
        self.update()

    # ------------------------------------------------------------------
    def _ring(self) -> tuple[QPointF, float, float]:
        margin = 14
        side = max(min(self.width(), self.height()) - 2 * margin, 20)
        outer = side / 2
        center = QPointF(self.width() / 2, self.height() / 2)
        return center, outer, outer * self.HOLE_RATIO

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._total <= 0:
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "No study data for\nthe selected period",
            )
            return

        center, outer_r, inner_r = self._ring()
        outer = QRectF(center.x() - outer_r, center.y() - outer_r, 2 * outer_r, 2 * outer_r)
        inner = QRectF(center.x() - inner_r, center.y() - inner_r, 2 * inner_r, 2 * inner_r)

        painter.setPen(QPen(QColor(theme.CARD), 2))
        angle = 90.0  # start at 12 o'clock and go clockwise
        for _name, minutes, color in self._items:
            fraction = minutes / self._total
            path = QPainterPath()
            if fraction >= 0.9999:  # single slice: full ring
                path.setFillRule(Qt.FillRule.OddEvenFill)
                path.addEllipse(outer)
                path.addEllipse(inner)
            else:
                span = -360.0 * fraction
                path.arcMoveTo(outer, angle)
                path.arcTo(outer, angle, span)
                path.arcTo(inner, angle + span, -span)
                path.closeSubpath()
                angle += span
            painter.setBrush(color)
            painter.drawPath(path)

        # Centre label
        painter.setPen(QColor(theme.TEXT))
        big = QFont(self.font())
        big.setPointSizeF(18)
        big.setBold(True)
        painter.setFont(big)
        painter.drawText(
            QRectF(inner.left(), inner.center().y() - 26, inner.width(), 30),
            Qt.AlignmentFlag.AlignCenter, minutes_to_hm_text(self._total),
        )
        small = QFont(self.font())
        small.setPointSizeF(9)
        painter.setFont(small)
        painter.setPen(QColor(theme.MUTED))
        painter.drawText(
            QRectF(inner.left(), inner.center().y() + 4, inner.width(), 20),
            Qt.AlignmentFlag.AlignCenter, "Total",
        )

    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        item = self._item_at(event.position())
        if item is None:
            QToolTip.hideText()
            return
        name, minutes, _color = item
        pct = minutes / self._total * 100
        QToolTip.showText(
            event.globalPosition().toPoint(),
            f"<b>{html.escape(name)}</b><br>{minutes_to_hm_text(minutes)} · {pct:.1f}%",
            self,
        )

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        QToolTip.hideText()

    def _item_at(self, pos: QPointF) -> Item | None:
        if self._total <= 0:
            return None
        center, outer_r, inner_r = self._ring()
        dx, dy = pos.x() - center.x(), center.y() - pos.y()
        if not inner_r <= math.hypot(dx, dy) <= outer_r:
            return None
        theta = (90.0 - math.degrees(math.atan2(dy, dx))) % 360.0  # clockwise from top
        acc = 0.0
        for item in self._items:
            acc += 360.0 * item[1] / self._total
            if theta < acc:
                return item
        return self._items[-1]
