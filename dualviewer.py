import difflib
from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QSplitter,
    QSpacerItem,
    QFileDialog,
    QSizePolicy, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from codeeditor import CodeEditor
from trackinglineedit import TrackingLineEdit

class DualViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Side-by-Side File Diff Viewer")

        # Create components
        self.editor1 = CodeEditor()
        self.editor2 = CodeEditor()

        # Create top bar for editor1
        self.textbox1 = TrackingLineEdit()
        self.textbox1.setPlaceholderText("Path for Left file compare...")
        self.button1 = QPushButton("...")
        self.textbox1.reloadEditor.connect(self.reloadWithPopup)
        self.textbox1.returnPressed.connect(self.textBoxEnterKey)
        self.button1.clicked.connect(self.browseFile)

        editor1_container = QWidget()
        editor1_layout = QVBoxLayout(editor1_container)
        editor1_top_bar = QHBoxLayout()
        editor1_top_bar.addSpacerItem(QSpacerItem(8, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        editor1_top_bar.addWidget(self.textbox1)
        editor1_top_bar.addWidget(self.button1)
        editor1_layout.addLayout(editor1_top_bar)
        editor1_layout.addWidget(self.editor1)
        editor1_layout.setContentsMargins(0, 0, 0, 0)

        # Create top bar for editor2
        self.textbox2 = TrackingLineEdit()
        self.textbox2.setPlaceholderText("Path for Right file compare...")
        self.button2 = QPushButton("...")
        self.textbox2.reloadEditor.connect(self.reloadWithPopup)
        self.textbox2.returnPressed.connect(self.textBoxEnterKey)
        self.button2.clicked.connect(self.browseFile)

        editor2_container = QWidget()
        editor2_layout = QVBoxLayout(editor2_container)
        editor2_top_bar = QHBoxLayout()
        editor2_top_bar.addWidget(self.textbox2)
        editor2_top_bar.addWidget(self.button2)
        editor2_top_bar.addSpacerItem(QSpacerItem(8, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        editor2_layout.addLayout(editor2_top_bar)
        editor2_layout.addWidget(self.editor2)
        editor2_layout.setContentsMargins(0, 0, 0, 0)

        # Sync scrollbars
        self.editor1.verticalScrollBar().valueChanged.connect(self.syncScrollEditor2)
        self.editor2.verticalScrollBar().valueChanged.connect(self.syncScrollEditor1)

        # Add to splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(editor1_container)
        splitter.addWidget(editor2_container)
        splitter.setSizes([1, 1])

        # Set main layout
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(container)
        self.resize(1000, 600)

        #self.loadFiles()

    # Boilerplate for textbox and button signals

    def textBoxEnterKey(self):
        sender = self.sender()
        self.loadFile(sender.text(), sender)

        # Trick the sender into not triggering an exit signal
        sender._original_text = sender.text()

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

    def browseFile(self):
        sender = self.sender()
        header = 'Open Left File' if sender == self.button1 else 'Open Right File'
        filename, _ = QFileDialog.getOpenFileName(self, header)

        if filename != '':
            textbox = self.textbox1 if sender == self.button1 else self.textbox2
            textbox.setText(filename)

            self.loadFile(filename, sender)


    def loadFile(self, filename: str, sender: TrackingLineEdit | QPushButton):
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
        except Exception as e:
            lines = [str(e)]

        self.fillEditor(lines, self.editor1 if sender == self.textbox1 or sender == self.button1 else self.editor2)

    def fillEditor(self, contents, editor):
        editor.setPlainText("".join(contents))

    def reloadWithPopup(self, sender: TrackingLineEdit):
        reply = QMessageBox.question(
            self,
            'Reload File?',
            '{} File Path Change Detected. Reload File?'.format('Left' if sender == self.textbox1 else 'Right'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.loadFile(sender.text().strip(), sender)
        

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



