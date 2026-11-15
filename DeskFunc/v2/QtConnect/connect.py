# coding: utf-8
"""
v2 总装层：把界面按钮与六个任务线程关联起来。

与 v1 的差异：
1. 只保留本次迁移的六个功能；
2. 不再有 OCR 依赖任务名单；
3. 所有任务线程通过 BaseTaskThread 的统一信号契约连接，停止时统一遍历 _task_threads；
4. 地图采集、世界竞拍、挑战点兑换只允许单窗口。
"""
import time

from PySide6.QtCore import QTimer

from Core.input.ghost import (
    GetGhostDriver,
    get_ghost_boards,
    get_ghost_mouse,
)
from Core.input.global_mouse import GlobalMouseListener
from Core.windows.window import (
    WindowsHandle,
    is_window_alive,
    is_window_capturable,
)
from DeskFunc.v2.QthTask.qth_buff_monitor import BuffMonitorTask
from DeskFunc.v2.QthTask.qth_challenge_point import ChallengePointTask
from DeskFunc.v2.QthTask.qth_dance import DanceTask
from DeskFunc.v2.QthTask.qth_get_all_goods import GetAllGoodsTask
from DeskFunc.v2.QthTask.qth_map_goods import MapGoodsTask
from DeskFunc.v2.QthTask.qth_money_card import OpenGiftCardTask
from DeskFunc.v2.QthTask.qth_world_market import WorldMarketTask
from DeskFunc.v2.TaskBussinese.buff_config import (
    load_buff_config,
    miss_seconds_from_config,
    panel_settings_from_config,
)
from DeskPage.v2.buff_panel import (BuffState, PanelSettings,
                                   load_show_icons)
from DeskPage.v2.buff_panel_window import PanelPresenter, StatePanelWidget
from DeskPage.v2.fuction_page import TaskEnum
from DeskPage.v2.main_page import MainUI
from Utils.load_resources import get_map_goods_point_list_by_selected
from Utils.resource_config import get_resources


