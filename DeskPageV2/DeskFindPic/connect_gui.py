import datetime
import platform
import time

from DeskPageV2.DeskGUIQth.execut_th import DanceThByFindPic, ScreenGameQth
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

        # # 键盘驱动对象
        self.dm_window = getWindows()
        self.dm_key_board = getKeyBoardMouse()

        # 定义3个窗口的handle
        self.gui_windows_handle_list = []

        # 定义一些变量
        self.dm_driver = None  # 大漠驱动
        self.handle_dict: dict = {}

        # 初始化一些控件的内容
        self.status_bar_print.showMessage(" 当前状态 : 等待执行")
        self.radio_button_school_dance.setChecked(True)

        # 初始化一些对象
        self.loading_driver()

        # 信号槽连接
        self.th.status_bar.connect(self.print_status_bar)
        self.th.sin_out.connect(self.print_logs)
        self.th.sin_work_status.connect(self.execute_status)
        self.th_screen.status_bar.connect(self.print_status_bar)
        self.th_screen.sin_out.connect(self.print_logs)
        self.th_screen.sin_work_status.connect(self.execute_status)

        # click事件的信号槽
        self.push_button_start_or_stop_execute.clicked.connect(self.execute_button_status)
        self.push_button_get_windows_handle.clicked.connect(self.get_windows_handle)
        self.push_button_test_windows.clicked.connect(self.test_windows_handle)

    @staticmethod
    def get_windows_release() -> int:
        """
        获取windows版本
        :return: 7, 8, 10
        """
        return int(platform.release())

    def loading_driver(self):
        """
        加载驱动
        :return:
        """
        self.push_button_get_windows_handle.setEnabled(False)
        if self.get_windows_release() == 7:
            # 如果当前系统是win7，那么就启用大漠插件，那么优先检查是否有幽灵键鼠，没有的话就使用大漠插件
            if self.loading_driver_dm():
                is_load_keyboard_driver = True
            else:
                self.print_logs("开始尝试加载幽灵键鼠")
                self.loading_driver_ghost()
                is_load_keyboard_driver = True
        else:
            self.loading_driver_ghost()
            is_load_keyboard_driver = True
        if is_load_keyboard_driver is True:
            self.push_button_get_windows_handle.setEnabled(True)
            self.print_logs("更新日期: 2024-03-02"
                            "\n"
                            "\n注意："
                            "\n1:游戏客户端设置为【经典模式】，不然无法正常识别到游戏画面"
                            "\n2:开始执行后，请不要做其他操作，保持游戏窗口一直显示在最前面"
                            "\n3:本工具为免费工具，请勿支付金钱购买"
                            "\n4:项目地址请访问 https://github.com/moonlessdark/JiuYinDance", True)

    def loading_driver_ghost(self) -> bool:
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

    def loading_driver_dm(self) -> bool:
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
            self.print_logs("大漠插件加载失败，请检查驱动文件是否存在或杀毒软件误杀.或者请鼠标右键以'管理员权限'执行本程序")
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
        self.text_browser_print_log.insertPlainText(text + '\n')

    def print_status_bar(self, text: str):
        """
        打印底部状态栏的日志
        :param text:
        :return:
        """
        def get_local_time() -> str:
            now = datetime.datetime.now()
            time_str = now.strftime("%H:%M:%S")
            return time_str

        self.status_bar_print.showMessage(f"{get_local_time()} {text}")

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

    def execute_start(self):
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
            if self.radio_button_school_dance.isChecked():
                """
                如果是团练/授业
                """
                self.th.start_execute_init(windows_handle_list=windows_list, dance_type="团练",
                                           key_board_mouse_driver_type=key_board)
                self.th.start()
                self.push_button_start_or_stop_execute.setText("结束执行")

                self.push_button_get_windows_handle.setEnabled(False)
                self.push_button_test_windows.setEnabled(False)

            elif self.radio_button_party_dance.isChecked():
                """
                如果是势力/隐士
                """
                self.th.start_execute_init(windows_handle_list=windows_list, dance_type="望辉洲",
                                           key_board_mouse_driver_type=key_board)

                self.th.start()
                self.push_button_start_or_stop_execute.setText("结束执行")

                self.push_button_get_windows_handle.setEnabled(False)
                self.push_button_test_windows.setEnabled(False)

            elif self.radio_button_game_screen.isChecked():
                """
                如果是截图
                """
                self.th_screen.get_param(windows_handle_list=windows_list, pic_save_path="D://")
                self.th_screen.start()
                self.push_button_start_or_stop_execute.setText("结束执行")
            else:
                self.print_logs("还未选择需要执行的功能")

    def execute_button_status(self):
        if self.radio_button_game_screen.isChecked():
            if self.th_screen.working is True and self.push_button_start_or_stop_execute.text() == '开始执行':
                self.execute_start()
            elif self.th_screen.working is True and self.push_button_start_or_stop_execute.text() == '结束执行':
                self.stop_execute()
            elif self.th_screen.working is False and self.push_button_start_or_stop_execute.text() == '开始执行':
                self.execute_start()
        else:
            if self.th.working is True and self.push_button_start_or_stop_execute.text() == '开始执行':
                self.execute_start()
            elif self.th.working is True and self.push_button_start_or_stop_execute.text() == '结束执行':
                self.stop_execute()
            elif self.th.working is False and self.push_button_start_or_stop_execute.text() == '开始执行':
                self.execute_start()

    def execute_stop(self):
        """
        结束执行
        :return:
        """
        self.th.stop_execute_init()
        self.print_logs("等待程序结束运行")
        self.print_status_bar("等待执行")

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

    def stop_execute(self):
        """
        停止执行
        :return:
        """
        self.print_logs("已发出停止指令，请等待")
        if self.radio_button_game_screen.isChecked():
            self.th_screen.stop_execute_init()
        else:
            self.th.stop_execute_init()
        self.push_button_start_or_stop_execute.setText("开始执行")
        self.status_bar_print.showMessage("等待执行")
        # 按钮恢复一下
        self.push_button_get_windows_handle.setEnabled(True)
        self.push_button_test_windows.setEnabled(True)

    def execute_status(self, sin_work_status):
        if sin_work_status == "结束":
            self.push_button_start_or_stop_execute.setEnabled(True)
            self.stop_execute()
