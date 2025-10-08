from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF
from mymap.gfx.node_item import NodeItem

class AddNodeCommand(QUndoCommand):
    def __init__(self, scene, pos: QPointF, text: str = "New Node"):
        super().__init__("Add Node")
        self.scene = scene
        self.pos = pos
        self.text = text
        self.node = None

    def redo(self):
        if self.node is None:
            self.node = NodeItem(self.text)
        self.scene.addItem(self.node)
        self.node.setPos(self.pos)

    def undo(self):
        for e in list(self.node.edges):
            e.remove()
        self.scene.removeItem(self.node)