class TaskConnect(MainUI):
    """页面按钮和任务的关联类。"""

    def __init__(self):
        super().__init__(buff_settings_changed=self._apply_buff_settings)

        self._windows_hwnd_save: dict[str, int] = {}
        self._run_task_status = False
        self._driver_ready = self._init_driver()
        self._init_game_windows_hwnd()

        self.global_mouse_monitoring = False
        self.global_mouse_listener: GlobalMouseListener | None = None

        # 任务窗口存活监测：记录本次任务勾选的窗口句柄，定时检查是否全部关闭
        self._run_task_hwnd_list: list[int] = []
        self._hwnd_alive_timer = QTimer(self)
        self._hwnd_alive_timer.setInterval(500)
        self._hwnd_alive_timer.timeout.connect(self._check_task_windows_alive)

        self._init_task_threads()
        self._bind_task_signals()
        self._init_buff_panel()

        self.windows_get.push_button_run_windows.clicked.connect(self.run_task)
        self.windows_get.push_button_get_windows.clicked.connect(self._init_game_windows_hwnd)
        self.windows_get.push_button_test_windows.clicked.connect(self.test_hwnd)
        # 选中 BUFF 监控时立即弹出状态面板，无需等待点击开始执行
        self.task_tab_windows.task_other.radio_button_buff_monitor.toggled.connect(
            self._on_buff_monitor_toggled)

    def _init_task_threads(self):
        """创建全部任务线程并集中登记。"""
        self.qth_dance = DanceTask()
        self.qth_open_gift = OpenGiftCardTask()
        self.qth_map_get = MapGoodsTask()
        self.qth_market = WorldMarketTask()
        self.qth_challenge = ChallengePointTask()
        self.qth_get_all_goods = GetAllGoodsTask()
        self.qth_buff = BuffMonitorTask()

        self._task_threads = [
            self.qth_dance,
            self.qth_open_gift,
            self.qth_map_get,
            self.qth_market,
            self.qth_challenge,
            self.qth_get_all_goods,
            self.qth_buff,
        ]

    def _bind_task_signals(self):
        """统一绑定任务线程的公共信号。"""
        for thread in self._task_threads:
            thread.sin_out.connect(self.log_print)
            thread.status_bar.connect(self.status_bar.update_execute_num)
            thread.sin_run_status.connect(self._update_task_run_status)
        # BUFF 任务额外把每帧识别结果交给主线程刷新独立面板
        self.qth_buff.buff_frame.connect(self._on_buff_frame)

    def _init_buff_panel(self) -> None:
        """创建独立的 BUFF 状态面板，任务开始前保持隐藏。"""
        assets = get_resources().buff_assets
        config = load_buff_config(assets.config_path)
        self._buff_settings = PanelSettings(
            **panel_settings_from_config(config))
        icons = load_show_icons(assets.showbuff_dir)
        if not icons:
            self.log_print("未读取到 BUFF 状态大图标，面板只能显示文字")

        self._buff_panel = StatePanelWidget()
        self._buff_panel.setWindowTitle("BUFF 状态面板")
        self._buff_panel.resize(420, 300)
        self._buff_presenter = PanelPresenter(
            self._buff_panel, icons, {}, "", lambda: self._buff_settings,
            miss_seconds=miss_seconds_from_config(config))

    def _apply_buff_settings(self, settings: PanelSettings) -> None:
        """设置对话框保存后立即更新面板外观，同时刷新检测灵敏度。"""
        self._buff_settings = settings
        self._buff_panel.set_settings(settings)
        assets = get_resources().buff_assets
        config = load_buff_config(assets.config_path)
        self._buff_presenter.set_miss_seconds(
            miss_seconds_from_config(config))

    def _on_buff_monitor_toggled(self, checked: bool) -> None:
        """选中 BUFF 监控时弹出面板并激活，取消选中时收起。"""
        if checked:
            self._buff_panel.set_overlay_mode(True)
            # 任务未启动时允许拖动面板，方便先摆到合适位置
            self._buff_panel.set_draggable(True)
            # 预览阶段不跟随目标窗口：先解除绑定并把面板设为激活窗口，
            # 等点击“开始执行”后再绑定目标窗口并开始跟随。
            self._buff_panel.unbind_target_window()
            self._buff_panel.activate_panel()
            return

        # 任务执行期间不应触发取消选中，这里只处理普通切换
        if self._run_task_status:
            return
        self._buff_panel.set_overlay_mode(False)
        self._buff_panel.hide()

    def _on_buff_frame(self, detections: list, title: str) -> None:
        """把任务线程的识别结果转换成面板状态并刷新。"""
        states = [
            BuffState(
                name=item.name,
                category=item.category,
                attribute=item.attribute,
                stack=item.stack,
                seconds=item.seconds,
                has_countdown=item.has_countdown,
                track_id=item.track_id,
                position=item.position,
                score=item.score,
            )
            for item in detections
        ]
        self._buff_presenter.update_frame(states, title)

    def _init_driver(self) -> bool:
        """初始化幽灵键鼠驱动。"""
        ghost_dll = get_resources().ghost_dll
        GetGhostDriver(dll_path=ghost_dll.dll_ghost)
        if GetGhostDriver.dll is not None:
            ghost_boards = get_ghost_boards()
            ghost_boards.open_device()
            if ghost_boards.check_usb_connect():
                self.log_print("幽灵键鼠加载成功。\n如有疑问，请查看“帮助”-“功能说明”\n")
                get_ghost_mouse().set_mouse_movement_speed(8)
                return True
            self.log_print("未检测到usb设备,请检查后重试\n")
        else:
            self.log_print("幽灵键鼠驱动加载失败,请确认是否缺失了驱动文件,请检查后重试\n")

        # 不直接禁用开始按钮：BUFF 监控只截图、不需要幽灵键鼠，
        # 其它任务在 run_task 中单独校验驱动状态。
        return False

    def toggle_global_mouse_monitoring(self, enable: bool):
        """切换鼠标中键停止监听。"""
        self.global_mouse_monitoring = enable
        if enable:
            if self.global_mouse_listener is None:
                self.global_mouse_listener = GlobalMouseListener()
                self.global_mouse_listener.middle_clicked.connect(
                    self.listener_task_run_status)
                self.global_mouse_listener.start()
        else:
            if self.global_mouse_listener is not None:
                self.global_mouse_listener.stop()
                self.global_mouse_listener = None

    def listener_task_run_status(self):
        """鼠标中键按下时停止任务。"""
        if self._run_task_status:
            self.log_print("监听到鼠标中键被按下,当前任务结束")
        self._run_task_status = False
        self._stop_run_task()

    def _init_game_windows_hwnd(self):
        """重新枚举游戏窗口并刷新界面。"""
        self._windows_hwnd_save.clear()

        windows_list = WindowsHandle().get_windows_handle()
        if not windows_list:
            self.log_print("未找到窗口...")
            self.windows_get.get_windows([])
            self.windows_get.push_button_run_windows.setEnabled(False)
            self.windows_get.push_button_test_windows.setEnabled(False)
            return

        self.windows_get.push_button_test_windows.setEnabled(True)
        self.windows_get.push_button_run_windows.setEnabled(True)
        for index, hwnd in enumerate(windows_list):
            self._windows_hwnd_save[f"窗口:{index + 1}"] = hwnd
        self.windows_get.get_windows(self._windows_hwnd_save.keys())

    def _get_windows_hwnd_list(self) -> list[int]:
        """返回当前勾选的窗口句柄。"""
        checked_names = self.windows_get.get_windows_checked()
        return [self._windows_hwnd_save[name] for name in checked_names
                if name in self._windows_hwnd_save]

    def test_hwnd(self):
        """依次激活勾选的窗口，用于确认前台切换是否正常。"""
        checked_list = self._get_windows_hwnd_list()
        if not checked_list:
            self.log_print("未勾选窗口...")
            return None

        for hwnd in checked_list:
            if is_window_capturable(hwnd):
                success, reason = WindowsHandle().activate_windows_ex(hwnd)
                time.sleep(0.2)
                if success:
                    self.log_print(f"窗口 {hwnd} 已激活")
                else:
                    self.log_print(f"窗口 {hwnd} 激活失败：{reason}")
                time.sleep(1)
            else:
                self.log_print(f"{hwnd} 未显示，请检查")
        return None

    def run_task(self):
        """执行或停止当前任务。"""
        task_enum = self.task_tab_windows.get_task_active()

        if self._run_task_status:
            self.log_print(f"任务 {task_enum.value} 停止执行...")
            self.windows_get.push_button_run_windows.setText("停止中...")
            self.windows_get.push_button_run_windows.setEnabled(False)
            self.toggle_global_mouse_monitoring(False)
            self._stop_run_task()
            return None

        checked_hwnd_list = self._get_windows_hwnd_list()
        if not checked_hwnd_list:
            self.log_print("请勾选需要执行的窗口")
            return False

        # BUFF 监控只需要截图；其余任务依赖幽灵键鼠发送按键
        if task_enum != TaskEnum.buff_monitor and not self._driver_ready:
            self.log_print("幽灵键鼠未就绪，当前任务无法执行")
            return None

        self.log_clear()
        self.log_print(f"任务 {task_enum.value} 开始执行...")

        # 切换到非 BUFF 任务时，隐藏上次监控遗留的状态面板
        if task_enum != TaskEnum.buff_monitor:
            self._buff_panel.set_overlay_mode(False)
            self._buff_panel.hide()

        task_started = False

        if task_enum == TaskEnum.dance_grey:
            self.qth_dance.init_task_param(checked_hwnd_list, dance_type="grey")
            self.qth_dance.start()
            task_started = True
        elif task_enum == TaskEnum.dance_green:
            self.qth_dance.init_task_param(checked_hwnd_list, dance_type="green")
            self.qth_dance.start()
            task_started = True
        elif task_enum == TaskEnum.open_gift:
            self.qth_open_gift.get_param(checked_hwnd_list)
            self.qth_open_gift.start()
            task_started = True
        elif task_enum == TaskEnum.map_goods_get:
            if len(checked_hwnd_list) > 1:
                self.log_print("地图采集暂时只支持一个游戏窗口，请去掉不需要的窗口")
                return None
            line_name = self.task_tab_windows.task_life_work.combo_box_goods_point_selected.currentText()
            try:
                map_point_list = get_map_goods_point_list_by_selected()
            except (OSError, ValueError) as exc:
                self.log_print(f"读取地图路线失败：{exc}")
                return None
            if not map_point_list:
                self.log_print(f"路线 {line_name} 没有坐标,请重新选择路线")
                return None
            self.qth_map_get.get_param(checked_hwnd_list[0], map_point_list)
            self.qth_map_get.start()
            task_started = True
        elif task_enum == TaskEnum.world_market:
            if len(checked_hwnd_list) > 1:
                self.log_print("世界竞拍暂时只支持控制一个游戏窗口!")
                return None
            product_list = self.task_tab_windows.task_other.widget_world_market.get_table_content()
            scan_product_num = int(
                self.task_tab_windows.task_other.widget_world_market
                .scan_product_num_select.currentText())
            self.qth_market.get_param(checked_hwnd_list[0], product_list, scan_product_num)
            self.qth_market.start()
            task_started = True
        elif task_enum == TaskEnum.challenge_point_2_book:
            if len(checked_hwnd_list) > 1:
                self.log_print("挑战点兑换暂时只支持控制一个游戏窗口!")
                return None
            self.qth_challenge.init_task_param(checked_hwnd_list[0])
            self.qth_challenge.start()
            task_started = True
        elif task_enum == TaskEnum.get_all_goods:
            self.qth_get_all_goods.get_param(checked_hwnd_list)
            self.qth_get_all_goods.start()
            task_started = True
        elif task_enum == TaskEnum.buff_monitor:
            if len(checked_hwnd_list) > 1:
                self.log_print("BUFF 监控暂时只支持一个游戏窗口，请去掉多余的窗口")
                return None
            self.qth_buff.init_task_param(checked_hwnd_list)
            # 面板无边框置顶并锁定到勾选的游戏窗口上方，执行中禁止拖动
            self._buff_panel.set_overlay_mode(True)
            self._buff_panel.bind_target_window(checked_hwnd_list[0])
            self._buff_panel.set_draggable(False)
            self.qth_buff.start()
            task_started = True
        else:
            self.log_print("请选择需要执行的任务")
            return None

        if task_started:
            self.toggle_global_mouse_monitoring(True)
            self._start_hwnd_alive_watch(checked_hwnd_list)
        return None

    def _start_hwnd_alive_watch(self, hwnd_list: list[int]) -> None:
        """记录本次任务的窗口句柄并启动存活监测。"""
        self._run_task_hwnd_list = list(hwnd_list)
        self._hwnd_alive_timer.start()

    def _stop_hwnd_alive_watch(self) -> None:
        """停止窗口存活监测并清空记录。"""
        self._hwnd_alive_timer.stop()
        self._run_task_hwnd_list = []

    def _check_task_windows_alive(self) -> None:
        """
        定时检查任务窗口是否全部失效。

        游戏窗口被关闭后句柄会失效，任务线程继续截图、点击就会空转甚至卡死；
        只要还有任意一个勾选窗口存活就继续任务，全部失效时主动结束任务。
        """
        if not self._run_task_hwnd_list:
            return
        if any(is_window_alive(hwnd) for hwnd in self._run_task_hwnd_list):
            return

        self._stop_hwnd_alive_watch()
        self.log_print("已勾选的游戏窗口全部关闭,任务自动结束")
        self.windows_get.push_button_run_windows.setText("停止中...")
        self.windows_get.push_button_run_windows.setEnabled(False)
        self._stop_run_task()

    def _stop_run_task(self):
        """停止所有任务线程。"""
        self._stop_hwnd_alive_watch()
        for thread in self._task_threads:
            thread.stop_execute_init()

    def _update_task_run_status(self, task_status: bool):
        """根据线程状态更新执行按钮和任务选项。"""
        # 任务执行中锁定面板位置，结束后恢复拖动
        self._buff_panel.set_draggable(not task_status)
        if task_status:
            self.windows_get.push_button_run_windows.setText("停止执行")
            self.windows_get.push_button_run_windows.setEnabled(True)
            self.status_bar.run_status(True)
            self._run_task_status = True
            self.task_tab_windows.update_radio_enable(False)
        else:
            self.windows_get.push_button_run_windows.setText("开始执行")
            self.windows_get.push_button_run_windows.setEnabled(True)
            self.status_bar.run_status(False)
            self._run_task_status = False
            self.task_tab_windows.update_radio_enable(True)
            # 任务自然结束时也要关闭中键监听，避免监听线程长期占用
            self.toggle_global_mouse_monitoring(False)
            # 任务结束（无论正常完成还是手动停止）都停止窗口存活监测
            self._stop_hwnd_alive_watch()
            # BUFF 监控结束后保持无边框叠加窗口，保留最后一份识别结果；
            # 拖动已在方法开头随任务状态恢复，这里不恢复系统标题栏
