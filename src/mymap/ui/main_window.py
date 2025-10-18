# src/mymap/ui/main_window.py
import json
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QToolBar,
    QFileDialog,
    QStatusBar,
)
from PySide6.QtGui import QAction, QKeySequence, QUndoStack, QShortcut, QFont, QUndoCommand
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


class SpawnBranchCommand(QUndoCommand):
    """
    Undoable command that creates a NodeItem and (optionally) an EdgeItem linking it to `anchor`.
    This implementation **reuses** existing AddNodeCommand and AddEdgeCommand so behavior,
    bookkeeping, and undo/redo remain consistent across the app.
    """

    def __init__(self, scene, anchor: Optional[NodeItem], pos: QPointF, text: str = "New", description: str = "Spawn branch"):
        super().__init__(description)
        self.scene = scene
        self.anchor = anchor  # may be None
        self.pos = pos
        self.text = text

        # internal sub-commands (created here but executed in redo)
        self._add_node_cmd: Optional[AddNodeCommand] = AddNodeCommand(self.scene, self.pos, self.text)
        self._add_edge_cmd: Optional[AddEdgeCommand] = None  # created after node exists (in redo)

    def redo(self):
        # create the node via the existing AddNodeCommand
        if self._add_node_cmd is not None:
            # calling redo() repeatedly is safe: AddNodeCommand is idempotent in its logic
            self._add_node_cmd.redo()

        # if anchor provided, create the edge using AddEdgeCommand
        if self.anchor is not None:
            # instantiate AddEdgeCommand if not yet created
            if self._add_edge_cmd is None:
                # dst is the node created by AddNodeCommand
                dst_node = getattr(self._add_node_cmd, "node", None)
                # sanity guard: if node is still None (shouldn't be), attempt to use scene lookup
                if dst_node is None:
                    # fallback: try to find a node at self.pos (rare); else raise
                    raise RuntimeError("SpawnBranchCommand: couldn't determine created node to link edge to.")
                self._add_edge_cmd = AddEdgeCommand(self.scene, self.anchor, dst_node)
            # perform edge creation
            self._add_edge_cmd.redo()

    def undo(self):
        # undo edge first (if created)
        if self._add_edge_cmd is not None:
            try:
                self._add_edge_cmd.undo()
            except Exception:
                pass
        # then undo node
        if self._add_node_cmd is not None:
            try:
                self._add_node_cmd.undo()
            except Exception:
                pass


class LabelNodeCommand(QUndoCommand):
    """
    Undoable command that creates a label-mode NodeItem (text-only, no rounded rect).
    Use this for 'branch-only' handles.
    """
    def __init__(self, scene, pos: QPointF, text: str = ""):
        super().__init__("Add label node")
        self.scene = scene
        self.pos = pos
        self.text = text
        self.node: Optional[NodeItem] = None

    def redo(self):
        if self.node is None:
            # create label-mode node
            self.node = NodeItem(self.text, label_mode=True)
        if self.node.scene() is None:
            self.scene.addItem(self.node)
        self.node.setPos(self.pos)

    def undo(self):
        if self.node:
            try:
                for e in list(self.node.edges):
                    e.remove()
            except Exception:
                pass
            try:
                self.scene.removeItem(self.node)
            except Exception:
                pass


