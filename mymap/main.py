# mymap/main.py
# Milestone 1 + full undo/redo for edges & deletes
# Requirements: PyQt5
# Run: python -m mymap.main

# standard libs
import sys
import json
import uuid

# Qt imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsObject,
    QGraphicsTextItem, QGraphicsPathItem, QToolBar, QAction, QFileDialog,
    QUndoStack, QUndoCommand, QShortcut
)
from PyQt5.QtGui import QPainterPath, QPen, QBrush, QColor, QFont, QPainter, QKeySequence
from PyQt5.QtCore import QRectF, QPointF, Qt, pyqtSignal



# --- EditableTextItem -------------------------------------------------------
class EditableTextItem(QGraphicsTextItem):
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


# --- NodeItem ---------------------------------------------------------------
class NodeItem(QGraphicsObject):
    moved = pyqtSignal(object, object)
    textChanged = pyqtSignal(object, object)

    def __init__(self, text="New Node", node_id=None):
        super().__init__()
        self.id = node_id or str(uuid.uuid4())
        self.text_item = EditableTextItem(text, self)
        f = QFont()
        f.setPointSize(10)
        self.text_item.setFont(f)

        self.padding = 8
        self.bg_color = QColor(255, 255, 200)

        self.setFlags(
            QGraphicsObject.ItemIsMovable |
            QGraphicsObject.ItemIsSelectable |
            QGraphicsObject.ItemSendsGeometryChanges
        )
        self._drag_start_pos = QPointF()
        self.edges = []

    def boundingRect(self) -> QRectF:
        rect = self.text_item.boundingRect()
        return QRectF(rect.left() - self.padding, rect.top() - self.padding,
                      rect.width() + 2 * self.padding, rect.height() + 2 * self.padding)

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
        if change == QGraphicsObject.ItemPositionHasChanged:
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
        self.textChanged.emit(old_text, new_text)

    def set_text(self, text):
        # set programmatically without triggering textChanged (focusOut handles user edits)
        self.text_item.setPlainText(text)


# --- EdgeItem ---------------------------------------------------------------
class EdgeItem(QGraphicsPathItem):
    def __init__(self, source: NodeItem, dest: NodeItem):
        super().__init__()
        self.source = source
        self.dest = dest
        # make edge selectable so user can click it
        self.setFlags(QGraphicsPathItem.ItemIsSelectable)
        pen = QPen(Qt.black)
        pen.setWidth(2)
        self._normal_pen = pen
        sel_pen = QPen(Qt.blue)
        sel_pen.setWidth(2)
        self._sel_pen = sel_pen
        self.setPen(self._normal_pen)
        self.setZValue(-1)
        # register with nodes
        self.source.add_edge(self)
        self.dest.add_edge(self)
        self.update_path()

    def update_path(self):
        s = self.source.sceneBoundingRect().center()
        d = self.dest.sceneBoundingRect().center()
        path = QPainterPath()
        path.moveTo(s)
        dx = (d.x() - s.x())
        cp1 = QPointF(s.x() + dx * 0.35, s.y())
        cp2 = QPointF(d.x() - dx * 0.35, d.y())
        path.cubicTo(cp1, cp2, d)
        self.setPath(path)

    def itemChange(self, change, value):
        from PyQt5.QtWidgets import QGraphicsItem
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(self._sel_pen)
            else:
                self.setPen(self._normal_pen)
        return super().itemChange(change, value)

    def remove(self):
        try:
            # unregister from nodes
            try:
                self.source.remove_edge(self)
            except Exception:
                pass
            try:
                self.dest.remove_edge(self)
            except Exception:
                pass
            sc = self.scene()
            if sc:
                sc.removeItem(self)
        except Exception:
            pass


