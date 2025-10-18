from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Node:
    id: str
    text: str
    x: float = 0
    y: float = 0

@dataclass
class Edge:
    src: str
    dst: str

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, src: str, dst: str):
        self.edges.append(Edge(src, dst))
