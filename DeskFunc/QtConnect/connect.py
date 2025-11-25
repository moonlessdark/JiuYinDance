import time

from PySide6.QtWidgets import QMessageBox

from DeskFunc.QThTask.QthMapGoods import MapGoodsQth
from DeskFunc.QThTask.QthMoneyCard import OpenGiftCard
from DeskPage.fuctionPage import TaskEnum
from DeskPage.mainPage import MainUI
from Utils.FindWindowsImage import WindowsHandle, WindowsCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import GetGhostDriver, SetGhostBoards, SetGhostMouse
from Utils.dataClass import GhostDll
from Utils.loadResources import GetConfig, get_map_goods_point_list_by_selected

from DeskFunc.TaskBussinese.findAuctionMarket import FindAuctionMarket

from DeskFunc.QThTask.QthDance import DanceThByFindPic
from DeskFunc.QThTask.QthScreen import ScreenGameQth
from DeskFunc.QThTask.QthTruck import TruckTaskFightMonsterQth, TruckCarTaskQth
from DeskFunc.QThTask.QthMyFight import MyFightXJ
from DeskFunc.QThTask.QthWorldMarket import WorldMarketGetGoodsQth

_windows_hwnd_save: dict = {}
_run_task_status: bool = False  # 任务执行状态


