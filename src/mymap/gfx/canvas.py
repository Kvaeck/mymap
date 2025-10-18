# src/mymap/gfx/canvas.py
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter, QKeyEvent, QMouseEvent
from PySide6.QtCore import Qt, Signal, QPointF

class CanvasView(QGraphicsView):
    """Thin QGraphicsView with Ctrl+wheel zoom and rubberband selection.

    Emits:
      - spawn_branch_from_center(scene_pos: QPointF)
      - spawn_branch_with_node(scene_pos: QPointF)
      - spawn_sister_branch()
    """
    spawn_branch_from_center = Signal(object)   # scene pos
    spawn_branch_with_node = Signal(object)     # scene pos (reserved)
    spawn_sister_branch = Signal()

    def __init__(self, scene):
        super().__init__(scene)
        # prefer high-quality rendering
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.RubberBandDrag)
        # use bounding rect updates so changed items are repainted fully but efficiently
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self._zoom = 0

        # input state
        self._shift_pressed = False

    def wheelEvent(self, event):
        # zoom when Ctrl is pressed
        if event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.0015 ** angle
            self.scale(factor, factor)
            self._zoom += angle
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        # Press Enter -> spawn sister branch
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.spawn_sister_branch.emit()
            event.accept()
            return

        # Track Shift state for click-to-spawn behavior
        if event.key() == Qt.Key_Shift:
            self._shift_pressed = True

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Shift:
            self._shift_pressed = False
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # If shift is pressed and user clicks left, spawn a branch from the pusat (center)
        if event.button() == Qt.LeftButton and self._shift_pressed:
            scene_pos = self.mapToScene(event.pos())
            self.spawn_branch_from_center.emit(scene_pos)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        # (future) could implement drag-handle logic: if mouse was dragging from a handle,
        # then emit spawn_branch_with_node with the release position.
        super().mouseReleaseEvent(event)
