from PySide6.QtWidgets import QWidget

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return self.codeEditor.lineNumberAreaSize()

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)
