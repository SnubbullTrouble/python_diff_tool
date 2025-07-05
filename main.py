from PySide6.QtWidgets import QApplication
from dualviewer import DualViewer
import sys, os
from sessionutils import validate_session_variables

if __name__ == "__main__":
    validate_session_variables()
    app = QApplication(sys.argv)
    viewer = DualViewer()
    viewer.show()
    sys.exit(app.exec())
