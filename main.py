"""Transparent timer."""
# Standard library imports
import sys

# Third party imports
import qdarkstyle
from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QGuiApplication, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QMenu,
    QProgressBar,
    QSystemTrayIcon,
)

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

MAIN_WIDTH = 100
MAIN_HEIGHT = 30


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

        # <MainWindow Properties>
        self.setFixedSize(MAIN_WIDTH, MAIN_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.move_window()
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

    def move_window(self):
        """Move main window to top left."""
        qr = self.frameGeometry()
        screen = QGuiApplication.primaryScreen()
        cp = screen.availableGeometry().bottomRight()
        qr.moveBottomRight(cp)
        self.move(qr.topLeft() - QPoint(42, 3))

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

    def closeEvent(self, event):
        """Redefine close event."""
        self.hide()
        event.ignore()


class TrayIcon(QSystemTrayIcon):
    """Tray Icon을 생성한다."""

    def __init__(self, app, window):
        """Init."""
        super().__init__()

        self.app = app
        self.window = window

        icon = QIcon()
        icon.addPixmap(QPixmap("timer.ico"), QIcon.Normal, QIcon.Off)
        self.setIcon(icon)
        self.window.show()

        self.menu = QMenu()
        act_show = QAction("show", self)
        act_show.triggered.connect(self.window.show)

        act_hide = QAction("hide", self)
        act_hide.triggered.connect(self.window.hide)

        act_quit = QAction("quit", self)
        act_quit.triggered.connect(self.app.quit)

        self.menu.addAction(act_show)
        self.menu.addAction(act_hide)
        self.menu.addAction(act_quit)

        self.setContextMenu(self.menu)

        self.activated.connect(self.onTrayIconActivated)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def onTrayIconActivated(self, reason):
        """Tray icon 클릭 시 동작을 정의한다."""
        if reason == QSystemTrayIcon.Trigger:
            if self.window.isHidden():
                self.window.show()
            else:
                self.window.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = TransparentWindow()
    tray = TrayIcon(app, window)
    tray.setVisible(True)

    sys.exit(app.exec_())
