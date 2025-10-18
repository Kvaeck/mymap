# mymap/src/mymap/app.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QFont, QColor, QPalette
from PySide6.QtCore import Qt
from mymap.ui.main_window import MainWindow
from mymap.ui.splash import SplashScreen


def apply_pepik_theme(app: QApplication):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F7F9FC"))
    palette.setColor(QPalette.WindowText, QColor("#222831"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#F7F9FC"))
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipText, QColor("#222831"))
    palette.setColor(QPalette.Text, QColor("#222831"))
    palette.setColor(QPalette.Button, QColor("#4B6AFC"))
    palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Highlight, QColor("#FFCC33"))
    palette.setColor(QPalette.HighlightedText, QColor("#222831"))
    app.setPalette(palette)

    # Font: if you bundle "Inter" put it in assets/ and register with QFontDatabase.
    app.setFont(QFont("Inter", 11))


def run(argv=None):
    argv = argv or sys.argv
    app = QApplication(argv)

    # Apply the PePik theme early
    apply_pepik_theme(app)

    # === Load PePik logo (robust path) ===
    base_dir = Path(__file__).resolve().parents[1]  # src/mymap
    assets_dir = base_dir / "assets"
    logo_path = assets_dir / "logo.png"   # put your logo here
    if not logo_path.exists():
        # try alternative path for dev setups
        logo_path = Path.cwd() / "src" / "mymap" / "assets" / "logo.png"

    if logo_path.exists():
        pix = QPixmap(str(logo_path))
    else:
        pix = QPixmap(600, 400)
        pix.fill(app.palette().color(QPalette.Window))

    # === Create splash screen ===
    splash = QSplashScreen(pix)
    splash.setFont(QFont("Arial", 12))

    splash.showMessage(
        "Memuat PePik…\nSatu Pikiran, Sejuta Ide",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        QColor("white")
    )

    splash = SplashScreen(pix)
    splash.show()
    app.processEvents()
    
    # === Initialize services (license + exporter) and pass to MainWindow ===
    from mymap.services.license_manager import LicenseManager
    from mymap.services.exporter import ExportService

    license_manager = LicenseManager()           # stores ~/.pepik/pepik_license.json, exports.json
    export_service = ExportService(license_manager)

    # === Create and show main window ===
    win = MainWindow(license_manager=license_manager, export_service=export_service)
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
