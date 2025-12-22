import sys

from PySide6.QtWidgets import QApplication

from DeskPage.fuctionPage import TaskFunc
from DeskPage.menuPage import MenuUI
from DeskPage.statusBar import StatusBarProcess
from DeskPage.windowsMonitorPage import WindowsButton
from PySide6 import QtWidgets, QtCore, QtGui


class MainUI(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setFixedSize(300, 450)

        self.setWindowIcon(QtGui.QIcon("./_internal/Resources/logo/logo.ico"))
        # self.setWindowIcon(QtGui.QIcon("D:\\SoftWare\\Developed\\Projected\\JiuYinDnaceRemake\\Resources\\ImageTemplate\\PicDance\\pic_dance_K.png"))

        self.__print_logs = QtWidgets.QTextBrowser()

        self.task_tab_windows = TaskFunc()

        self.windows_get = WindowsButton()

        _main_widget = QtWidgets.QWidget(self)
        _main_widget.resize(self.width(), self.height())

        _lay_out_main = QtWidgets.QVBoxLayout(_main_widget)
        _lay_out_main.setSpacing(2)
        _lay_out_main.addWidget(self.task_tab_windows)
        _lay_out_main.addWidget(self.windows_get)
        _lay_out_main.addWidget(self.__print_logs)

        _lay_out_main.setContentsMargins(10, 30, 10, 25)

        # 让任务栏的高度大一些，不然任务放不下
        self.task_tab_windows.setMinimumHeight(120)  # 示例值，可根据需要调整

        self.status_bar = StatusBarProcess()
        self.setStatusBar(self.status_bar)

        # 顶部菜单栏
        menu_bar = MenuUI()
        self.setMenuBar(menu_bar)

    def log_print(self, text: str):
        """
        日志打印
        :param text:
        :return:
        """
        __time: str = QtCore.QTime.currentTime().toString('HH:mm:ss')
        self.__print_logs.append(f"{__time} : {text}")

    def log_clear(self):
        """
        清理日志
        :return:
        """
        self.__print_logs.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainUI()
    w.show()
    app.exec()
