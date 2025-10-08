# src/mymap/gfx/node_item.py
import uuid
from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsObject, QGraphicsItem
from PySide6.QtGui import QFont, QPainter, QBrush, QColor
from PySide6.QtCore import QRectF, QPointF, Qt, Signal


class EditableTextItem(QGraphicsTextItem):
    """A QGraphicsTextItem that records old/new text on focus changes."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self._old_text = self.toPlainText()

    def focusInEvent(self, event):
        self._old_text = self.toPlainText()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        new_text = self.toPlainText()
        old = self._old_text
        if new_text != old and self.parentItem() is not None:
            parent = self.parentItem()
            if hasattr(parent, "commit_text_change"):
                parent.commit_text_change(old, new_text)
        super().focusOutEvent(event)


class NodeItem(QGraphicsObject):
    """A movable, selectable node that contains an EditableTextItem and tracks connected edges."""

    moved = Signal(object, object)
    textChanged = Signal(object, object)

    def __init__(self, text="New Node", node_id=None):
        super().__init__()
        self.id = node_id or str(uuid.uuid4())
        self.text_item = EditableTextItem(text, self)
        f = QFont()
        f.setPointSize(10)
        self.text_item.setFont(f)
        # anchor text inside the node at local (0,0)
        self.text_item.setPos(0, 0)

        self.padding = 8
        self.bg_color = QColor(255, 255, 200)

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self._drag_start_pos = QPointF()
        self.edges = []

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
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.bg_color))
        painter.drawRoundedRect(rect, 8, 8)

    def mousePressEvent(self, event):
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        end_pos = self.pos()
        if end_pos != self._drag_start_pos:
            self.moved.emit(self._drag_start_pos, end_pos)

    def itemChange(self, change, value):
        # update connected edges when the node position changes
        if change == QGraphicsItem.ItemPositionHasChanged:
            for e in list(self.edges):
                try:
                    e.update_path()
                except Exception:
                    pass
        return super().itemChange(change, value)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def commit_text_change(self, old_text, new_text):
        # emit a high-level event; commands will capture this
        self.textChanged.emit(old_text, new_text)

    def set_text(self, text):
        # set programmatically without triggering textChanged (user edits are handled via focusOut)
        self.text_item.setPlainText(text)
