# src/mymap/gfx/node_item.py
import uuid
from typing import Optional
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsObject, QGraphicsItem, QGraphicsEllipseItem
from PySide6.QtGui import QFont, QPainter, QBrush, QColor, QPen
from PySide6.QtCore import QRectF, QPointF, Qt, Signal

class EditableTextItem(QGraphicsTextItem):
    """A QGraphicsTextItem that records old/new text on focus changes."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self._old_text = self.toPlainText()

    def focusInEvent(self, event):
        self._old_text = self.toPlainText()
        try:
            self.update()
            parent = self.parentItem()
            if parent:
                parent.update()
        except Exception:
            pass
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        new_text = self.toPlainText()
        old = self._old_text
        try:
            doc = self.document()
            doc.adjustSize()
            self.update()
            parent = self.parentItem()
            if parent:
                parent.update()
        except Exception:
            pass

        if new_text != old and self.parentItem() is not None:
            parent = self.parentItem()
            if hasattr(parent, "commit_text_change"):
                parent.commit_text_change(old, new_text)
        super().focusOutEvent(event)


class HandleItem(QGraphicsEllipseItem):
    """
    Small circular handle attached to NodeItem. Emits drag-release events to the parent NodeItem.
    """

    def __init__(self, parent_node: QGraphicsItem, radius: float = 8.0, handle_type: str = "branch"):
        super().__init__(-radius, -radius, radius * 2, radius * 2, parent_node)
        self.setAcceptHoverEvents(True)
        # Make sure handle explicitly accepts the left mouse button
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, False)
        self.radius = radius
        self.handle_type = handle_type
        # visual
        self._normal_brush = QBrush(QColor(255, 255, 255, 230))
        self._normal_pen = QPen(QColor(80, 80, 80, 160))
        self._hover_brush = QBrush(QColor(255, 255, 255))
        self._hover = False
        self.setZValue(10)

        # internal drag tracking
        self._dragging = False

    def paint(self, painter, option, widget=None):
        painter.setPen(self._normal_pen)
        painter.setBrush(self._hover_brush if self._hover else self._normal_brush)
        painter.drawEllipse(self.rect())

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            # debug print
            print(f"[Handle] mousePress: type={self.handle_type}, parent={self.parentItem().__class__.__name__}")
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # accept the move so release will be delivered reliably
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            # debug print
            try:
                parent_name = self.parentItem().__class__.__name__ if self.parentItem() else "None"
            except Exception:
                parent_name = "None"
            print(f"[Handle] mouseRelease: type={self.handle_type}, parent={parent_name}")
            # compute scene position robustly
            # event.pos() is local to the handle; mapToScene will produce correct scene coords
            scene_pos = self.mapToScene(event.pos())
            parent = self.parentItem()
            if parent is not None and hasattr(parent, "_handle_released"):
                parent._handle_released(self.handle_type, scene_pos)
            event.accept()
            return
        super().mouseReleaseEvent(event)



class NodeItem(QGraphicsObject):
    """A movable, selectable node that contains an EditableTextItem and tracks connected edges."""

    moved = Signal(object, object)
    textChanged = Signal(object, object)
    # New signals: a node emitted when one of its handles releases a drag
    spawn_branch = Signal(object)            # scene_pos
    spawn_branch_with_node = Signal(object)  # scene_pos

    def __init__(self, text="New Node", node_id=None, label_mode: bool = False):
        """
        label_mode: if True, node renders only text (no rounded rect), used for 'branch-only' labels.
        """
        super().__init__()
        self.id = node_id or str(uuid.uuid4())
        self.text_item = EditableTextItem(text, self)
        f = QFont()
        f.setPointSize(10 if not label_mode else 12)
        self.text_item.setFont(f)
        # anchor text inside the node at local (0,0)
        self.text_item.setPos(0, 0)

        self.padding = 8 if not label_mode else 4
        self.bg_color = QColor(200, 250, 100) if not label_mode else QColor(0, 0, 0, 0)
        self.label_mode = label_mode

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        try:
            self.setCacheMode(QGraphicsItem.NoCache)
        except Exception:
            pass

        self._drag_start_pos = QPointF()
        self.edges = []

        # ---- create two handles on the right side ----
        # handle 1: branch-only (label)
        self._handle_branch = HandleItem(self, radius=7.0, handle_type="branch")
        # handle 2: branch with node
        self._handle_branch_node = HandleItem(self, radius=7.0, handle_type="branch_node")

        # initial placement of handles (relative to bounding rect)
        self._update_handles_pos()

    def boundingRect(self) -> QRectF:
        rect = self.text_item.boundingRect()
        return QRectF(
            rect.left() - self.padding,
            rect.top() - self.padding,
            rect.width() + 2 * self.padding,
            rect.height() + 2 * self.padding,
        )

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()
        # draw background rectangle only when not in label_mode
        if not self.label_mode:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.bg_color))
            painter.drawRoundedRect(rect, 8, 8)
        # update handle positions after painting (ensures correct geometry)
        self._update_handles_pos()

    def _update_handles_pos(self):
        """Position handles at the right-middle edge of the node, stacked vertically."""
        try:
            rect = self.boundingRect()
            # place handles near the right edge - one slightly above center, one slightly below
            right_x = rect.width() / 2 + rect.left()
            center_y = rect.height() / 2 + rect.top()
            spacing = 12
            # map local coordinates to handle parent (handles are children so local coords are fine)
            self._handle_branch.setPos(right_x + 6, center_y - spacing)
            self._handle_branch_node.setPos(right_x + 6, center_y + spacing)
        except Exception:
            pass

    def mousePressEvent(self, event):
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        end_pos = self.pos()
        if end_pos != self._drag_start_pos:
            self.moved.emit(self._drag_start_pos, end_pos)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for e in list(self.edges):
                try:
                    e.update_path()
                except Exception:
                    pass
            # move handles (position handled in paint/update, but also force update)
            self._update_handles_pos()
        return super().itemChange(change, value)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def commit_text_change(self, old_text, new_text):
        self.textChanged.emit(old_text, new_text)

    def set_text(self, text):
        self.text_item.setPlainText(text)
        try:
            self.text_item.document().adjustSize()
            self.update()
        except Exception:
            pass

    # ---- handle callback from child HandleItem ----
    def _handle_released(self, handle_type: str, scene_pos: QPointF):
        """
        Called by HandleItem when user drags/release from a handle.
        Emits higher-level signals so MainWindow can react.
        handle_type: "branch" or "branch_node"
        """
        if handle_type == "branch":
            self.spawn_branch.emit(scene_pos)
        elif handle_type == "branch_node":
            self.spawn_branch_with_node.emit(scene_pos)
        else:
            # unknown - ignore
            pass
