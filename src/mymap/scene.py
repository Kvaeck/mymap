# src/mymap/scene.py
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal

from mymap.gfx.node_item import NodeItem
from mymap.gfx.edge_item import EdgeItem


class MindScene(QGraphicsScene):
    """Scene that emits nodeAdded when NodeItem instances are added."""

    nodeAdded = Signal(object)

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
                nodes.append(
                    {
                        "id": it.id,
                        "x": it.x(),
                        "y": it.y(),
                        "text": it.text_item.toPlainText(),
                    }
                )
        for it in self.items():
            if isinstance(it, EdgeItem):
                edges.append({"from": it.source.id, "to": it.dest.id})
        return {"nodes": nodes, "edges": edges}

    def from_json(self, data):
        # remove old items
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
