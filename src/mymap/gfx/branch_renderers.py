# src/mymap/gfx/branch_renderers.py
from PySide6.QtGui import QPainterPath, QPainter, QPen
from PySide6.QtCore import QPointF

class CurvedBranchRenderer:
    """
    Draws a smooth curved connection between two points using a cubic bezier approach.
    Example usage in a QGraphicsItem's paint():
        renderer = CurvedBranchRenderer()
        renderer.draw(painter, start_qpointf, end_qpointf, pen)
    """

    def __init__(self, curvature: float = 0.4):
        """
        curvature: a factor 0..1 controlling the control points offset
        """
        self.curvature = max(0.0, min(1.0, curvature))

    def _control_points(self, p1: QPointF, p2: QPointF):
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        # Use horizontal bias for mindmap branches. Control distance proportional to dx.
        cp1 = QPointF(p1.x() + dx * self.curvature, p1.y())
        cp2 = QPointF(p2.x() - dx * self.curvature, p2.y())
        return cp1, cp2

    def draw(self, painter: QPainter, p1: QPointF, p2: QPointF, pen: QPen):
        painter.save()
        painter.setPen(pen)
        path = QPainterPath()
        path.moveTo(p1)
        cp1, cp2 = self._control_points(p1, p2)
        path.cubicTo(cp1, cp2, p2)
        painter.drawPath(path)
        painter.restore()
