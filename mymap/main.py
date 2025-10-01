#main.py

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from mymap import __appname__, __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__appname__} v{__version__}")
        self.resize(1000, 700)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
