from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF

class DeleteNodeCommand(QUndoCommand):
    def __init__(self, scene, node):
        super().__init__("Delete Node")
        self.scene = scene
        self.node = node
        self.edges = list(node.edges)
        self.pos = QPointF(node.pos())
        self.text = node.text_item.toPlainText()

    def redo(self):
        for e in list(self.edges):
            if e.scene() is not None:
                e.remove()
        if self.node.scene() is not None:
            self.scene.removeItem(self.node)

    def undo(self):
        self.scene.addItem(self.node)
        self.node.setPos(self.pos)
        self.node.set_text(self.text)
        for e in list(self.edges):
            if e.source is not None and e.dest is not None:
                self.scene.addItem(e)
                try:
                    e.source.add_edge(e)
                except Exception:
                    pass
                try:
                    e.dest.add_edge(e)
                except Exception:
                    pass
                e.update_path()