class TaskConnect(MainUI):

    """
    页面按钮和任务的关联类
    """
    file_config = GetConfig()

    def __init__(self):
        super().__init__()
        self.__init_driver()
        self.__init_game_windows_hwnd()

        # 把线程都加载进来
        self.qth_dance = DanceThByFindPic()  # 团练授业、势力修炼
        self.qth_cap_pic = ScreenGameQth()  # 游戏截图
        self.qht_open_gift = OpenGiftCard()  # 9点开卡
        self.qth_map_get = MapGoodsQth()  # 地图采集
        self.qth_truck_fight_monster = TruckTaskFightMonsterQth()  # 运镖打怪
        self.qth_truck_find = TruckCarTaskQth()  # 接镖
        self.qht_my_fight = MyFightXJ()  # 我的战斗
        self.qth_market = WorldMarketGetGoodsQth()  # 世界竞拍

        # 线程的信号槽连接
        # 团练授业
        self.qth_dance.sin_out.connect(self.log_print)  # 执行日志打印
        self.qth_dance.status_bar.connect(self.status_bar.update_execute_num)  # 右下角显示执行了几次
        self.qth_dance.sin_run_status.connect(self._update_task_run_status)
        # 窗口截图
        self.qth_cap_pic.sin_out.connect(self.log_print)
        self.qth_cap_pic.status_bar.connect(self.status_bar.update_execute_num)  # 右下角显示执行了几次
        self.qth_cap_pic.sin_run_status.connect(self._update_task_run_status)
        # 9点开卡
        self.qht_open_gift.sin_out.connect(self.log_print)
        self.qht_open_gift.status_bar.connect(self.status_bar.update_execute_num)  # 右下角显示执行了几次
        self.qht_open_gift.sin_run_status.connect(self._update_task_run_status)
        # 地图采集
        self.qth_map_get.sin_out.connect(self.log_print)
        self.qth_map_get.status_bar.connect(self.status_bar.update_execute_num)  # 右下角显示执行了几次
        self.qth_map_get.sin_run_status.connect(self._update_task_run_status)
        # 押镖
        self.qth_truck_fight_monster.sin_out.connect(self.log_print)
        self.qth_truck_find.sin_out.connect(self.log_print)
        self.qth_truck_fight_monster.next_step.connect(self.truck_task_func_switch)
        self.qth_truck_find.next_step.connect(self.truck_task_func_switch)
        self.qth_truck_find.sin_run_status.connect(self._update_task_run_status)
        # 我的战斗-玄机秘境
        self.qht_my_fight.sin_out.connect(self.log_print)
        self.qht_my_fight.status_bar.connect(self.status_bar.update_execute_num)
        self.qht_my_fight.sin_run_status.connect(self._update_task_run_status)
        # 世界竞拍
        self.qth_market.sin_out.connect(self.show_table_market)
        self.qth_market.status_information.connect(self._information_print)

        self.task_tab_windows.task_other.widget_world_market.push_button_market_get_goods_list.clicked.connect(self.market_get_product_price)  # 获取竞拍的商品列表

        # GUI的按钮的信号槽
        self.windows_get.push_button_run_windows.clicked.connect(self.run_task)  # 执行任务
        self.windows_get.push_button_get_windows.clicked.connect(self.__init_game_windows_hwnd)  # 获取窗口
        self.windows_get.push_button_test_windows.clicked.connect(self.test_hwnd)  # 测试窗口

    def __init_driver(self):
        """
        初始化幽灵键鼠的驱动
        :return:
        """
        ghost_tools_dir: GhostDll = self.file_config.get_dll_ghost()
        GetGhostDriver(dll_path=ghost_tools_dir.dll_ghost)
        if GetGhostDriver.dll is not None:
            SetGhostBoards().open_device()  # 启动幽灵键鼠标
            if SetGhostBoards().check_usb_connect():
                self.log_print("幽灵键鼠加载成功。\n如有疑问，请查看“帮助”-“功能说明”")
                SetGhostMouse().set_mouse_movement_speed(8)  # 初始化鼠标移动速度
                return True
            else:
                self.log_print("未检测到usb设备,请检查后重试")
        else:
            self.log_print("幽灵键鼠驱动加载失败,请确认是否缺失了驱动文件,请检查后重试")
        self.windows_get.push_button_run_windows.setEnabled(False)  # 未检测到驱动，把执行按钮禁用掉
        return False

    def __init_game_windows_hwnd(self):
        """
        检查一下游戏窗口
        :return:
        """
        global _windows_hwnd_save

        def __save_dict(hwnd_list: list):
            """
            将获取到的窗口句柄放入全局变量中方便调用
            :param hwnd_list:
            :return:
            """
            _windows_hwnd_save.clear()
            for index_h in range(len(hwnd_list)):
                _windows_hwnd_save[f"窗口:{index_h+1}"] = hwnd_list[index_h]

        _windows_list: list = WindowsHandle().get_windows_handle()
        if len(_windows_list) == 0:
            self.log_print("未找到窗口...")
            self.windows_get.push_button_run_windows.setEnabled(False)  # 未检测到驱动，把执行按钮禁用掉
            self.windows_get.push_button_test_windows.setEnabled(False)
        else:
            self.windows_get.push_button_test_windows.setEnabled(True)
            self.windows_get.push_button_run_windows.setEnabled(True)  # 未检测到驱动，把执行按钮禁用掉
            __save_dict(_windows_list)
            self.windows_get.get_windows(_windows_hwnd_save.keys())

    def __get_windows_hwnd_list(self) -> list:
        """
        获取当前窗口有哪些窗口句柄被勾选了
        :return:
        """
        _checked_hwnd_list: list = self.windows_get.get_windows_checked()
        xx_hwnd_list: list = [_windows_hwnd_save.get(h) for h in _checked_hwnd_list]
        return xx_hwnd_list

    def _information_print(self, information: str):
        """
        打印一下窗口
        """
        msg_box = QMessageBox(self)
        msg_box.setText(information)
        msg_box.setWindowTitle("信息")
        msg_box.setIcon(QMessageBox.Information)

    def test_hwnd(self):
        """
        检测窗口是否存在
        :return:
        """
        _checked_hwnd_list: list = self.__get_windows_hwnd_list()
        if len(_checked_hwnd_list) == 0:
            self.log_print("未勾选窗口...")
            return None
        for hwnd in _checked_hwnd_list:
            if WindowsCapture().windows_handle_visible(hwnd):
                WindowsHandle().activate_windows(hwnd)
                time.sleep(0.2)
                self.log_print(f"窗口 {hwnd} 已激活")
                time.sleep(1)
            else:
                self.log_print(f"{hwnd} 未显示，请检查")
        return None

    def run_task(self):
        """
        执行任务
        :return:
        """
        global _run_task_status

        _checked_hwnd_list: list = self.__get_windows_hwnd_list()
        if len(_checked_hwnd_list) == 0:
            self.log_print("请勾选需要执行的窗口")
            return False
        # 获取一下当前勾选了哪个任务
        _widget_radio_enum: TaskEnum = self.task_tab_windows.get_task_active()
        if not _run_task_status:
            self.log_clear()
            self.log_print(f"任务 {_widget_radio_enum.value} 开始执行...")

            if _widget_radio_enum == TaskEnum.dance_grey:
                """
                团练授业
                """
                self.qth_dance.init_task_param(hwnd_list=_checked_hwnd_list, dance_type="grey")
                self.qth_dance.start()
            elif _widget_radio_enum == TaskEnum.dance_green:
                """
                绿色的 上下左右
                """
                self.qth_dance.init_task_param(hwnd_list=_checked_hwnd_list, dance_type="green")
                self.qth_dance.start()
            elif _widget_radio_enum == TaskEnum.game_pic_screen:
                """
                窗口截图
                """
                self.qth_cap_pic.get_param(windows_handle_list=_checked_hwnd_list, pic_save_path="./")
                self.qth_cap_pic.start()
            elif _widget_radio_enum == TaskEnum.open_gift:
                """
                9点开卡
                """
                self.qht_open_gift.get_param(_checked_hwnd_list)
                self.qht_open_gift.start()
            elif _widget_radio_enum == TaskEnum.map_goods_get:
                """
                地图物资采集
                """
                if len(_checked_hwnd_list) > 1:
                    self.log_print("地图采集暂时只支持一个游戏窗口，请去掉不需要的窗口")
                    return None
                _map_point_list: list = get_map_goods_point_list_by_selected()
                _line_map_name: str = self.task_tab_windows.task_life_work.combo_box_goods_point_selected.currentText()
                if len(_map_point_list) == 0:
                    self.log_print(f"路线 {_line_map_name} 没有坐标,请重写选择路线")
                    return None
                self.qth_map_get.get_param(windows_handle=_checked_hwnd_list[0], map_goods_point_list=_map_point_list)
                self.qth_map_get.start()
            elif _widget_radio_enum == TaskEnum.express_transportation:
                """
                押镖
                """
                if len(_checked_hwnd_list) > 1:
                    self.log_print("暂时只支持控制一个游戏窗口!")
                    return None
                __truck_car_sum: int = int(self.task_tab_windows.task_activity.input_line_express_transportation.text())
                self.qth_truck_find.get_param(_checked_hwnd_list[0], __truck_car_sum)
                self.qth_truck_find.start()
            elif _widget_radio_enum == TaskEnum.xj_secret_scene:
                """
                我的战斗-玄机秘境
                """
                self.qht_my_fight.get_param(_checked_hwnd_list)
                self.qht_my_fight.start()
            elif _widget_radio_enum == TaskEnum.world_market:
                """
                世界竞拍
                """
                pass

        else:
            self.log_print(f"任务 {_widget_radio_enum.value} 停止执行...")
            self.windows_get.push_button_run_windows.setText("停止中...")
            self.windows_get.push_button_run_windows.setEnabled(False)

            """
            将以下人物进程都更新为"停止"。
            """
            self.qth_dance.stop_stak()  # 团练授业，绿色的上下左右
            self.qth_cap_pic.stop_execute_init()  # 截图
            self.qht_open_gift.stop_execute_init()  # 9点开卡
            self.qth_map_get.stop_execute_init()  # 地图采集
            self.qht_my_fight.stop_execute_init()  # 我的战斗
        return None

    def _update_task_run_status(self, task_status: bool):
        """
        更新任务执行状态
        :return:
        """
        global _run_task_status
        if task_status:
            self.windows_get.push_button_run_windows.setText("停止执行")
            self.windows_get.push_button_run_windows.setEnabled(True)
            self.status_bar.run_status(True)
            _run_task_status = True  # 执行状态更新为 进行中
            self.task_tab_windows.update_radio_enable(False)  # 将所有任务选项禁用
        else:
            self.windows_get.push_button_run_windows.setText("开始执行")
            self.windows_get.push_button_run_windows.setEnabled(True)
            self.status_bar.run_status(False)
            _run_task_status = False  # 执行状态更新为 未开始
            self.task_tab_windows.update_radio_enable(True)  # 将所有任务按钮 启用

    def truck_task_func_switch(self, step: int):
        """
        押镖的切换方法
        :param step: 1 是扫描打怪。
                     2 是重新查找 镖车并开车,
                     3: 打怪中，暂时查找车辆，
                     4：打怪结束，重新查找车辆
        """
        # 前面已经做了判断，只能有一个窗口执行，所以这里直接获取
        windows_handle: int = self.__get_windows_hwnd_list()[0]
        if step == 1:
            # self.print_logs("开启线程:等待劫镖NPC...")
            if not self.qth_truck_fight_monster.isRunning():
                self.qth_truck_fight_monster.get_param(windows_handle, True)
                self.qth_truck_fight_monster.start()
        elif step == 2:
            # self.print_logs("开启线程:查找镖车...")
            pass
        elif step == 3:
            # self.print_logs("开启线程:保持镖车在屏幕中心...")
            pass
        elif step == 4:
            # self.print_logs("关闭线程:保持镖车在屏幕中心...")
            pass
        elif step == 5:
            # self.print_logs("关闭线程:查找镖车...")
            pass
        elif step == 0:
            """
            如果是其他值，一般是 0，就表示结束
            """
            # self.print_logs("本次押镖结束,即将关闭所有线程")
            self.qth_truck_fight_monster.get_param(windows_handle, False)  # 停止打怪

    def market_get_product_price(self):
        """
        获取世界竞拍的商品
        """
        windows_handle_list: list = self.__get_windows_hwnd_list()
        if len(windows_handle_list) != 1:
            self.log_print("暂时只支持选中一个窗口")
            return None

        self.qth_market.get_param(windows_handle_list[0])
        self.qth_market.run()
        return None

    def show_table_market(self, product_list: list) -> bool:
        """
        显示商品内容到表格
        """
        if len(product_list) == 0:
            return False
        p_list: list = []
        for p in product_list:
            p_list.append(p[1])
        self.task_tab_windows.task_other.widget_world_market.add_table(p_list)
        return True
