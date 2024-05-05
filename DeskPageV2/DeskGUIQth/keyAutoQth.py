# coding: utf-8

import random
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.Utils.keyEvenQTAndGhost import qt_key_get_ghost_key_code


class AutoPressKeyQth(QThread):
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
        self.windows_handle = 0
        self.key_press_list: str = ""
        self.press_count: int = 0
        self.press_wait_time: int = 0

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
        self.windows_handle = 0

    def get_param(self, windows_handle: int, key_press_list: str, press_count: int, press_wait_time: float):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle
        self.key_press_list = key_press_list
        self.press_count = press_count
        self.press_wait_time = press_wait_time

    def run(self):
        self.mutex.lock()  # 先加锁
        key_code_list = qt_key_get_ghost_key_code(self.key_press_list)
        print(key_code_list)
        for count_i in range(self.press_count):
            if self.working is False:
                break
            wait_time: float = random.uniform(self.press_wait_time, self.press_wait_time + 2)
            time.sleep(round(wait_time, 2))
            if self.windows_opt.activate_windows(self.windows_handle):
                SetGhostBoards().click_all_press_and_release_by_key_code(key_code_list)
            self.sin_out.emit(f"已经执行了 {count_i + 1} 次按钮")
        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
