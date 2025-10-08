# src/mymap/app.py
import sys
from PySide6.QtWidgets import QApplication

# import your real main window; change path if your main window lives elsewhere
try:
    from mymap.ui.widgets import MainWindow  # if you named your main window class here
except Exception:
    # fallback stub if widgets.MainWindow not ready yet
    from PySide6.QtWidgets import QMainWindow, QLabel
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("MyMap (stub)")
            self.setCentralWidget(QLabel("Replace with real main window"))

def run(argv=None):
    argv = argv or sys.argv
    app = QApplication(argv)
    win = MainWindow()
    win.resize(1000, 700)
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(run())

