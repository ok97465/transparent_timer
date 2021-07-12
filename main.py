"""Transparent timer."""
# Standard library imports
import sys

# Third party imports
import qdarkstyle
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import QPoint, Qt, QTimer
from PySide2.QtWidgets import (
    QApplication, QDesktopWidget, QMainWindow, QProgressBar)

MAIN_WIDTH = 200
MAIN_HEIGHT = 60


class TimerProgressBar(QProgressBar):
    """Progressbar for Timer."""

    def __init__(self, parent):
        """."""
        super().__init__(parent)
        self.timer_req = 0
        self.timer_cur = 0
        self.setValue(0)

    def set_timer(self, val: int):
        """Set timer.

        Args:
            val: Minute
        """
        self.timer_req = val * 60
        self.timer_cur = 0
        self.setValue(0)
        self.setMaximum(self.timer_req)
        self.setFormat(f"%p% of {val}min")

    def add_sec(self, val: int):
        """Add second.

        Args:
            val: Second
        """
        if self.timer_cur < self.timer_req:
            self.timer_cur += val
            self.setValue(self.timer_cur)


class TransparentWindow(QMainWindow):
    """Transparent window."""

    def __init__(self):
        """."""
        super().__init__()

        icon = QIcon()
        icon.addPixmap(QPixmap('timer.ico'), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        # <MainWindow Properties>
        self.setFixedSize(MAIN_WIDTH, MAIN_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.move_to_topright()
        self.setWindowOpacity(0.3)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # </MainWindow Properties>
        self.progress_bar = TimerProgressBar(self)
        self.setCentralWidget(self.progress_bar)

        self.old_pos = self.pos()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.progress_bar.add_sec(1))
        self.timer.start()

    def move_to_topright(self):
        """Move main window to top left."""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().topRight()
        qr.moveTopRight(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        """Save mouse position."""
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        """Move window as mush as mouse moves."""
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def keyPressEvent(self, event):
        """Set timer using pressing key."""
        key = event.key()
        shift_pressed = event.modifiers() & Qt.ShiftModifier

        if shift_pressed:
            if key == Qt.Key_R:
                self.progress_bar.set_timer(15)
        else:
            if key == Qt.Key_W:
                self.progress_bar.set_timer(25)
            elif key == Qt.Key_R:
                self.progress_bar.set_timer(5)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())
