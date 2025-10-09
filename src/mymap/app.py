#mymap/src/mymap/app.py
import sys
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QPalette
from PySide6.QtCore import Qt
from mymap.ui.main_window import MainWindow

def run(argv=None):
    argv = argv or sys.argv
    app = QApplication(argv)

    # === Load PePik logo (ensure correct path) ===
    # Tip: put logo in "assets/" folder (e.g., src/mymap/assets/pepik_logo.png)
    pix = QPixmap("mymap/src/mymap/assets/logo.png")  # <-- adjust if needed

    # If logo fails to load, fallback to plain background
    if pix.isNull():
        pix = QPixmap(600, 400)
        pix.fill(app.palette().color(QPalette.Window))

    # === Create splash screen ===
    splash = QSplashScreen(pix)
    splash.setFont(QFont("Arial", 12))
    splash.showMessage(
        "Memuat PePik…\nSatu Pikiran, Sejuta Ide",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.white
    )

    splash.show()
    app.processEvents()

    # === Create and show main window ===
    win = MainWindow()
    win.resize(1000, 700)

    try:
        win.create_initial_main_node()
    except Exception as e:
        print("Warning: could not create initial node:", e)

    win.show()
    splash.finish(win)

    return app.exec()

if __name__ == "__main__":
    raise SystemExit(run())
