# src/mymap/gfx/canvas.py
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt


class CanvasView(QGraphicsView):
    """Thin QGraphicsView with Ctrl+wheel zoom and rubberband selection."""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._zoom = 0

    def wheelEvent(self, event):
        # zoom when Ctrl is pressed
        if event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.0015 ** angle
            self.scale(factor, factor)
            self._zoom += angle
        else:
            super().wheelEvent(event)
