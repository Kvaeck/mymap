# src/mymap/ui/splash.py
from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QFont, QColor
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Slot

class SplashScreen(QSplashScreen):
    """
    Enhanced splash screen with animated 'loading...' dots and fade-out.
    Usage:
      splash = SplashScreen(pixmap, parent=None)
      splash.show()
      ... do loading work ...
      splash.finish_with_fade(main_window)
    """
    def __init__(self, pixmap: QPixmap, parent=None, tagline: str = "Satu Pikiran, Sejuta Ide"):
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.setParent(parent)
        self.setMask(pixmap.mask() if not pixmap.isNull() else None)

        # small overlay label for loading text
        self._label = QLabel(self)
        self._label.setAttribute(Qt.WA_TranslucentBackground)
        self._label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        font = QFont()
        font.setPointSize(11)
        self._label.setFont(font)
        self._base_text = "Memuat PePik…"
        self._tagline = tagline
        self._dots = 0
        self._label.setStyleSheet("color: white;")
        self._update_label()

        # timer for dots animation
        self._timer = QTimer(self)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # position label near the bottom center of the splash pixmap
        w = self.size().width()
        h = self.size().height()
        margin = 24
        self._label.setGeometry(margin, h - 80, w - margin * 2, 60)

    @Slot()
    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._update_label()

    def _update_label(self):
        dots = "." * self._dots
        text = f"{self._base_text}{dots}\n{self._tagline}"
        self._label.setText(text)

    def finish_with_fade(self, window, duration: int = 600):
        """
        Finish splash with fade-out animation, then call QSplashScreen.finish(window).
        """
        self._timer.stop()

        # fade animation on splash window opacity
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(duration)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)

        # when animation finishes, call underlying finish and delete the splash
        def _on_finished():
            try:
                super(SplashScreen, self).finish(window)
            except Exception:
                # fallback: just hide
                self.hide()
            try:
                self.deleteLater()
            except Exception:
                pass

        anim.finished.connect(_on_finished)
        anim.start()
