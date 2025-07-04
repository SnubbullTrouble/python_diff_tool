from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import pyqtSignal

class TrackingLineEdit(QLineEdit):
    focusEntered = pyqtSignal()
    focusExited = pyqtSignal(bool)  # Emits True if text changed, False if same

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_text = ""

    def focusInEvent(self, event):
        self._original_text = self.text()
        self.focusEntered.emit()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        text_changed = self.text() != self._original_text
        self.focusExited.emit(text_changed)
        super().focusOutEvent(event)
