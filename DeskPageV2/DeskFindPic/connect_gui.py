import ctypes
import platform
import time

from PySide6 import QtWidgets
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QMessageBox

from DeskPageV2.DeskFindPic.findCars import TruckCar
from DeskPageV2.DeskGUIQth.execut_th import DanceThByFindPic, ScreenGameQth, QProgressBarQth, AutoPressKeyQth, \
    TruckCarTaskQth, TruckTaskFightMonsterQth, TruckTaskFindCarQth, FollowTheTrailOfTruckQth
from DeskPageV2.DeskPageGUI.MainPage import MainGui
from DeskPageV2.DeskTools.DmSoft.get_dm_driver import getDM, getWindows, getKeyBoardMouse
from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import GetGhostDriver, SetGhostBoards
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.Utils.dataClass import DmDll, GhostDll, Config
from DeskPageV2.Utils.keyEvenQTAndGhost import check_ghost_code_is_def
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
        self.th_key_press_auto = AutoPressKeyQth()

        # 押镖
        self.th_truck_task = TruckCarTaskQth()  # 运镖
        self.th_truck_fight_monster = TruckTaskFightMonsterQth()  # 打怪
        self.th_truck_find_car = TruckTaskFindCarQth()  # 找NPC
        self.th_follow_truck = FollowTheTrailOfTruckQth()  # 查找镖车

        # # 键盘驱动对象
        self.dm_window = getWindows()
        self.dm_key_board = getKeyBoardMouse()

        # 定义3个窗口的handle
        self.gui_windows_handle_list = []

        # 定义一些变量
        self.dm_driver = None  # 大漠驱动
        self.handle_dict: dict = {}
        self.execute_button_status_bool: bool = False  # 按钮状态，用于判断文字显示

        self.keyboard_type = None  # 加载的键盘驱动类型

        self.is_debug = False

        # 初始化一些控件的内容
        self.radio_button_school_dance.setChecked(True)

        # 初始化一些对象
        self.loading_driver()
        self.load_config()
        self.progress_bar_action(0)  # 先把进度条隐藏了

        # 信号槽连接
        self.th.status_bar.connect(self.print_status_bar)
        self.th.sin_out.connect(self.print_logs)
        self.th.sin_work_status.connect(self._th_execute_stop)
        self.th_screen.status_bar.connect(self.print_status_bar)
        self.th_screen.sin_out.connect(self.print_logs)
        self.th_progress_bar.thread_step.connect(self.progress_bar_action)

        self.th_key_press_auto.sin_out.connect(self.print_logs)
        self.th_key_press_auto.sin_work_status.connect(self._th_execute_stop)

        self.th_truck_task.sin_out.connect(self.print_logs)
        self.th_truck_task.sin_work_status.connect(self._th_execute_stop)

        # 押镖相关的信号槽
        self.th_truck_task.sin_out.connect(self.print_logs)
        self.th_truck_task.next_step.connect(self.truck_task_func_switch)
        self.th_truck_task.sin_work_status.connect(self._th_execute_stop)

        self.th_truck_find_car.sin_out.connect(self.print_logs)
        self.th_truck_find_car.next_step.connect(self.truck_task_func_switch)
        self.th_truck_find_car.sin_work_status.connect(self._th_execute_stop)

        self.th_truck_fight_monster.sin_out.connect(self.print_logs)
        self.th_truck_fight_monster.next_step.connect(self.truck_task_func_switch)
        self.th_truck_fight_monster.sin_work_status.connect(self._th_execute_stop)

        self.th_follow_truck.sin_out.connect(self.print_logs)
        self.th_follow_truck.next_step.connect(self.truck_task_func_switch)
        self.th_follow_truck.sin_work_status.connect(self._th_execute_stop)

        self.text_browser_print_log.textChanged.connect(lambda: self.text_browser_print_log.moveCursor(QTextCursor.End))

        # click事件的信号槽
        self.push_button_start_or_stop_execute.clicked.connect(self.click_execute_button)
        self.push_button_get_windows_handle.clicked.connect(self.get_windows_handle)
        self.push_button_test_windows.clicked.connect(self.test_windows_handle)
        self.radio_button_key_auto.toggled.connect(self.set_ui_key_press_auto)

        # 按钮设置
        self.push_button_save_key_press_add.clicked.connect(self.key_press_even_add)
        self.push_button_save_key_press_delete.clicked.connect(self.key_press_even_del)
        self.push_button_save_key_press_save.clicked.connect(self.key_press_even_save)

        # 其他的
        self.widget_dock_setting.visibilityChanged.connect(self.load_config)
        self.push_button_save_setting.clicked.connect(self.update_config)
        self.widget_dock.visibilityChanged.connect(self.on_top_level_changed)

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

    def load_config(self, is_top_level=True):
        """
        加载配置文件
        :return:
        """
        if is_top_level:
            config_ini: Config = self.file_config.get_find_pic_config()
            is_debug: bool = config_ini.is_debug
            dance_threshold: float = config_ini.dance_threshold
            whz_dance_threshold: float = config_ini.whz_dance_threshold
            area_dance_threshold: float = config_ini.area_dance_threshold
            self.line_dance_threshold.setValue(dance_threshold)
            self.line_whz_dance_threshold.setValue(whz_dance_threshold)
            self.line_area_dance_threshold.setValue(area_dance_threshold)

            if is_debug:
                self.check_debug_mode.setChecked(True)
            else:
                self.check_debug_mode.setChecked(False)

    def show_dialog(self, tips: str):
        """
        创建一个消息框，并显示
        :param tips:
        :return:
        """
        QMessageBox.information(self, '提示', tips)

    def update_config(self):
        """
        更新配置文件
        :return:
        """

        dance_threshold = self.line_dance_threshold.value()
        whz_dance_threshold = self.line_whz_dance_threshold.value()
        area_dance_threshold = self.line_area_dance_threshold.value()
        is_debug = True if self.check_debug_mode.isChecked() else False

        self.file_config.update_find_pic_config(dance_threshold_tl=dance_threshold,
                                                dance_threshold_whz=whz_dance_threshold,
                                                dance_threshold_area=area_dance_threshold,
                                                debug=is_debug)

        self.show_dialog("更新成功")

    def loading_driver(self):
        """
        加载驱动
        :return:
        """
        self.push_button_get_windows_handle.setEnabled(False)
        is_load_keyboard_driver: bool = False

        self.print_logs("开始尝试加载幽灵键鼠")
        if self._loading_driver_ghost():
            is_load_keyboard_driver = True
        else:
            pass
            # if self.get_windows_release() == 7:
            #     if ctypes.windll.shell32.IsUserAnAdmin() == 1:
            #         self.print_logs("\n当前系统是win7，开始尝试加载大漠插件")
            #         # 如果当前系统是win7，那么就启用大漠插件，那么优先检查是否有幽灵键鼠，没有的话就使用大漠插件
            #         if self._loading_driver_dm():
            #             is_load_keyboard_driver = True
            #     else:
            #         QMessageBox.critical(None, "Error", "当前系统是win7，请以“管理员”权限运行此脚本")
            #         self.print_logs("\n")
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
                self.keyboard_type = "ghost"
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
            self.keyboard_type = "dm"
            return True
        else:
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
        elif self.radio_button_school_dance.isChecked() or self.radio_button_party_dance.isChecked():
            """
            如果当前团练授业模式
            """
            self.th.stop_execute_init()
        elif self.radio_button_key_auto.isChecked():
            self.th_key_press_auto.stop_execute_init()
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
            self.is_debug = True if self.check_debug_mode.isChecked() else False
            start_log_string: str = "开始执行"
            if self.is_debug:
                start_log_string: str = "开始执行Debug模式(仅限团练授业)，详情请查看程序根目录生成的日志文件"
            self.print_logs(start_log_string, is_clear=True)
            if self.radio_button_school_dance.isChecked() or self.radio_button_party_dance.isChecked():
                """
                如果是团练/授业
                """
                if self.radio_button_school_dance.isChecked():
                    dance_type = "团练"
                else:
                    dance_type = "望辉洲"
                self.th.start_execute_init(windows_handle_list=windows_list,
                                           dance_type=dance_type,
                                           key_board_mouse_driver_type=self.keyboard_type,
                                           debug=self.is_debug)
                self.th.start()
                self.changed_execute_button_text_and_status(True)
                # 开始执行跑马灯效果
                self.th_progress_bar.start_init()
                self.th_progress_bar.start()

            elif self.radio_button_game_screen.isChecked():
                """
                如果是截图
                """
                self.th_screen.get_param(windows_handle_list=windows_list, pic_save_path="./")
                self.th_screen.start()
                self.changed_execute_button_text_and_status(True)
                # 开始执行跑马灯效果
                self.th_progress_bar.start_init()
                self.th_progress_bar.start()

            elif self.radio_button_key_auto.isChecked():
                """
                如果是键盘连点器
                """
                key_selected_str = self.list_widget.currentItem()
                if key_selected_str is not None:
                    key_selected_str = key_selected_str.text()
                    if len(windows_list) == 1:
                        self.th_key_press_auto.get_param(windows_handle=windows_list[0],
                                                         key_press_list=key_selected_str,
                                                         press_count=self.line_key_press_execute_sum.value(),
                                                         press_wait_time=self.line_key_press_wait_time.value())
                        self.th_key_press_auto.start()
                        self.changed_execute_button_text_and_status(True)
                        # 开始执行跑马灯效果
                        self.th_progress_bar.start_init()
                        self.th_progress_bar.start()

                    else:
                        self.print_logs("键盘连按功能暂时只支持1个窗口运行")
                else:
                    self.print_logs("请选择需要执行的键盘按钮")
            elif self.radio_button_truck_car_task.isChecked():
                """
                如果是押镖
                """
                if len(windows_list) == 1:

                    self.th_truck_task.get_param(windows_list[0], 5)
                    self.th_truck_task.start()

                    self.changed_execute_button_text_and_status(True)
                    # 开始执行跑马灯效果
                    self.th_progress_bar.start_init()
                    self.th_progress_bar.start()

            else:
                self.print_logs("还未选择需要执行的功能")

    def _th_execute_stop(self, execute_status: bool):
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
                        if self.keyboard_type == "ghost":
                            SetGhostBoards().click_press_and_release_by_key_name("K")
                        else:
                            getKeyBoardMouse().key_press_char("K")
                        self.print_logs("窗口(%s)已激活，并尝试按下了'K'按钮" % i)
                        break
                time.sleep(1)
                GetHandleList().set_allow_set_foreground_window()  # 取消置顶

    def key_press_even_add(self):
        """
        新增列表
        :return:
        """
        self.list_widget.addItem(QtWidgets.QListWidgetItem(f"请输入按钮"))

    def key_press_even_del(self):
        """
        删除
        :return:
        """
        if self.list_widget.selectedItems():
            item = self.list_widget.currentRow()
            self.list_widget.takeItem(item)
        else:
            self.show_dialog("请选择需要删除的记录")

    def key_press_even_save(self):
        """
        保存按钮
        :return:
        """

        def get_all_items(list_widget):
            items = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                items.append(item.text())
            return items

        key_list: list = []
        all_items = get_all_items(self.list_widget)

        if all_items is not None:
            for item in all_items:
                key_word: str = str(item)
                if key_word != "请输入按钮":
                    key_list.append(key_word)
            if len(key_list) > 0:

                # 判断一下输入的 按钮我有没有定义
                res_list: list = check_ghost_code_is_def(key_list)
                if len(res_list) == 0:
                    self.file_config.save_key_even_code_auto_list(key_list)
                    self.show_dialog("保存成功")
                else:
                    error_key: str = " 和 ".join(res_list)
                    self.show_dialog(f"按钮 {error_key} 暂不支持,请更换按钮")
            else:
                self.show_dialog("请先设置按钮再保存")
        else:
            self.show_dialog("没有需要保存的按钮")
        self.on_top_level_changed()

    def on_top_level_changed(self):
        """
        加载一下配置文件
        :return:
        """
        self.list_widget.clear()
        if self.widget_dock.isTopLevel():
            res_file: str = self.file_config.get_key_even_code_auto_list()
            res_list: list = list(eval(res_file))
            for res in res_list:
                self.list_widget.addItem(res)

    def truck_task_func_switch(self, step: int):
        """
        切换方法
        :param step: 1 是扫描打怪。
                     2 是重新查找 镖车并开车,
                     3: 打怪中，暂时查找车辆，
                     4：打怪结束，重新查找车辆
        """
        # 前面已经做了判断，只能有一个窗口执行，所以这里直接获取
        windows_handle = self.check_handle_is_selected()[0]
        if step == 1:
            print("接收到信号，开始等待出怪")
            self.th_truck_fight_monster.get_param(windows_handle)
            self.th_truck_fight_monster.start()
        elif step == 2:
            print("接收到信号，开始查找镖车")
            self.th_truck_find_car.get_param(windows_handle, True)
            self.th_truck_find_car.start()
        elif step == 3:
            print("接收到信号，正在打怪中，暂时停止找车")
            self.th_truck_find_car.get_param(windows_handle, False)
            self.th_follow_truck.get_param(windows_handle, False)  # 停止跟踪车辆
        elif step == 4:
            print("接收到信号，打怪结束，开始继续找车")
            self.th_truck_find_car.get_param(windows_handle, True)
            self.th_truck_find_car.start()
        elif step == 5:
            print("接收到信号，保持镖车在屏幕中心区域")
            self.th_follow_truck.get_param(windows_handle, True)
            self.th_follow_truck.start()
        else:
            """
            如果是其他值，一般是 0，就表示结束
            """
            self.th_truck_fight_monster.get_param(windows_handle, False)  # 停止打怪
            self.th_truck_find_car.get_param(windows_handle, False)  # 停止找车
            self.th_follow_truck.get_param(windows_handle, False)  # 停止跟踪车辆
