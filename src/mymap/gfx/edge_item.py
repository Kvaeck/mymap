# src/mymap/gfx/edge_item.py
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QPen
from PySide6.QtCore import QPointF, Qt


class EdgeItem(QGraphicsPathItem):
    """A bezier-curved edge between two NodeItem instances."""

    def __init__(self, source, dest):
        super().__init__()
        self.source = source
        self.dest = dest
        # make edge selectable so user can click it
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        pen = QPen(Qt.black)
        pen.setWidth(2)
        self._normal_pen = pen
        sel_pen = QPen(Qt.blue)
        sel_pen.setWidth(2)
        self._sel_pen = sel_pen
        self.setPen(self._normal_pen)
        self.setZValue(-1)
        # register with nodes
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.update_path()

    def update_path(self):
        s = self.source.sceneBoundingRect().center()
        d = self.dest.sceneBoundingRect().center()
        path = QPainterPath()
        path.moveTo(s)
        dx = (d.x() - s.x())
        cp1 = QPointF(s.x() + dx * 0.35, s.y())
        cp2 = QPointF(d.x() - dx * 0.35, d.y())
        path.cubicTo(cp1, cp2, d)
        self.setPath(path)

    def itemChange(self, change, value):
        # use the numeric constant which is available via QGraphicsItem
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(self._sel_pen)
            else:
                self.setPen(self._normal_pen)
        return super().itemChange(change, value)

    def remove(self):
        try:
            try:
                self.source.remove_edge(self)
            except Exception:
                pass
            try:
                self.dest.remove_edge(self)
            except Exception:
                pass
            sc = self.scene()
            if sc:
                sc.removeItem(self)
        except Exception:
            pass
