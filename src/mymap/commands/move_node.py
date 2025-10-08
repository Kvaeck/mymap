from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF

class MoveNodeCommand(QUndoCommand):
    def __init__(self, node, old_pos: QPointF, new_pos: QPointF):
        super().__init__("Move Node")
        self.node = node
        self.old = QPointF(old_pos)
        self.new = QPointF(new_pos)

    def undo(self):
        self.node.setPos(self.old)

    def redo(self):
        self.node.setPos(self.new)
