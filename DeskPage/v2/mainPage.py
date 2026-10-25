# coding: utf-8
"""
v2 主窗口。

负责组装任务页、窗口选择、日志、状态栏和菜单栏。
"""
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication

from Core.config.paths import PathUtil
from DeskPage.v2.fuctionPage import TaskFunc
from DeskPage.v2.menuPage import MenuUI
from DeskPage.v2.statusBar import StatusBarProcess
from DeskPage.v2.windowsMonitorPage import WindowsButton


class MainUI(QtWidgets.QMainWindow):
    """主界面。"""

    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 450)
        self.setWindowIcon(QtGui.QIcon(
            PathUtil().get_root_path() + "Resources/logo/logo.ico"))

        self.__print_logs = QtWidgets.QTextBrowser()
        self.task_tab_windows = TaskFunc()
        self.windows_get = WindowsButton()

        main_widget = QtWidgets.QWidget(self)
        main_widget.resize(self.width(), self.height())

        layout_main = QtWidgets.QVBoxLayout(main_widget)
        layout_main.setSpacing(2)
        layout_main.addWidget(self.task_tab_windows)
        layout_main.addWidget(self.windows_get)
        layout_main.addWidget(self.__print_logs)
        layout_main.setContentsMargins(10, 30, 10, 25)

        self.task_tab_windows.setMinimumHeight(120)

        self.status_bar = StatusBarProcess()
        self.setStatusBar(self.status_bar)

        self.setMenuBar(MenuUI())

    def log_print(self, text: str):
        """追加一条带时间的日志。"""
        current_time = QtCore.QTime.currentTime().toString('HH:mm:ss')
        self.__print_logs.append(f"{current_time} : {text}")

    def log_clear(self):
        """清空日志。"""
        self.__print_logs.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainUI()
    window.show()
    app.exec()
