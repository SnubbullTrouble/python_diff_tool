import difflib
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QHBoxLayout, QWidget,
    QSplitter, QFileDialog, QVBoxLayout, QTextEdit
)
from PySide6.QtGui import QPainter, QColor, QTextFormat, QTextCursor, QTextCharFormat
from PySide6.QtCore import Qt, QRect

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return self.codeEditor.lineNumberAreaSize()

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def apply_line_backgrounds(self, highlights):
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()

        fmt_default = QTextCharFormat()
        fmt_default.setBackground(Qt.white)

        for i in range(self.blockCount()):
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, i)
            cursor.select(QTextCursor.LineUnderCursor)

            fmt = QTextCharFormat(fmt_default)
            if i in highlights:
                fmt.setBackground(highlights[i])
            cursor.setCharFormat(fmt)

        cursor.endEditBlock()


class DualViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Side-by-Side File Diff Viewer")

        self.editor1 = CodeEditor()
        self.editor2 = CodeEditor()

        self.editor1.verticalScrollBar().valueChanged.connect(self.syncScrollEditor2)
        self.editor2.verticalScrollBar().valueChanged.connect(self.syncScrollEditor1)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor1)
        splitter.addWidget(self.editor2)
        splitter.setSizes([1, 1])

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(container)
        self.resize(1000, 600)

        self.loadFiles()

    def syncScrollEditor2(self, value):
        if self.editor2.verticalScrollBar().value() != value:
            self.editor2.verticalScrollBar().setValue(value)

    def syncScrollEditor1(self, value):
        if self.editor1.verticalScrollBar().value() != value:
            self.editor1.verticalScrollBar().setValue(value)

    def loadFiles(self):
        file1, _ = QFileDialog.getOpenFileName(self, "Open First File")
        file2, _ = QFileDialog.getOpenFileName(self, "Open Second File")

        if file1 and file2:
            with open(file1, 'r', encoding='utf-8') as f1:
                content1 = f1.readlines()
            with open(file2, 'r', encoding='utf-8') as f2:
                content2 = f2.readlines()

            self.editor1.setPlainText("".join(content1))
            self.editor2.setPlainText("".join(content2))

            self.diff_files(content1, content2)

    def diff_files(self, lines1, lines2):
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))

        # Line color mapping
        editor1_colors = {}
        editor2_colors = {}

        i1 = i2 = 0
        for line in diff:
            if line.startswith("  "):  # same
                i1 += 1
                i2 += 1
            elif line.startswith("- "):  # line in file1 only
                editor1_colors[i1] = QColor("#ffdddd")  # red-ish
                i1 += 1
            elif line.startswith("+ "):  # line in file2 only
                editor2_colors[i2] = QColor("#ddffdd")  # green-ish
                i2 += 1
            elif line.startswith("? "):  # line with a change indicator (not always useful)
                # optionally add yellow to mark changed lines
                pass

        self.editor1.apply_line_backgrounds(editor1_colors)
        self.editor2.apply_line_backgrounds(editor2_colors)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    viewer = DualViewer()
    viewer.show()
    sys.exit(app.exec())
