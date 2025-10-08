from PySide6.QtGui import QUndoCommand

class DeleteEdgeCommand(QUndoCommand):
    def __init__(self, scene, edge):
        super().__init__("Delete Edge")
        self.scene = scene
        self.edge = edge

    def redo(self):
        if self.edge:
            self.edge.remove()

    def undo(self):
        if self.edge:
            self.scene.addItem(self.edge)
            try:
                self.edge.source.add_edge(self.edge)
            except Exception:
                pass
            try:
                self.edge.dest.add_edge(self.edge)
            except Exception:
                pass
            self.edge.update_path()
