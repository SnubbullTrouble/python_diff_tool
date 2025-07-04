from PySide6.QtWidgets import QApplication
from dualviewer import DualViewer

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    viewer = DualViewer()
    viewer.show()
    sys.exit(app.exec())
