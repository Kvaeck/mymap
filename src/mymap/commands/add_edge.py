from PySide6.QtGui import QUndoCommand

class AddEdgeCommand(QUndoCommand):
    def __init__(self, scene, src, dst):
        super().__init__("Add Edge")
        self.scene = scene
        self.src = src
        self.dst = dst
        self.edge = None

    def redo(self):
        from mymap.gfx.edge_item import EdgeItem
        if self.edge is None:
            self.edge = EdgeItem(self.src, self.dst)
        self.scene.addItem(self.edge)
        self.edge.update_path()

    def undo(self):
        if self.edge:
            self.edge.remove()
