import ctypes
import os
import sys
import time

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QIcon, QIntValidator, QFont
from PySide6.QtWidgets import QApplication, QListWidget, QHeaderView

from DeskPageV2.DeskPageGUI.MarkdownViewer import MarkdownViewer


class ListWidgetItemEventFilter(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.list_widget: QListWidget = parent
        self.event_key_str_list: list = []  # 本次所有按下的按键
        self.event_key_sum: int = 0  # 按下的组合键数量

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            """
            如果是按钮按下
            """
            key_text = event.text()
            if event.modifiers():
                key_text = event.keyCombination().key().name.decode(encoding="utf-8")
            if key_text not in self.event_key_str_list:
                """
                如果本次按下的键是没有被按过的，就加入队列
                """
                self.event_key_str_list.append(key_text)
                self.event_key_sum += 1
                # print(f"键盘按下了 {key_text} {event.key()} 当前按钮数量{self.event_key_sum}")

        elif event.type() == QEvent.KeyRelease:
            """
            如果是按钮弹起
            """
            self.event_key_sum -= 1
            # print(f"键盘松开了一个键_当前按钮数量{self.event_key_sum}")
            if self.event_key_sum == 0:
                """
                如果所有的按钮都弹起了，那么就说明已经输入完毕
                """
                if self.list_widget.selectedItems():
                    item = self.list_widget.selectedItems()[0]
                    event_key_str = "+".join(self.event_key_str_list)
                    item.setText(event_key_str.upper())
                    self.event_key_str_list = []
            elif self.event_key_sum < 0:
                self.event_key_sum = 0
        return super().eventFilter(watched, event)


class MainGui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.resize(300, 460)
        self.setFixedWidth(300)
        # self.setWindowTitle("蜗牛跳舞小助手")
        # 加载任务栏和窗口左上角图标
        self.setWindowIcon(QIcon("./_internal/Resources/logo/logo.ico"))
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("my_app_id")

        """
        加载事件筛选器
        """
        self.list_widget = QtWidgets.QListWidget()
        event_filter = ListWidgetItemEventFilter(self.list_widget)
        self.list_widget.installEventFilter(event_filter)

        self.__new_windows = None

        """
        顶部菜单栏
        """
        menu_bar = self.menuBar()

        file_menu = QtWidgets.QMenu("&配置", self)
        about_menu = QtWidgets.QMenu("&帮助", self)

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(about_menu)

        action_open_config_file = QtGui.QAction("资源目录", self)
        file_menu.addAction(action_open_config_file)
        action_open_config_file.triggered.connect(self.open_config_file)

        action_edit_config_file = QtGui.QAction("修改配置", self)
        file_menu.addAction(action_edit_config_file)
        action_edit_config_file.triggered.connect(self.edit_config_file)

        self.action_edit_skill_list = QtGui.QAction("编辑技能", self)
        file_menu.addAction(self.action_edit_skill_list)

        action_open_url = QtGui.QAction("访问项目", self)
        about_menu.addAction(action_open_url)
        action_open_url.triggered.connect(self.open_url_project)

        action_open_url_get_fore_ground_window_fail = QtGui.QAction("修复窗口激活失败", self)
        about_menu.addAction(action_open_url_get_fore_ground_window_fail)
        action_open_url_get_fore_ground_window_fail.triggered.connect(self.open_url_get_fore_ground_window_fail)

        action_func_detail = QtGui.QAction("功能说明", self)
        about_menu.addAction(action_func_detail)
        action_func_detail.triggered.connect(self.open_func_detail_widget)

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

        # 主界面容器，所有控件都在这里面
        self.widget_main = QtWidgets.QWidget()
        self.setCentralWidget(self.widget_main)

        __widget_width: int = 280  # 容器的宽

        """
        选择类型
        """
        self.group_box_functional_area = QtWidgets.QGroupBox()  # 功能区
        self.group_box_functional_area.setTitle("选择功能")

        _label_day_task = QtWidgets.QLabel("每日任务")
        _label_desert_task = QtWidgets.QLabel("漠西风涛")
        _label_other_task = QtWidgets.QLabel("其他")

        self.radio_button_school_dance = QtWidgets.QRadioButton()
        self.radio_button_school_dance.setText("团练授业")
        # 隐士/势力/修罗刀
        self.radio_button_party_dance = QtWidgets.QRadioButton()
        self.radio_button_party_dance.setText("势力修炼")
        # 游戏截图
        self.radio_button_game_screen = QtWidgets.QRadioButton()
        self.radio_button_game_screen.setText("游戏截图")
        # 按键宏
        self.radio_button_key_auto = QtWidgets.QRadioButton()
        self.radio_button_key_auto.setText("键盘连按")
        # 押镖
        self.radio_button_truck_car_task = QtWidgets.QRadioButton()
        self.radio_button_truck_car_task.setText("押镖任务")
        # 世界竞拍
        self.radio_button_auction_market = QtWidgets.QRadioButton()
        self.radio_button_auction_market.setText("世界竞拍")
        # 成语填空
        self.radio_button_chengyu_input = QtWidgets.QRadioButton()
        self.radio_button_chengyu_input.setText("成语填空")
        self.radio_button_chengyu_input.setVisible(False)
        # 成语填空
        self.radio_button_chengyu_search = QtWidgets.QRadioButton()
        self.radio_button_chengyu_search.setText("成语搜索")

        """
        增加一下布局框
        """
        # 一个网格布局
        self.gridLayout_group_box_functional_area = QtWidgets.QGridLayout()
        self.gridLayout_group_box_functional_area.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_group_box_functional_area.setSpacing(1)
        self.gridLayout_group_box_functional_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 每日任务
        self.gridLayout_group_box_functional_area.addWidget(_label_day_task, 0, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_school_dance, 1, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_party_dance, 1, 1)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_truck_car_task, 1, 2)

        # 漠西风涛
        self.gridLayout_group_box_functional_area.addWidget(_label_desert_task, 2, 0)
        # self.gridLayout_group_box_functional_area.addWidget(self.radio_button_chengyu_input, 3, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_chengyu_search, 3, 0)

        # 其他工具
        self.gridLayout_group_box_functional_area.addWidget(_label_other_task, 4, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_key_auto, 5, 0)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_auction_market, 5, 1)
        self.gridLayout_group_box_functional_area.addWidget(self.radio_button_game_screen, 5, 2)

        # 将布局放入容器中
        self.group_box_functional_area.setLayout(self.gridLayout_group_box_functional_area)

        """
        选择游戏窗口与执行
        """
        self.group_box_get_windows = QtWidgets.QGroupBox()
        self.group_box_get_windows.setTitle("选择游戏窗口")

        # 获取窗口按钮
        self.push_button_get_windows_handle = QtWidgets.QPushButton()
        self.push_button_get_windows_handle.setText("获取窗口")
        self.push_button_get_windows_handle.setFixedHeight(30)
        # 测试窗口
        self.push_button_test_windows = QtWidgets.QPushButton()
        self.push_button_test_windows.setText("测试窗口")
        self.push_button_test_windows.setEnabled(False)
        self.push_button_test_windows.setFixedHeight(30)
        # 开始执行/停止执行
        self.push_button_start_or_stop_execute = QtWidgets.QPushButton()
        self.push_button_start_or_stop_execute.setText("开始执行")
        self.push_button_start_or_stop_execute.setEnabled(False)
        self.push_button_start_or_stop_execute.setFixedHeight(30)

        # 加载一个横向的布局
        self.layout_group_box_get_windows = QtWidgets.QHBoxLayout(self.group_box_get_windows)
        self.layout_group_box_get_windows.addWidget(self.push_button_get_windows_handle)
        self.layout_group_box_get_windows.addWidget(self.push_button_test_windows)
        self.layout_group_box_get_windows.addWidget(self.push_button_start_or_stop_execute)

        # 获取到的游戏窗口要如何加载
        self.group_box_select_windows = QtWidgets.QGroupBox()

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
        self.layout_group_box_select_windows.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_one)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_two)
        self.layout_group_box_select_windows.addWidget(self.check_box_windows_three)

        """
        日志打印区      
        """
        self.text_browser_print_log = QtWidgets.QTextBrowser()

        """
        将主界面进行布局加载
        """
        _lay_out_main_page = QtWidgets.QVBoxLayout()
        _lay_out_main_page.addWidget(self.group_box_functional_area)
        _lay_out_main_page.addWidget(self.group_box_get_windows)
        _lay_out_main_page.addWidget(self.group_box_select_windows)
        _lay_out_main_page.addWidget(self.text_browser_print_log)
        _lay_out_main_page.setSpacing(1)

        self.widget_main.setLayout(_lay_out_main_page)

        """
        以下是一些弹出窗口的界面UI
        """

        """
        按键连按
        """
        widget_key_press_auto = QtWidgets.QWidget()
        # 最大随机等待事件
        self.line_key_press_wait_time = QtWidgets.QDoubleSpinBox(widget_key_press_auto)
        self.line_key_press_wait_time.setValue(1.5)  # 双精度
        self.line_key_press_wait_time.setRange(0.5, 99)  # 双精度
        self.line_key_press_wait_time.setSuffix("秒")  # 单位

        self.line_key_press_execute_sum = QtWidgets.QSpinBox(widget_key_press_auto)
        self.line_key_press_execute_sum.setValue(10)
        self.line_key_press_execute_sum.setRange(1, 999999)
        self.line_key_press_execute_sum.setSuffix("次")

        lay_out_input = QtWidgets.QHBoxLayout()
        lay_out_input.addWidget(self.line_key_press_execute_sum)
        lay_out_input.addWidget(self.line_key_press_wait_time)

        self.push_button_save_key_press_add = QtWidgets.QPushButton("新增", widget_key_press_auto)
        self.push_button_save_key_press_delete = QtWidgets.QPushButton("删除", widget_key_press_auto)
        self.push_button_save_key_press_save = QtWidgets.QPushButton("保存", widget_key_press_auto)

        layout_input = QtWidgets.QGridLayout(widget_key_press_auto)
        layout_input.addLayout(lay_out_input, 0, 0, 1, 1)
        layout_input.addWidget(self.list_widget, 1, 0, 3, 1)
        layout_input.addWidget(self.push_button_save_key_press_add, 1, 1)
        layout_input.addWidget(self.push_button_save_key_press_delete, 2, 1)
        layout_input.addWidget(self.push_button_save_key_press_save, 3, 1)
        layout_input.setAlignment(QtCore.Qt.AlignHCenter)

        self.widget_dock = QtWidgets.QDockWidget("键盘按钮设置", self)
        self.widget_dock.setWidget(widget_key_press_auto)
        self.widget_dock.setFloating(True)  # 独立于主窗口之外
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.widget_dock)
        self.widget_dock.setVisible(False)
        self.widget_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable)  # dockWidget窗口禁止回到主窗口，且屏蔽关闭按钮

        """
        设置世界竞拍的最高价格
        """
        widget_market = QtWidgets.QWidget()

        self.list_widget_market = QtWidgets.QTableWidget(widget_market)
        self.list_widget_market.resizeColumnsToContents()  # 自适应列宽

        header = self.list_widget_market.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.push_button_market_get_goods_list = QtWidgets.QPushButton("获取物品")

        layout_input = QtWidgets.QGridLayout(widget_market)
        layout_input.addWidget(self.list_widget_market, 0, 0, 10, 1)
        layout_input.addWidget(self.push_button_market_get_goods_list, 0, 1)
        layout_input.setAlignment(QtCore.Qt.AlignHCenter)

        self.widget_dock_market = QtWidgets.QDockWidget("设置竞拍物品", self)
        self.widget_dock_market.setFixedHeight(230)
        self.widget_dock_market.setWidget(widget_market)
        self.widget_dock_market.setFloating(True)  # 独立于主窗口之外
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.widget_dock_market)
        self.widget_dock_market.setVisible(False)
        self.widget_dock_market.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable)  # dockWidget窗口禁止回到主窗口，且屏蔽关闭按钮

        """
        设置配置文件窗口
        """
        widget_setting = QtWidgets.QWidget()
        self.label_dance_threshold = QtWidgets.QLabel("团练授业阈值", widget_setting)
        self.line_dance_threshold = QtWidgets.QDoubleSpinBox(widget_setting)
        self.line_dance_threshold.setToolTip("最低匹配阈值，影响团练授业")
        self.line_dance_threshold.setRange(0.01, 1.00)

        self.label_whz_dance_threshold = QtWidgets.QLabel("势力修炼阈值", widget_setting)
        self.line_whz_dance_threshold = QtWidgets.QDoubleSpinBox(widget_setting)
        self.line_whz_dance_threshold.setToolTip("最低匹配阈值，影响挖宝的修罗刀、天涯海阁的瀑布修炼和钓鱼、望辉洲的跳舞")
        self.line_whz_dance_threshold.setRange(0.01, 1.00)

        self.label_area_dance_threshold = QtWidgets.QLabel("按钮区域阈值", widget_setting)
        self.line_area_dance_threshold = QtWidgets.QDoubleSpinBox(widget_setting)
        self.line_area_dance_threshold.setToolTip("最低匹配阈值，影响按钮区域的识别率，越低越好。")
        self.line_area_dance_threshold.setRange(0.01, 1.00)

        self.label_max_truck_car_sum = QtWidgets.QLabel("押镖次数设置", widget_setting)
        self.line_max_truck_car_sum = QtWidgets.QSpinBox(widget_setting)
        self.line_max_truck_car_sum.setToolTip("押镖最大次数,4L碎银一次，最多80次")
        self.line_max_truck_car_sum.setRange(1, 80)

        self.check_debug_mode = QtWidgets.QCheckBox("Debug", widget_setting)
        self.push_button_save_setting = QtWidgets.QPushButton("保存设置", widget_setting)

        layout_setting = QtWidgets.QGridLayout(widget_setting)
        layout_setting.addWidget(self.label_dance_threshold, 0, 0)
        layout_setting.addWidget(self.line_dance_threshold, 0, 1)
        layout_setting.addWidget(self.label_whz_dance_threshold, 1, 0)
        layout_setting.addWidget(self.line_whz_dance_threshold, 1, 1)
        layout_setting.addWidget(self.label_area_dance_threshold, 2, 0)
        layout_setting.addWidget(self.line_area_dance_threshold, 2, 1)
        layout_setting.addWidget(self.label_max_truck_car_sum, 3, 0)
        layout_setting.addWidget(self.line_max_truck_car_sum, 3, 1)
        layout_setting.addWidget(self.check_debug_mode, 4, 0)
        layout_setting.addWidget(self.push_button_save_setting, 4, 1)

        self.widget_dock_setting = QtWidgets.QDockWidget("配置信息", self)
        self.widget_dock_setting.setWidget(widget_setting)
        self.widget_dock_setting.setFloating(True)  # 独立于主窗口之外
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.widget_dock_setting)
        self.widget_dock_setting.setVisible(False)
        self.widget_dock_setting.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable)  # dockWidget窗口禁止回到主窗口

        """
        配置打怪技能
        """
        self.dialog_skill_table = QtWidgets.QDialog()
        self.dialog_skill_table.setWindowTitle("设置技能")
        self.dialog_skill_table.resize(530, 300)
        self._skill_table = QtWidgets.QTableWidget(self.dialog_skill_table)
        self._skill_table.setRowCount(1)
        self._skill_table.setColumnCount(5)
        __widget = QtWidgets.QWidget()
        self._button_add_skill_table_row = QtWidgets.QPushButton("新增")
        self._button_del_skill_table_row = QtWidgets.QPushButton("删除")
        self._button_save_skill_table = QtWidgets.QPushButton("保存")

        __lay_table_ui_button = QtWidgets.QHBoxLayout(__widget)
        __lay_table_ui_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        __lay_table_ui_button.addWidget(self._button_add_skill_table_row)
        __lay_table_ui_button.addWidget(self._button_del_skill_table_row)
        __lay_table_ui_button.addWidget(self._button_save_skill_table)
        __lay_table_ui_button.setSpacing(1)

        __lay_table_ui = QtWidgets.QVBoxLayout(self.dialog_skill_table)
        __lay_table_ui.addWidget(__widget)
        __lay_table_ui.addWidget(self._skill_table)
        __lay_table_ui.setSpacing(2)
        __lay_table_ui.setContentsMargins(5, 5, 5, 5)

        self._button_add_skill_table_row.clicked.connect(self.add_skill_table_row)
        self._button_del_skill_table_row.clicked.connect(self.del_skill_table_row)

        """
        成语搜索
        """
        self.dialog_chengyu_search = QtWidgets.QDialog()
        self.dialog_chengyu_search.setWindowTitle("成语搜索")
        self.dialog_chengyu_search.resize(460, 650)
        self.dialog_chengyu_search.setFixedWidth(460)

        self.table_chengyu_screen = QtWidgets.QTableWidget()  # 查询游戏页面上的文字
        self.table_chengyu_screen.setFixedHeight(300)

        self.push_button_chengyu_get_pic_text = QtWidgets.QPushButton("获取文字")
        self.push_button_chengyu_search = QtWidgets.QPushButton("搜索成语")

        self.push_button_chengyu_search.setToolTip("输入关键字模糊查询成语,每个输入框只能输入一个文字")

        _label_get_chengyu_pic = QtWidgets.QLabel("请根据游戏画面中的文字补充完整")
        _label_search_result_chengyu = QtWidgets.QLabel("查询结果如下")

        self.push_button_chengyu_input_add_row = QtWidgets.QPushButton('插入新一行')
        self.push_button_chengyu_input_add_row.setFixedWidth(100)

        _lay_out_chengyu_search_input = QtWidgets.QHBoxLayout()
        _lay_out_chengyu_search_input.setSpacing(2)
        _lay_out_chengyu_search_input.setAlignment(QtCore.Qt.AlignCenter)
        _lay_out_chengyu_search_input.addWidget(self.push_button_chengyu_get_pic_text)
        _lay_out_chengyu_search_input.addWidget(self.push_button_chengyu_search)

        _lay_out_chengyu_search_input_tips = QtWidgets.QHBoxLayout()
        _lay_out_chengyu_search_input_tips.addWidget(_label_get_chengyu_pic, QtCore.Qt.AlignLeft)
        _lay_out_chengyu_search_input_tips.addWidget(self.push_button_chengyu_input_add_row, QtCore.Qt.AlignRight)

        # 将获取页面的布局准备好
        _lay_out_chengyu_get_search = QtWidgets.QVBoxLayout()
        _lay_out_chengyu_get_search.addLayout(_lay_out_chengyu_search_input)
        _lay_out_chengyu_get_search.addLayout(_lay_out_chengyu_search_input_tips)
        _lay_out_chengyu_get_search.addWidget(self.table_chengyu_screen)

        self.table_chengyu_search = QtWidgets.QTableWidget()  # 查询结果表格

        # 将查询结果的布局准备好
        _lay_out_chengyu_search_result = QtWidgets.QVBoxLayout()
        _lay_out_chengyu_search_result.addLayout(_lay_out_chengyu_get_search)
        _lay_out_chengyu_search_result.addWidget(_label_search_result_chengyu)

        _lay_out_chengyu_search_result.addWidget(self.table_chengyu_search)
        self.dialog_chengyu_search.setLayout(_lay_out_chengyu_search_result)

        self.radio_button_chengyu_search.toggled.connect(self.show_dialog_chengyu_search)

    def show_dialog_chengyu_search(self):
        if self.radio_button_chengyu_search.isChecked():
            if self.dialog_chengyu_search.isVisible() is False:
                self.dialog_chengyu_search.show()
        else:
            self.dialog_chengyu_search.close()

    def del_skill_table_row(self):
        """
        删除行，需要选中具体的行
        :return:
        """
        selected_row = self._skill_table.currentRow()
        if selected_row == 0 and not self._skill_table.selectedItems():
            QtWidgets.QMessageBox.information(self, '提示', "请选择需要删除的技能")
            return False
        self._skill_table.removeRow(selected_row)
        return True

    def add_skill_table_row(self):
        """
        新增行
        如果没有选择制定的行，那么就插入在最后面
        :return:
        """
        selected_row = self._skill_table.currentRow() + 1
        if not self._skill_table.selectedItems():
            selected_row = self._skill_table.rowCount()
        self._skill_table.insertRow(selected_row)

    def open_config_file(self):
        """
        打开配置文件
        :return:
        """
        config_file: str = '.\\_internal\\Resources\\'
        if not os.path.exists(config_file):  # 如果主目录+小时+分钟这个文件路径不存在的话
            config_file = ".\\DeskPageV2\\Resources\\"
        QtWidgets.QFileDialog.getOpenFileName(self, "资源文件", config_file,
                                              "Text Files (*.yaml;*.bat;*.png;*.ico;*.dll;*.json;*.*)")

    def edit_config_file(self):
        if self.widget_dock_setting.isVisible() is False:
            self.widget_dock_setting.setVisible(True)

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

    def open_func_detail_widget(self):
        """
        打开功能说明
        """
        self.__new_windows = MarkdownViewer()
        self.__new_windows.show()

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

    def set_ui_key_press_auto(self):
        """
        设置dockWidget是否显示
        :return:
        """
        if self.radio_button_key_auto.isChecked():
            self.widget_dock.setVisible(True)
        else:
            self.widget_dock.setVisible(False)

    def set_ui_market_goods_list(self):
        """
        设置dockWidget是否显示
        :return:
        """
        if self.radio_button_auction_market.isChecked():
            self.widget_dock_market.setVisible(True)
        else:
            self.widget_dock_market.setVisible(False)

    def set_market_goods_list(self, goods_name_list: list):
        """
        设置当前界面上的物品最大价格
        """
        # 设置表格的行数和列数
        self.list_widget_market.setRowCount(len(goods_name_list))  # 设置表格有行数
        self.list_widget_market.setColumnCount(2)  # 设置表格有2列

        column_labels = ['物品名称', '最大价格']
        self.list_widget_market.setHorizontalHeaderLabels(column_labels)

        # 添加按钮控件到每个单元格
        for row in range(len(goods_name_list)):
            label = QtWidgets.QLabel(goods_name_list[row])
            line = QtWidgets.QLineEdit()
            line.setPlaceholderText("设置最高价格(两)")
            line.setValidator(QIntValidator())
            # 将按钮控件添加到单元格中
            self.list_widget_market.setCellWidget(row, 0, label)
            self.list_widget_market.setCellWidget(row, 1, line)

        time.sleep(1)
        self.list_widget_market.resizeColumnsToContents()
        self.list_widget_market.resizeRowsToContents()

        # 获取QDockWidget的建议大小
        size_hint = self.widget_dock_market.sizeHint()

        # 设置QDockWidget的新尺寸
        self.widget_dock_market.resize(size_hint)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_gui = MainGui()
    main_gui.show()
    sys.exit(app.exec())
