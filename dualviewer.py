import difflib
from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QSplitter, QFileDialog, QVBoxLayout
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from codeeditor import CodeEditor

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



