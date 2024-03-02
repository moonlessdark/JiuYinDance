import ctypes
import sys

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


class MainGui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setFixedSize(280, 400)
        self.setWindowTitle("蜗牛跳舞小助手")
        # 加载任务栏和窗口左上角图标
        self.setWindowIcon(QIcon("./_internal/Resources/logo/logo.ico"))
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
        """
        底部状态栏显示区域
        """
        self.status_bar_print = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar_print)
        self.status_bar_print.showMessage(" 等待执行")

        """
        日志打印区      
        """
        self.text_browser_print_log = QtWidgets.QTextBrowser(self)
        self.text_browser_print_log.setGeometry(QtCore.QRect(10, 190, 260, 188))

        """
        选择类型
        """
        self.group_box_functional_area = QtWidgets.QGroupBox(self)  # 功能区
        self.group_box_functional_area.setGeometry(QtCore.QRect(10, 5, 260, 60))
        self.group_box_functional_area.setTitle("选择功能")

        self.radio_button_school_dance = QtWidgets.QRadioButton()
        self.radio_button_school_dance.setText("团练授业")
        # 隐士/势力/修罗刀
        self.radio_button_party_dance = QtWidgets.QRadioButton()
        self.radio_button_party_dance.setText("隐士势力")
        # 游戏截图
        self.radio_button_game_screen = QtWidgets.QRadioButton()
        self.radio_button_game_screen.setText("游戏截图")
        # 按键宏
        self.radio_button_key_auto = QtWidgets.QRadioButton()
        self.radio_button_key_auto.setText("键鼠宏")

        """
        增加一下布局框
        """
        # 一个网格布局
        self.gridLayout_group_box_functional_area = QtWidgets.QGridLayout(self.group_box_functional_area)
        self.gridLayout_group_box_functional_area.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_school_dance, 0, 0, QtCore.Qt.AlignRight)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_party_dance, 0, 1, QtCore.Qt.AlignCenter)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_game_screen, 0, 2, QtCore.Qt.AlignCenter)
        # self.gridLayout_group_box_functional_area.addWidget(self.radio_button_key_auto, 1, 1, QtCore.Qt.AlignCenter)

        self.setLayout(self.gridLayout_group_box_functional_area)

        """
        选择游戏窗口与执行
        """
        self.group_box_get_windows = QtWidgets.QGroupBox(self)
        self.group_box_get_windows.setGeometry(QtCore.QRect(10, 70, 260, 70))
        self.group_box_get_windows.setTitle("选择游戏窗口")

        # 获取窗口按钮
        self.push_button_get_windows_handle = QtWidgets.QPushButton()
        self.push_button_get_windows_handle.setText("获取窗口")
        # 测试窗口
        self.push_button_test_windows = QtWidgets.QPushButton(self.group_box_get_windows)
        self.push_button_test_windows.setText("测试窗口")
        self.push_button_test_windows.setEnabled(False)
        # 开始执行/停止执行
        self.push_button_start_or_stop_execute = QtWidgets.QPushButton(self.group_box_get_windows)
        self.push_button_start_or_stop_execute.setText("开始执行")
        self.push_button_start_or_stop_execute.setEnabled(False)

        # 加载一个横向的布局
        self.layout_group_box_get_windows = QtWidgets.QHBoxLayout(self.group_box_get_windows)
        self.layout_group_box_get_windows.addWidget(self.push_button_get_windows_handle)
        self.layout_group_box_get_windows.addWidget(self.push_button_test_windows)
        self.layout_group_box_get_windows.addWidget(self.push_button_start_or_stop_execute)

        self.setLayout(self.layout_group_box_get_windows)

        # 获取到的游戏窗口要如何加载
        self.group_box_select_windows = QtWidgets.QGroupBox(self)
        self.group_box_select_windows.setGeometry(QtCore.QRect(10, 140, 260, 40))

        # 窗口A/B/C
        self.check_box_windows_one = QtWidgets.QCheckBox()
        self.check_box_windows_two = QtWidgets.QCheckBox()
        self.check_box_windows_three = QtWidgets.QCheckBox()

        self.check_box_windows_one.setText("窗口1")
        self.check_box_windows_two.setText("窗口2")
        self.check_box_windows_three.setText("窗口3")
        self.check_box_windows_one.setEnabled(False)
        self.check_box_windows_two.setEnabled(False)
        self.check_box_windows_three.setEnabled(False)

        # 加载一个横向的布局
        self.layout_group_box_select_windows = QtWidgets.QHBoxLayout(self.group_box_select_windows)
        self.layout_group_box_select_windows.addStretch(1)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_one)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_two)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_three)
        self.layout_group_box_select_windows.addStretch(1)
        self.setLayout(self.layout_group_box_select_windows)

    def set_ui_load_windows_check_box_init(self):
        """
        选择按钮初始化，全部禁用
        :return:
        """
        self.check_box_windows_one.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.check_box_windows_one.setEnabled(False)
        self.check_box_windows_two.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.check_box_windows_two.setEnabled(False)
        self.check_box_windows_three.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.check_box_windows_three.setEnabled(False)

    def set_ui_load_windows_check_box_by_single(self):
        """
        只能选择一个窗口，用在游戏截图这个功能
        :return:
        """
        if self.check_box_windows_one.isChecked():
            self.check_box_windows_two.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_two.setEnabled(False)
            self.check_box_windows_three.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_three.setEnabled(False)
        elif self.check_box_windows_two.isChecked():
            self.check_box_windows_one.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_one.setEnabled(False)
            self.check_box_windows_three.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_three.setEnabled(False)
        elif self.check_box_windows_three.isChecked():
            self.check_box_windows_one.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_one.setEnabled(False)
            self.check_box_windows_two.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.check_box_windows_two.setEnabled(False)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_gui = MainGui()
    main_gui.show()
    sys.exit(app.exec_())