class MainWindow(QMainWindow):
    def __init__(self, license_manager=None, export_service=None):
        super().__init__()
        self.setStyleSheet("background-color: #E7ECF7;")
        self.setWindowTitle("PePik")

        # services (optional)
        self.license_manager = license_manager
        self.export_service = export_service

        self.scene = MindScene()
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)
        self.undo_stack = QUndoStack(self)
        self.scene.nodeAdded.connect(self.register_node_signals)

        # Connect canvas signals (branch/sister spawn)
        self.view.spawn_branch_from_center.connect(self._on_spawn_branch_from_center)
        self.view.spawn_branch_with_node.connect(self._on_spawn_branch_with_node)
        self.view.spawn_sister_branch.connect(self._on_spawn_sister_branch)

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

        # connect handle spawn signals from this node
        try:
            node.spawn_branch.connect(lambda scene_pos, n=node: self._on_node_spawn_branch(n, scene_pos))
            node.spawn_branch_with_node.connect(lambda scene_pos, n=node: self._on_node_spawn_branch_with_node(n, scene_pos))
        except Exception:
            pass

    def _on_node_spawn_branch(self, node: NodeItem, scene_pos: QPointF):
        """
        Handle branch-only creation from a node's handle.
        Behavior:
          - create a small label-node (label_mode=True) at scene_pos (undoable)
          - create an edge from `node` to that label-node (undoable)
        """
        label_cmd = LabelNodeCommand(self.scene, scene_pos, text="")
        self.undo_stack.push(label_cmd)

        dst = label_cmd.node
        if dst is None:
            return

        edge_cmd = AddEdgeCommand(self.scene, node, dst)
        self.undo_stack.push(edge_cmd)

        try:
            self.scene.clearSelection()
            dst.setSelected(True)
            self.view.centerOn(dst)
        except Exception:
            pass

    def _on_node_spawn_branch_with_node(self, node: NodeItem, scene_pos: QPointF):
        """
        Handle full branch+node creation from a node's handle.
        Uses existing AddNodeCommand + AddEdgeCommand to remain consistent with undo stack.
        """
        # create a normal node at scene_pos and edge anchor->new
        add_node_cmd = AddNodeCommand(self.scene, scene_pos, "New")
        self.undo_stack.push(add_node_cmd)
        dst = add_node_cmd.node
        if dst is None:
            return
        add_edge_cmd = AddEdgeCommand(self.scene, node, dst)
        self.undo_stack.push(add_edge_cmd)
        try:
            self.scene.clearSelection()
            dst.setSelected(True)
            self.view.centerOn(dst)
        except Exception:
            pass



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

    # ---------------------------
    # helper: create initial "Main Idea" node centered on the view
    def create_initial_main_node(self):
        # If there are already nodes, don't create another
        existing_nodes = [it for it in self.scene.items() if isinstance(it, NodeItem)]
        if existing_nodes:
            return

        center = self.view.mapToScene(self.view.viewport().rect().center())
        # create a NodeItem with larger font and padding
        node = NodeItem("Main Idea")
        # enlarge font
        f = node.text_item.font()
        f.setPointSize(20)   # big and readable; adjust as you like (e.g., 18-24)
        f.setBold(True)
        node.text_item.setFont(f)
        # increase padding for a more spacious look
        node.padding = 14
        self.scene.addItem(node)
        node.setPos(center)
        # ensure edges (none) updated & view recenters slightly
        node.update()
        self.view.centerOn(node)

    # ---------------------------
    # Canvas signal handlers for branch creation

    def _find_nearest_node_to_point(self, point: QPointF, max_distance: float = 300.0):
        """Return nearest NodeItem to `point` within max_distance, or None."""
        nodes = [it for it in self.scene.items() if isinstance(it, NodeItem)]
        if not nodes:
            return None
        best = None
        best_dist = None
        for n in nodes:
            d = (n.scenePos() - point).manhattanLength()
            if best is None or d < best_dist:
                best = n
                best_dist = d
        if best_dist is not None and best_dist <= max_distance:
            return best
        return None

    def _on_spawn_branch_from_center(self, scene_pos: QPointF):
        """Create a new branch attached to the central/main node — UNDOABLE."""
        pusat = self._find_nearest_node_to_point(self.view.mapToScene(self.view.viewport().rect().center()))
        if pusat is None:
            # fallback: spawn a freestanding node (undoable but no anchor edge)
            pos = scene_pos
            self._spawn_freestanding_node_undoable(pos, text="Idea")
            return

        # compute offset position to place the new child branch
        offset = QPointF(140, 0)  # to the right by default
        view_center = self.view.mapToScene(self.view.viewport().rect().center())
        if pusat.scenePos().x() > view_center.x():
            # pusat is on the right side — spawn on left
            offset = QPointF(-140, 0)

        new_pos = pusat.scenePos() + offset
        cmd = SpawnBranchCommand(self.scene, pusat, new_pos, text="New", description="Spawn branch")
        self.undo_stack.push(cmd)
        # select and focus the new node: the redo already added it, but ensure selection & centering.
        try:
            new_node = cmd.node
            if new_node:
                self.scene.clearSelection()
                new_node.setSelected(True)
                self.view.centerOn(new_node)
        except Exception:
            pass

    def _spawn_freestanding_node_undoable(self, pos: QPointF, text: str = "Idea"):
        class AddSingleNodeCmd(QUndoCommand):
            def __init__(self, scene, pos, text):
                super().__init__("Add node")
                self.scene = scene
                self.pos = pos
                self.text = text
                self.node = None

            def redo(self):
                if self.node is None:
                    self.node = NodeItem(self.text)
                if self.node.scene() is None:
                    self.scene.addItem(self.node)
                self.node.setPos(self.pos)

            def undo(self):
                if self.node:
                    for e in list(self.node.edges):
                        e.remove()
                    try:
                        self.scene.removeItem(self.node)
                    except Exception:
                        pass

        cmd = AddSingleNodeCmd(self.scene, pos, text)
        self.undo_stack.push(cmd)
        # center and select
        try:
            node = cmd.node
            if node:
                self.scene.clearSelection()
                node.setSelected(True)
                self.view.centerOn(node)
        except Exception:
            pass



    def _on_spawn_branch_with_node(self, scene_pos: QPointF):
        """Placeholder for future drag-handle → create branch + node behavior."""
        # For now behave same as spawn_branch_from_center but using scene_pos
        self._on_spawn_branch_from_center(scene_pos)

    def _on_spawn_sister_branch(self):
        """
        When Enter is pressed: create a sister branch for the selected node.
        Logic:
         - if exactly one node is selected, attempt to find its parent (edge where dest == selected)
         - if parent found, create new node and connect parent -> new node (sibling)
         - else, create a child node connected to the selected node
        """
        sel = [it for it in self.scene.selectedItems() if isinstance(it, NodeItem)]
        if len(sel) != 1:
            # do nothing unless exactly one node is selected
            return
        selected_node = sel[0]

        # find parent: an edge where edge.dest is the selected node
        parent = None
        for it in self.scene.items():
            if isinstance(it, EdgeItem):
                try:
                    if it.dest is selected_node:
                        parent = it.source
                        break
                except Exception:
                    # safe-guard: older EdgeItem may have different attribute names
                    pass

        if parent is None:
            # no parent -> create child of selected_node
            anchor = selected_node
        else:
            # create sibling attached to parent
            anchor = parent

        # place new node near selected node but slightly offset; if anchor is parent, offset on opposite side
        if anchor is selected_node:
            new_pos = selected_node.scenePos() + QPointF(120, 0)
        else:
            # sibling: place mirroring selected node relative to parent
            direction = selected_node.scenePos() - anchor.scenePos()
            # rotate 90 degrees a bit to avoid overlap
            new_pos = selected_node.scenePos() + QPointF(direction.y() * 0.2 + 120, -direction.x() * 0.1)

        # Use SpawnBranchCommand so the action is undoable
        cmd = SpawnBranchCommand(self.scene, anchor, new_pos, text="New", description="Spawn sister")
        self.undo_stack.push(cmd)
        try:
            new_node = cmd.node
            if new_node:
                self.scene.clearSelection()
                new_node.setSelected(True)
                self.view.centerOn(new_node)
        except Exception:
            pass