# --- MindScene --------------------------------------------------------------
class MindScene(QGraphicsScene):
    nodeAdded = pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, NodeItem):
            self.nodeAdded.emit(item)

    def add_edge(self, src: NodeItem, dst: NodeItem) -> EdgeItem:
        e = EdgeItem(src, dst)
        super().addItem(e)
        return e

    def to_json(self):
        nodes = []
        edges = []
        for it in self.items():
            if isinstance(it, NodeItem):
                nodes.append({
                    "id": it.id,
                    "x": it.x(),
                    "y": it.y(),
                    "text": it.text_item.toPlainText()
                })
        for it in self.items():
            if isinstance(it, EdgeItem):
                edges.append({"from": it.source.id, "to": it.dest.id})
        return {"nodes": nodes, "edges": edges}

    def from_json(self, data):
        for it in list(self.items()):
            if isinstance(it, NodeItem) or isinstance(it, EdgeItem):
                self.removeItem(it)
        id_map = {}
        for n in data.get("nodes", []):
            ni = NodeItem(n.get("text", ""), node_id=n["id"])
            super().addItem(ni)
            ni.setPos(n.get("x", 0), n.get("y", 0))
            id_map[n["id"]] = ni
        for e in data.get("edges", []):
            s = id_map.get(e["from"])
            d = id_map.get(e["to"])
            if s and d:
                self.add_edge(s, d)


# --- Undo/Redo Commands ----------------------------------------------------
class AddNodeCommand(QUndoCommand):
    def __init__(self, scene: MindScene, pos: QPointF, text: str = "New Node"):
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


class MoveNodeCommand(QUndoCommand):
    def __init__(self, node: NodeItem, old_pos: QPointF, new_pos: QPointF):
        super().__init__("Move Node")
        self.node = node
        self.old = QPointF(old_pos)
        self.new = QPointF(new_pos)

    def undo(self):
        self.node.setPos(self.old)

    def redo(self):
        self.node.setPos(self.new)


class EditTextCommand(QUndoCommand):
    def __init__(self, node: NodeItem, old_text: str, new_text: str):
        super().__init__("Edit Node Text")
        self.node = node
        self.old = old_text
        self.new = new_text

    def undo(self):
        self.node.set_text(self.old)

    def redo(self):
        self.node.set_text(self.new)


class AddEdgeCommand(QUndoCommand):
    def __init__(self, scene: MindScene, src: NodeItem, dst: NodeItem):
        super().__init__("Add Edge")
        self.scene = scene
        self.src = src
        self.dst = dst
        self.edge = None

    def redo(self):
        if self.edge is None:
            self.edge = EdgeItem(self.src, self.dst)
        self.scene.addItem(self.edge)
        self.edge.update_path()

    def undo(self):
        if self.edge:
            self.edge.remove()


class DeleteEdgeCommand(QUndoCommand):
    def __init__(self, scene: MindScene, edge: EdgeItem):
        super().__init__("Delete Edge")
        self.scene = scene
        self.edge = edge

    def redo(self):
        if self.edge:
            self.edge.remove()

    def undo(self):
        if self.edge:
            # re-add edge to scene and register with nodes
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
    def __init__(self, scene: MindScene, node: NodeItem):
        super().__init__("Delete Node")
        self.scene = scene
        self.node = node
        # store edges connected so we can restore them on undo
        self.edges = list(node.edges)  # EdgeItem objects

        # store node state (position and text)
        self.pos = QPointF(node.pos())
        self.text = node.text_item.toPlainText()

    def redo(self):
        # remove connected edges first
        for e in list(self.edges):
            if e.scene() is not None:
                e.remove()
        # remove the node
        if self.node.scene() is not None:
            self.scene.removeItem(self.node)

    def undo(self):
        # re-add node and restore its state
        self.scene.addItem(self.node)
        self.node.setPos(self.pos)
        self.node.set_text(self.text)
        # re-add edges
        for e in list(self.edges):
            # only re-add if both endpoints still present
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


