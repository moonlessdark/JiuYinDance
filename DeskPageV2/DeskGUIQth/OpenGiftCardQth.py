# coding: utf-8
import datetime
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex
from sympy import Interval

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostMouse
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
        _is_wait: bool = False  # False 表示这一轮已经执行，等待下一轮  True 真在在执行中

        while 1:
            if self.working is False:
                break

            now = datetime.datetime.now()
            # 计算到21点整还有多久
            if now in [datetime.datetime(now.year, now.month, now.day, 20, 59, 55),
                       datetime.datetime(now.year, now.month, now.day, 20, 59, 56),
                       datetime.datetime(now.year, now.month, now.day, 21, 3, 55),
                       datetime.datetime(now.year, now.month, now.day, 21, 3, 56)]:  # 如果已经过了21点，则设置为明天的21点

                # 先把背包打开,并检查是否有礼卡，如果包裹里没有礼卡的花那就没啥意义了啊
                for hwnd_i in self.windows_handle_list:
                    if self.find_gift_card.open_bag(hwnd_i) is False:
                        # 如果包裹里没有礼卡
                        continue
                    _is_ready_hwnd.append(hwnd_i)

                if len(_is_ready_hwnd) == len(_is_ok_hwnd):
                    # 如果，所有的窗口都没有检测到礼卡，那么就可以跳出去了，没有意义
                    # 如果所有的窗口已经检测完成了，那么就可以跳出去了，没有意义
                    _is_ready_hwnd = []
                    _is_ok_hwnd = []
                    break

                for _read_hwnd in _is_ready_hwnd:
                    if _read_hwnd in _is_ok_hwnd:
                        continue
                    self.windows_opt.activate_windows(_read_hwnd)
                    time.sleep(0.2)
                    self.find_gift_card.find_gift_card(_read_hwnd)
                    for run_i in range(50):
                        SetGhostMouse().click_mouse_right_button()
                        if self.find_gift_card.click_ok(_read_hwnd):
                            self.sin_out.emit(f"窗口id:{_read_hwnd}已开卡")
                            _is_ok_hwnd.append(_read_hwnd)
                            break

            else:
                self.sin_out.emit(f"等待到开卡时间")
            time.sleep(1)
        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
