"""Transparent timer."""
# Standard library imports
import sys
import sqlite3
import argparse
from datetime import datetime
from typing import Literal

# Third party imports
import qdarkstyle
from PyQt5.QtCore import QPoint, Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QMenu,
    QProgressBar,
    QSystemTrayIcon,
    QMessageBox,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QLCDNumber,
)

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

TIMER_TYPE = Literal["LongRest", "ShortRest", "Work"]


class TimerProgressBar(QProgressBar):
    """Progressbar for Timer."""

    sig_timer_end = pyqtSignal()

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

    def set_tooltip(self):
        """Set tooltip."""
        diff  = max(self.timer_req - self.timer_cur, 0)
        self.setToolTip(f"RemainTime: {diff // 60}min {diff % 60}sec")

    def add_sec(self, val: int):
        """Add second.

        Args:
            val: Second
        """
        if self.timer_cur < self.timer_req:
            self.timer_cur += val
            self.setValue(self.timer_cur)
            if self.timer_cur == self.timer_req:
                self.sig_timer_end.emit()
        self.set_tooltip()


class WorkDoneMessage(QMessageBox):
    """."""

    def __init__(
        self, title: str, text: str, btn_infos: dict[str, QMessageBox.ButtonRole]
    ):
        """."""
        super().__init__()
        self.setWindowTitle(title)
        self.setText(text)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setIcon(QMessageBox.Question)
        for txt, role in btn_infos.items():
            self.addButton(QPushButton(txt), role)

    def get_role_clicked(self) -> QMessageBox.ButtonRole:
        """Get the role of button clicked."""
        role_clicked = self.buttonRole(self.clickedButton())
        return role_clicked


class TransparentWindow(QMainWindow):
    """Transparent window."""

    def __init__(self, path_db: str):
        """."""
        super().__init__()

        # Setup dB
        self.path_db = path_db
        self.open_db()
        self.work_info: tuple[str, str] = ("", "")
        self.n_work: int = self.read_n_work_today()

        # <MainWindow Properties>
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.move_window()
        self.setWindowOpacity(0.3)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        # </MainWindow Properties>
        self.progress_bar = TimerProgressBar(self)
        self.progress_bar.sig_timer_end.connect(self.handle_timer_end_event)
        self.lcd = QLCDNumber(self)
        self.lcd.setDigitCount(2)
        self.lcd.display(self.n_work)

        self.setFixedSize(133, 30)
        self.progress_bar.setFixedSize(100, 30)
        self.lcd.setFixedSize(30, 30)

        # Layout
        widget = QWidget(self)
        widget.setContentsMargins(0, 0, 0, 0)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 3, 0)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.lcd)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # For save position for mouseMoveEvent
        self.old_pos = self.pos()

        self.timer_type: TIMER_TYPE = "ShortRest"
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(lambda: self.progress_bar.add_sec(1))
        self.timer.start()

    def open_db(self):
        """Create DB."""
        conn = sqlite3.connect(self.path_db)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS WorkingHistory(Date text,Time text);")
        cur.close()
        conn.commit()
        conn.close()

    def read_n_work_today(self) -> int:
        """Read the number of work today."""
        conn = sqlite3.connect(self.path_db)
        cur = conn.cursor()

        date = str(datetime.today().date())
        cur.execute(f"SELECT * FROM WorkingHistory WHERE Date='{date}'")
        rows = cur.fetchall()
        ret = len(rows)

        cur.close()
        conn.commit()
        conn.close()

        return ret

    def insert_workhistory(self):
        """Insert workhistory."""
        conn = sqlite3.connect(self.path_db)
        cur = conn.cursor()
        cur.execute("INSERT INTO WorkingHistory(Date,Time)VALUES(?,?);", self.work_info)
        cur.close()
        conn.commit()
        conn.close()

        # Update GUI
        self.n_work += 1

    def move_window(self):
        """Move main window to top left."""
        qr = self.frameGeometry()
        screen = QGuiApplication.primaryScreen()
        cp = screen.availableGeometry().bottomRight()
        qr.moveBottomRight(cp)
        # self.move(qr.topLeft() - QPoint(42, 3))
        self.move(QPoint(qr.left() - 1921, qr.bottom()))

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
                self.set_timer("LongRest")
        else:
            if key == Qt.Key_W:
                self.set_timer("Work")
            elif key == Qt.Key_R:
                self.set_timer("ShortRest")

    def set_timer(self, timer_type: TIMER_TYPE):
        """Set timer."""
        self.timer_type = timer_type
        if timer_type == "LongRest":
            self.progress_bar.set_timer(15)
        elif timer_type == "ShortRest":
            self.progress_bar.set_timer(5)
        elif timer_type == "Work":
            self.work_info = (
                str(datetime.today().date()),
                str(datetime.today().time()),
            )
            self.progress_bar.set_timer(25)

        self.lcd.display(self.n_work)

    def closeEvent(self, event):
        """Redefine close event."""
        self.hide()
        event.ignore()

    def handle_timer_end_event(self):
        """Handle timer end event."""
        self.progress_bar.setStyleSheet(
            "QProgressBar {color: green;}"
            "QProgressBar::chunk {background-color: red;}"
        )
        if self.timer_type == "Work":
            msgbox = WorkDoneMessage(
                "업무 완료",
                "업무 집중이 끝났습니다.",
                {
                    "휴식": QMessageBox.ApplyRole,
                    "새로운 업무": QMessageBox.AcceptRole,
                    "업무 재시작": QMessageBox.NoRole,
                },
            )
            msgbox.exec()
            role_clicked = msgbox.get_role_clicked()
            if role_clicked == QMessageBox.ApplyRole:
                self.insert_workhistory()
                self.set_timer("ShortRest")
            elif role_clicked == QMessageBox.AcceptRole:
                self.insert_workhistory()
                self.set_timer("Work")
            elif role_clicked == QMessageBox.NoRole:
                self.set_timer("Work")
        else:
            msgbox = WorkDoneMessage(
                "휴식 완료",
                "휴식이 끝났습니다.",
                {
                    "업무 집중": QMessageBox.AcceptRole,
                    "휴식 재시작": QMessageBox.NoRole,
                },
            )
            msgbox.exec()
            role_clicked = msgbox.get_role_clicked()
            if role_clicked == QMessageBox.AcceptRole:
                self.set_timer("Work")
            elif role_clicked == QMessageBox.NoRole:
                self.set_timer("ShortRest")

        self.progress_bar.setStyleSheet("")


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


def parse_arguments() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(description="Transparent Timer like Pomodoro")
    parser.add_argument(
        "--path_db",
        help="Path of dB of working history",
        type=str,
        default="workhistory.db",
    )
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_arguments()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = TransparentWindow(args.path_db)
    tray = TrayIcon(app, window)
    tray.setVisible(True)

    sys.exit(app.exec_())
