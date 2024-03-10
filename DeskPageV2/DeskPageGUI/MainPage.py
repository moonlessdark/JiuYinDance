import ctypes
import os
import sys
import time
import winreg

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


class MainGui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setFixedSize(280, 420)
        # self.setWindowTitle("蜗牛跳舞小助手")
        # 加载任务栏和窗口左上角图标
        self.setWindowIcon(QIcon("./_internal/Resources/logo/logo.ico"))
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

        """
        顶部菜单栏
        """
        menu_bar = self.menuBar()

        file_menu = QtWidgets.QMenu("&配置", self)
        about_menu = QtWidgets.QMenu("&帮助", self)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(about_menu)

        action_open_config_file = QtGui.QAction("打开配置文件", self)
        file_menu.addAction(action_open_config_file)
        action_open_config_file.triggered.connect(self.open_config_file)

        action_open_url = QtGui.QAction("访问项目github", self)
        about_menu.addAction(action_open_url)
        action_open_url.triggered.connect(self.open_url_project)

        action_open_url_get_fore_ground_window_fail = QtGui.QAction("修复窗户激活失败", self)
        about_menu.addAction(action_open_url_get_fore_ground_window_fail)
        action_open_url_get_fore_ground_window_fail.triggered.connect(self.open_url_get_fore_ground_window_fail)

        """
        底部状态栏显示区域
        """
        self.status_bar_print = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar_print)

        # 左侧区域
        # 给状态栏显示文字用的
        self.status_bar_label_left = QtWidgets.QLabel()
        # 状态栏本身显示的信息 第二个参数是信息停留的时间，单位是毫秒，默认是0（0表示在下一个操作来临前一直显示）
        # 在状态栏左侧新增显示控件
        self.status_bar_print.addWidget(self.status_bar_label_left, stretch=1)
        # 加载一个进度条
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setInvertedAppearance(False)  # 进度条的走向
        self.progress_bar.setOrientation(QtCore.Qt.Orientation.Horizontal)  # 进度条的方向
        # 出现跑马灯的效果
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_bar_print.addWidget(self.progress_bar, stretch=3)

        # 右侧区域
        self.status_bar_label_right = QtWidgets.QLabel()
        self.status_bar_label_right.setText("一共识别了 0 轮")
        self.status_bar_label_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_bar_print.addWidget(self.status_bar_label_right, stretch=1)

        self.status_bar_print.setContentsMargins(8, 0, 0, 0)

        """
        日志打印区      
        """
        self.text_browser_print_log = QtWidgets.QTextBrowser(self)
        self.text_browser_print_log.setGeometry(QtCore.QRect(10, 210, 260, 188))

        """
        选择类型
        """
        self.group_box_functional_area = QtWidgets.QGroupBox(self)  # 功能区
        self.group_box_functional_area.setGeometry(QtCore.QRect(10, 30, 260, 60))
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
        self.group_box_get_windows.setGeometry(QtCore.QRect(10, 90, 260, 70))
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
        self.group_box_select_windows.setGeometry(QtCore.QRect(10, 160, 260, 40))

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

    def open_config_file(self):
        """
        打开配置文件
        :return:
        """
        config_file: str = '.\\_internal\\Resources\\'
        if not os.path.exists(config_file):  # 如果主目录+小时+分钟这个文件路径不存在的话
            config_file = ".\\DeskPageV2\\Resources\\"
        QtWidgets.QFileDialog.getOpenFileName(self, "资源文件", config_file,
                                              "Text Files (*.yaml;*.bat;*.png;*.ico;*.dll)")

    @staticmethod
    def open_url_get_fore_ground_window_fail(self):
        """
        激活窗口失败
        :param self:
        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://blog.csdn.net/qq_26013403/article/details/129122971"))

    @staticmethod
    def open_url_project():
        """
        打开网页
        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/moonlessdark/JiuYinDance"))

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
