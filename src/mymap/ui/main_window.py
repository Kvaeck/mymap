# src/mymap/ui/main_window.py
import json
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QAction,
    QFileDialog,
    QShortcut,
    QStatusBar,
)
from PySide6.QtGui import QKeySequence, QUndoStack
from PySide6.QtCore import QPointF

from mymap.scene import MindScene
from mymap.gfx.canvas import CanvasView
from mymap.commands import (
    AddNodeCommand,
    MoveNodeCommand,
    EditTextCommand,
    AddEdgeCommand,
    DeleteEdgeCommand,
    DeleteNodeCommand,
)
from mymap.gfx.node_item import NodeItem
from mymap.gfx.edge_item import EdgeItem


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #E7ECF7;")
        self.setWindowTitle("MyMap — Milestone 1")
        self.scene = MindScene()
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)
        self.undo_stack = QUndoStack(self)
        self.scene.nodeAdded.connect(self.register_node_signals)
        self._build_toolbar()
        QShortcut(QKeySequence("Esc"), self, self.clear_selection)
        self.setStatusBar(QStatusBar(self))

    def clear_selection(self):
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
        a_save.setShortcut(QKeySequence("Ctrl+S"))
        tb.addAction(a_save)

        a_load = QAction("Load", self)
        a_load.triggered.connect(self.on_load)
        tb.addAction(a_load)

        a_undo = self.undo_stack.createUndoAction(self, "Undo")
        a_undo.setShortcut(QKeySequence("Ctrl+Z"))
        tb.addAction(a_undo)

        a_redo = self.undo_stack.createRedoAction(self, "Redo")
        a_redo.setShortcut(QKeySequence("Ctrl+Y"))
        tb.addAction(a_redo)

        a_delete = QAction("Delete", self)
        a_delete.setShortcut(QKeySequence("Del"))
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
        selected = list(self.scene.selectedItems())
        if not selected:
            return
        self.undo_stack.beginMacro("Delete selection")
        try:
            for it in selected:
                if isinstance(it, EdgeItem):
                    cmd = DeleteEdgeCommand(self.scene, it)
                    self.undo_stack.push(cmd)
            for it in selected:
                if isinstance(it, NodeItem):
                    cmd = DeleteNodeCommand(self.scene, it)
                    self.undo_stack.push(cmd)
        finally:
            self.undo_stack.endMacro()
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
        self.undo_stack.clear()
        self.scene.from_json(data)

    def on_export_pdf(self):
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtGui import QPainter

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
