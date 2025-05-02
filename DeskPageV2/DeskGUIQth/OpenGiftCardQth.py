# coding: utf-8
import datetime
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.DeskFindPic.findCard import FindGiftCard


class OpenGiftCard(QThread):
    """
    键盘连点器
    """
    sin_out: Signal(str) = Signal(str)
    status_bar: Signal(str) = Signal(str)
    sin_work_status: Signal(bool) = Signal(bool)

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle_list = []
        self.key_press_list: str = ""
        self.press_count: int = 0
        self.press_wait_time: int = 0

        self.find_gift_card = FindGiftCard()
        self.mouse = SetGhostMouse()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

    @staticmethod
    def check_local_time() -> bool:
        # 获取当前时间并去除微秒
        current_time = datetime.datetime.now().replace(microsecond=0)
        # 定义目标时间字符串列表
        target_times: list = ["20:59:55", "21:03:55"]

        # 转换为datetime对象并生成时间范围（前后2秒）
        time_ranges = []
        for t in target_times:
            target = datetime.datetime.strptime(t, "%H:%M:%S").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            time_ranges.append((target - datetime.timedelta(seconds=2), target + datetime.timedelta(seconds=2)))

        # 判断当前时间是否落入任一区间
        match_flag: bool = False
        for start, end in time_ranges:
            if start <= current_time <= end:
                match_flag = True
                break
        return match_flag

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle_list = 0

    def get_param(self, windows_handle_list: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list

    def run(self):
        self.mutex.lock()  # 先加锁

        _is_ready_hwnd: list = []
        _is_ok_hwnd: list = []

        while 1:
            if self.working is False:
                break

            # 计算到21点整还有多久
            if self.check_local_time() is False:
                # 如果还没有到21点
                time.sleep(1)
                continue

            # 先把背包打开,并检查是否有礼卡，如果包裹里没有礼卡的花那就没啥意义了啊
            for hwnd_i in self.windows_handle_list:
                if self.find_gift_card.open_bag(hwnd_i) is False:
                    # 如果包裹里没有礼卡
                    continue
                if hwnd_i not in _is_ready_hwnd:
                    _is_ready_hwnd.append(hwnd_i)

            if len(_is_ready_hwnd) == len(_is_ok_hwnd) and len(_is_ready_hwnd) > 0:
                # 如果，所有的窗口都没有检测到礼卡，那么就可以跳出去了，没有意义
                # 如果所有的窗口已经检测完成了，那么就可以跳出去了，没有意义

                for is_ok_h in _is_ok_hwnd:
                    # 如果有“获取全部”的按钮的话，那么就全部关掉吧
                    self.find_gift_card.click_ok(is_ok_h)

                _is_ready_hwnd = []
                _is_ok_hwnd = []

                continue

            for _read_hwnd in _is_ready_hwnd:

                if self.working is False:
                    break

                if _read_hwnd in _is_ok_hwnd:
                    continue
                self.windows_opt.activate_windows(_read_hwnd)
                time.sleep(0.2)
                if self.find_gift_card.find_gift_card(_read_hwnd) is False:
                    continue

                _index_x, _index_y = 0, 0
                for run_i in range(10):

                    if self.working is False:
                        break

                    # 检测一些鼠标的位置，如果人为移动的鼠标，那说明有突发情况，需要停止
                    x, y = SetGhostMouse().get_mouse_x_y()
                    if _index_x == 0 and _index_y == 0:
                        _index_x, _index_y = x, y
                    elif x != _index_x or y != _index_y:
                        self.sin_out.emit(f"发现鼠标移动,或许有突发情况，停止开卡")
                        self.working = False
                        break

                    SetGhostMouse().click_mouse_right_button()
                    if self.find_gift_card.find_open_loading(_read_hwnd):
                        self.sin_out.emit(f"窗口id:{_read_hwnd}已开卡,请结束后自行查看开卡记录")
                        if _read_hwnd not in _is_ok_hwnd:
                            _is_ok_hwnd.append(_read_hwnd)
                        w_point = coordinate_change_from_windows(_read_hwnd, (10, 10))
                        SetGhostMouse().move_mouse_to(w_point[0], w_point[1])  # 鼠标移动一下，避免挡住了包裹的图标
                        break
                    time.sleep(0.1)
            if len(_is_ready_hwnd) == len(_is_ok_hwnd) and len(_is_ready_hwnd) > 0:
                # 如果，所有的窗口都没有检测到礼卡，那么就可以跳出去了，没有意义
                # 如果所有的窗口已经检测完成了，那么就可以跳出去了，没有意义

                for is_ok_h in _is_ok_hwnd:
                    # 如果有“获取全部”的按钮的话，那么就全部关掉吧
                    self.find_gift_card.click_ok(is_ok_h)

                _is_ready_hwnd = []
                _is_ok_hwnd = []
                continue

        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
