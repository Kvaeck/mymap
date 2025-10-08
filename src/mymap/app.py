# src/mymap/app.py
import sys
from PySide6.QtWidgets import QApplication
from mymap.ui.main_window import MainWindow

def run(argv=None):
    argv = argv or sys.argv
    app = QApplication(argv)
    win = MainWindow()
    win.resize(1000, 700)
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(run())