# --- Canvas View (zoom) ----------------------------------------------------
class CanvasView(QGraphicsView):
    def __init__(self, scene: MindScene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self._zoom = 0

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.0015 ** angle
            self.scale(factor, factor)
            self._zoom += angle
        else:
            super().wheelEvent(event)


# --- Main Window -----------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyMap — Milestone 1")
        self.scene = MindScene()
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)
        self.undo_stack = QUndoStack(self)
        self.scene.nodeAdded.connect(self.register_node_signals)
        self._build_toolbar()
        # Esc clears selection (small UX polish)
        QShortcut(QKeySequence("Esc"), self, self.clear_selection)

    def clear_selection(self):
        #Clear selection in the scene.
        self.scene.clearSelection()


    def _build_toolbar(self):
        tb = QToolBar("Main")
        self.addToolBar(tb)

        a_add = QAction("Add Node", self)
        a_add.triggered.connect(self.on_add_node)
        tb.addAction(a_add)

        a_link = QAction("Link selected", self)
        a_link.triggered.connect(self.on_link_selected)
        tb.addAction(a_link)

        a_save = QAction("Save", self)
        a_save.triggered.connect(self.on_save)
        a_save.setShortcut("Ctrl+S")
        tb.addAction(a_save)

        a_load = QAction("Load", self)
        a_load.triggered.connect(self.on_load)
        tb.addAction(a_load)

        a_undo = self.undo_stack.createUndoAction(self, "Undo")
        a_undo.setShortcut("Ctrl+Z")
        tb.addAction(a_undo)

        a_redo = self.undo_stack.createRedoAction(self, "Redo")
        a_redo.setShortcut("Ctrl+Y")
        tb.addAction(a_redo)

        a_delete = QAction("Delete", self)
        a_delete.setShortcut("Del")
        a_delete.triggered.connect(self.on_delete_selected)
        tb.addAction(a_delete)

        a_pdf = QAction("Export PDF", self)
        a_pdf.triggered.connect(self.on_export_pdf)
        tb.addAction(a_pdf)



    def on_add_node(self):
        pos = self.view.mapToScene(self.view.viewport().rect().center())
        cmd = AddNodeCommand(self.scene, pos)
        self.undo_stack.push(cmd)

    def on_link_selected(self):
        sel = [it for it in self.scene.selectedItems() if isinstance(it, NodeItem)]
        if len(sel) >= 2:
            cmd = AddEdgeCommand(self.scene, sel[0], sel[1])
            self.undo_stack.push(cmd)

    def register_node_signals(self, node: NodeItem):
        node.moved.connect(lambda old, new, n=node: self._on_node_moved(n, old, new))
        node.textChanged.connect(lambda old, new, n=node: self._on_node_text_edited(n, old, new))

    def _on_node_moved(self, node: NodeItem, old_pos: QPointF, new_pos: QPointF):
        cmd = MoveNodeCommand(node, old_pos, new_pos)
        self.undo_stack.push(cmd)

    def _on_node_text_edited(self, node: NodeItem, old_text: str, new_text: str):
        cmd = EditTextCommand(node, old_text, new_text)
        self.undo_stack.push(cmd)

    def on_delete_selected(self):
        """
        Delete selected edges and nodes as a single grouped undo action.
        Uses undo_stack.beginMacro/endMacro so one Ctrl+Z will restore all deleted items.
        """
        selected = list(self.scene.selectedItems())
        if not selected:
            return

        # Group into one undo entry
        self.undo_stack.beginMacro("Delete selection")
        try:
            # First delete selected edges
            for it in selected:
                if isinstance(it, EdgeItem):
                    cmd = DeleteEdgeCommand(self.scene, it)
                    self.undo_stack.push(cmd)

            # Then delete selected nodes (use the original 'selected' list so nodes known)
            for it in selected:
                if isinstance(it, NodeItem):
                    cmd = DeleteNodeCommand(self.scene, it)
                    self.undo_stack.push(cmd)
        finally:
            self.undo_stack.endMacro()

        # Optional small status feedback
        try:
            self.statusBar().showMessage("Deleted selection", 2000)
        except Exception:
            pass


    def on_save(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save Map", "", "MindMap JSON (*.mymap *.json)")
        if not fn:
            return
        data = self.scene.to_json()
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def on_load(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Load map", "", "MindMap JSON (*.mymap *.json)")
        if not fn:
            return
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        # clear undo stack when loading new file to avoid invalid commands
        self.undo_stack.clear()
        self.scene.from_json(data)

    def on_export_pdf(self):
        from PyQt5.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        fn, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not fn:
            return
        printer.setOutputFileName(fn)
        painter = QPainter()
        painter.begin(printer)
        self.scene.render(painter)
        painter.end()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()