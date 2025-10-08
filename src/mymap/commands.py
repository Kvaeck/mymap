# src/mymap/commands.py
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF

# Import types lazily inside methods to avoid import cycles
# Commands operate on scene, NodeItem and EdgeItem instances passed in.


class AddNodeCommand(QUndoCommand):
    def __init__(self, scene, pos: QPointF, text: str = "New Node"):
        super().__init__("Add Node")
        self.scene = scene
        self.pos = pos
        self.text = text
        self.node = None

    def redo(self):
        from mymap.gfx.node_item import NodeItem

        if self.node is None:
            self.node = NodeItem(self.text)
        self.scene.addItem(self.node)
        self.node.setPos(self.pos)

    def undo(self):
        for e in list(self.node.edges):
            e.remove()
        self.scene.removeItem(self.node)


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


class EditTextCommand(QUndoCommand):
    def __init__(self, node, old_text: str, new_text: str):
        super().__init__("Edit Node Text")
        self.node = node
        self.old = old_text
        self.new = new_text

    def undo(self):
        self.node.set_text(self.old)

    def redo(self):
        self.node.set_text(self.new)


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


class DeleteNodeCommand(QUndoCommand):
    def __init__(self, scene, node):
        super().__init__("Delete Node")
        self.scene = scene
        self.node = node
        # store edges connected so we can restore them on undo
        self.edges = list(node.edges)

        # store node state (position and text)
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
