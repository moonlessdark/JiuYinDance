import datetime
import platform
import time

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QLabel

from DeskPageV2.DeskGUIQth.execut_th import DanceThByFindPic, ScreenGameQth, QProgressBarQth
from DeskPageV2.DeskPageGUI.MainPage import MainGui
from DeskPageV2.DeskTools.DmSoft.get_dm_driver import getDM, getWindows, getKeyBoardMouse
from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import GetGhostDriver, SetGhostBoards
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.Utils.dataClass import DmDll, GhostDll
from DeskPageV2.Utils.load_res import GetConfig


class Dance(MainGui):
    """
    团练授业
    """

    file_config = GetConfig()

    def __init__(self):
        super().__init__()
        # 初始化一些对象
        self.th = DanceThByFindPic()
        self.th_screen = ScreenGameQth()
        self.th_progress_bar = QProgressBarQth()
        # # 键盘驱动对象
        self.dm_window = getWindows()
        self.dm_key_board = getKeyBoardMouse()

        # 定义3个窗口的handle
        self.gui_windows_handle_list = []

        # 定义一些变量
        self.dm_driver = None  # 大漠驱动
        self.handle_dict: dict = {}
        self.execute_button_status_bool: bool = False  # 按钮状态，用于判断文字显示

        # 初始化一些控件的内容
        self.radio_button_school_dance.setChecked(True)

        # 初始化一些对象
        self.loading_driver()
        self.progress_bar_action(0)  # 先把进度条隐藏了

        # 信号槽连接
        self.th.status_bar.connect(self.print_status_bar)
        self.th.sin_out.connect(self.print_logs)
        self.th.sin_work_status.connect(self._th_execute_sop)
        self.th_screen.status_bar.connect(self.print_status_bar)
        self.th_screen.sin_out.connect(self.print_logs)
        self.th_progress_bar.thread_step.connect(self.progress_bar_action)

        self.text_browser_print_log.textChanged.connect(lambda: self.text_browser_print_log.moveCursor(QTextCursor.End))

        # click事件的信号槽
        self.push_button_start_or_stop_execute.clicked.connect(self.click_execute_button)
        self.push_button_get_windows_handle.clicked.connect(self.get_windows_handle)
        self.push_button_test_windows.clicked.connect(self.test_windows_handle)

    @staticmethod
    def get_windows_release() -> int:
        """
        获取windows版本
        :return: 7, 8, 10
        """
        return int(platform.release())

    @staticmethod
    def get_local_time():
        """
        获取当前时间
        :return:
        """
        time_string: str = time.strftime("%H:%M:%S", time.localtime(int(time.time())))
        return time_string

    def loading_driver(self):
        """
        加载驱动
        :return:
        """
        self.push_button_get_windows_handle.setEnabled(False)
        if self.get_windows_release() == 7:
            # 如果当前系统是win7，那么就启用大漠插件，那么优先检查是否有幽灵键鼠，没有的话就使用大漠插件
            if self._loading_driver_dm():
                is_load_keyboard_driver = True
            else:
                self.print_logs("开始尝试加载幽灵键鼠")
                self._loading_driver_ghost()
                is_load_keyboard_driver = True
        else:
            self._loading_driver_ghost()
            is_load_keyboard_driver = True
        if is_load_keyboard_driver is True:
            self.push_button_get_windows_handle.setEnabled(True)

    def _loading_driver_ghost(self) -> bool:
        """
        加载幽灵键鼠标驱动
        :return:
        """
        ghost_tools_dir: GhostDll = self.file_config.get_dll_ghost()
        GetGhostDriver(dll_path=ghost_tools_dir.dll_ghost)
        if GetGhostDriver.dll is not None:
            SetGhostBoards().open_device()  # 启动幽灵键鼠标
            if SetGhostBoards().check_usb_connect():
                self.print_logs("幽灵键鼠加载成功")
                return True
            else:
                self.print_logs("未检测到usb设备,请检查后重试")
        else:
            self.print_logs("幽灵键鼠驱动加载失败,请确认是否缺失了驱动文件,请检查后重试")
        return False

    def _loading_driver_dm(self) -> bool:
        """
        加载大漠插件驱动
        注意：此免费版本不支持win7以上的系统
        :return:
        """
        dm_tools_dir: DmDll = self.file_config.get_dll_dm()
        self.dm_driver = getDM(dm_reg_path=dm_tools_dir.dll_dm_reg, dm_path=dm_tools_dir.dll_dm)

        dm_release: str = self.dm_driver.get_version()
        if dm_release is not None:
            self.print_logs("大漠驱动免注册加载成功")
            return True
        else:
            self.print_logs(
                "大漠插件加载失败，请检查驱动文件是否存在或杀毒软件误杀.或者请鼠标右键以'管理员权限'执行本程序")
            return False

    def print_logs(self, text, is_clear=False):
        """
        打印日志的方法
        :param is_clear: 是否清除日志
        :param text: 日志内容
        :return:
        """
        if is_clear:
            self.text_browser_print_log.clear()
        self.text_browser_print_log.insertPlainText(f"{self.get_local_time()} {text}\n")

    def progress_bar_action(self, step: int):
        """
        进度条跑马灯
        :return:
        """

        if step == 0:
            self.progress_bar.setVisible(False)
            self.status_bar_label_left.setText("等待执行")
        else:
            self.status_bar_label_left.setText(self.get_local_time())
            if self.progress_bar.isVisible() is False:
                self.progress_bar.setVisible(True)
            self.progress_bar.setValue(step)

    def print_status_bar(self, text: str, find_button_count: int = 0):
        """
        打印底部状态栏的日志
        :param find_button_count: 已经找到了几个按钮了
        :param text: 打印的日志
        :return:
        """
        self.status_bar_label_right.setText(f"一共识别了 {find_button_count} 轮")

    def check_handle_is_selected(self) -> list:
        """
        看看哪些窗口已经勾选了
        :return:
        """
        windows_list = []
        if self.check_box_windows_one.isChecked():
            windows_list.append(self.handle_dict["windows_1"])
        if self.check_box_windows_two.isChecked():
            windows_list.append(self.handle_dict["windows_2"])
        if self.check_box_windows_three.isChecked():
            windows_list.append(self.handle_dict["windows_3"])
        return windows_list

    def changed_execute_button_text_and_status(self, button_status: bool):
        """
        更新执行按钮的文字和状态
        :param button_status:
        :return:
        """
        self.status_bar_print.showMessage("")
        if button_status is True:
            self.execute_button_status_bool = True  # 已经开始执行了
            self.push_button_start_or_stop_execute.setText("结束执行")
            self.push_button_get_windows_handle.setEnabled(False)
            self.push_button_test_windows.setEnabled(False)
        else:
            self.execute_button_status_bool = False  # 结束循环，等待执行
            self.push_button_start_or_stop_execute.setText("开始执行")
            self.push_button_get_windows_handle.setEnabled(True)
            self.push_button_test_windows.setEnabled(True)

    def click_execute_button(self):
        """
        判断开始还是结束
        :return:
        """
        if self.execute_button_status_bool is False:
            """
            如果当前状态是False，表示接下来需要开始执行循环,开始发出开始命令，等待开始
            """
            self._execute_start()
        else:
            """
            如果当前状态是True，说明正在执行，接下来需要停止，开始发出结束命令，等待结束
            """
            self._execute_stop()

    def _execute_stop(self):
        """
        点击结束执行按钮
        :return:
        """
        self.print_logs("已发出停止指令，请等待")
        if self.radio_button_game_screen.isChecked():
            """
            如果当前是截图模式
            """
            self.th_screen.stop_execute_init()
        else:
            """
            如果当前团练授业模式
            """
            self.th.stop_execute_init()
        self.th_progress_bar.stop_init()
        self.changed_execute_button_text_and_status(False)

    def _execute_start(self):
        """
        点击开始执行按钮
        :return:
        """
        windows_list = self.check_handle_is_selected()
        if len(windows_list) == 0:
            self.print_logs("请选择您需要执行的游戏窗口")
        else:
            self.print_logs("开始执行", is_clear=True)
            key_board: str = "dm" if int(self.get_windows_release()) <= 7 else "ghost"

            if self.radio_button_school_dance.isChecked() or self.radio_button_party_dance.isChecked():
                """
                如果是团练/授业
                """
                if self.radio_button_school_dance.isChecked():
                    dance_type = "团练"
                else:
                    dance_type = "望辉洲"

                self.th.start_execute_init(windows_handle_list=windows_list, dance_type=dance_type,
                                           key_board_mouse_driver_type=key_board)
                self.th.start()
                self.changed_execute_button_text_and_status(True)
                self.th_progress_bar.start_init()
                self.th_progress_bar.start()

            elif self.radio_button_game_screen.isChecked():
                """
                如果是截图
                """
                self.th_screen.get_param(windows_handle_list=windows_list, pic_save_path="./")
                self.th_screen.start()
                self.changed_execute_button_text_and_status(True)
            else:
                self.print_logs("还未选择需要执行的功能")

    def _th_execute_sop(self, execute_status: bool):
        """
        进程的停止状态
        :param execute_status:
        :return:
        """
        if execute_status is False:
            self._execute_stop()

    def get_windows_handle(self):
        """
        获取游戏窗口数量
        :return:
        """
        handle_list = GetHandleList().get_windows_handle()
        self.handle_dict = {}
        # handle_list = getWindows().enum_window(0, "", "FxMain", 2)
        if 0 < len(handle_list) <= 3:
            self.push_button_test_windows.setEnabled(True)
            self.push_button_start_or_stop_execute.setEnabled(True)
            for index_handle in range(len(handle_list)):
                self.handle_dict["windows_" + str(index_handle + 1)] = str(handle_list[index_handle])
            self.print_logs("已检测到了 %d 个获取到的窗口" % len(self.handle_dict.keys()), is_clear=True)
        elif len(handle_list) > 4:
            self.print_logs("检测到 %d 个游戏窗口，请减少至3个再次重试" % len(handle_list), is_clear=True)
        else:
            self.print_logs("未发现游戏窗口，请登录游戏后再次重试", is_clear=True)
        self.set_check_box_by_game_windows_enable()

    def set_check_box_by_game_windows_enable(self):
        """
        将窗口handle设置到控件是否为启用
        :return:
        """
        windows_check_element = [self.check_box_windows_one, self.check_box_windows_two, self.check_box_windows_three]
        self.set_ui_load_windows_check_box_init()
        self.push_button_test_windows.setEnabled(False)
        self.push_button_start_or_stop_execute.setEnabled(False)
        if len(self.handle_dict.keys()) > 0:
            for index_key in range(len(self.handle_dict.keys())):
                windows_check_element[index_key].setEnabled(True)
            self.push_button_test_windows.setEnabled(True)
            self.push_button_start_or_stop_execute.setEnabled(True)

    def test_windows_handle(self):
        """
        检测游戏窗口.对当前活跃的游戏窗口进行检测
        :return:
        """
        handle_list = self.check_handle_is_selected()
        windows_release: int = self.get_windows_release()
        if len(handle_list) == 0:
            self.print_logs("请勾选需要测试的窗口", is_clear=True)
        else:
            self.print_logs("开始测试窗口", is_clear=True)
            for i in handle_list:
                for execute_num in range(5):
                    r = GetHandleList().activate_windows(i)
                    if r is False:
                        self.print_logs(f"{i} 激活失败，正在进行第{execute_num}次重试")
                        continue
                    else:
                        if windows_release > 7:
                            SetGhostBoards().click_press_and_release_by_key_name("K")
                        else:
                            getKeyBoardMouse().key_press_char("K")
                        self.print_logs("窗口(%s)已激活，并尝试按下了'K'按钮" % i)
                        break
                time.sleep(1)
                GetHandleList().set_allow_set_foreground_window()  # 取消置顶
