from PySide6.QtGui import QUndoCommand

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
