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
        while 1:
            if self.working is False:
                break
            now = datetime.datetime.now()
            if now.time() >= datetime.time(20, 59, 50) or now.time() >= datetime.time(21, 3, 50):
                for hwnd_i in self.windows_handle_list:
                    if self.find_gift_card.open_bag(hwnd_i) is False:
                        self.working = False
                        break
                break
                # self.sin_out.emit(f"准备开卡中")
            elif now.time() >= datetime.time(20, 59, 55) or now.time() >= datetime.time(21, 3, 55):
                self.sin_out.emit(f"开卡中")
                for hwnd_i in self.windows_handle_list:
                    self.windows_opt.activate_windows(hwnd_i)
                    time.sleep(0.2)
                    self.find_gift_card.find_gift_card(hwnd_i)
                    for run_i in range(50):
                        SetGhostMouse().click_mouse_right_button()
                        if self.find_gift_card.click_ok(hwnd_i):
                            self.sin_out.emit(f"窗口id:{hwnd_i}已开卡")
                            break
            else:
                self.sin_out.emit(f"等待到开卡时间")
        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
