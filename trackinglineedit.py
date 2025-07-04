from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Signal

class TrackingLineEdit(QLineEdit):
    focusEntered = Signal()
    focusExited = Signal()
    reloadEditor = Signal(QLineEdit)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_text = ""

    def focusInEvent(self, event):
        self._original_text = self.text()
        self.focusEntered.emit()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if self.text() != self._original_text:
            self.reloadEditor.emit(self)
        self.focusExited.emit()
        super().focusOutEvent(event)
