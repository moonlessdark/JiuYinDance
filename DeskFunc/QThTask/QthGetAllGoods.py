import os
import time

import cv2
from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.commonOperations import CommonOperations
from Utils.FindWindowsImage import WindowsCapture, PicCapture
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse
from DeskFunc.TaskBussinese.openHiddenRealmItem import OpenHiddenRealmItems

class GetAllGoodsQth(QThread):
    """
    截图
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
        self.windows_handle_list = []

        self.opt = CommonOperations()
        self.func_open = OpenHiddenRealmItems()

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

    def get_param(self, windows_handle_list: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list

    @staticmethod
    def move_mouse(hwnd: int):
        """
        鼠标移动一下，避免挡住了包裹的图标
        """
        m_x, m_y = SetGhostMouse().get_mouse_x_y()
        w_point = coordinate_change_from_windows(hwnd, (m_x - 10, m_y - 10))
        SetGhostMouse().move_mouse_to(w_point[0], w_point[1])
        time.sleep(0.5)

    def run(self):
        self.mutex.lock()  # 先加锁
        self.sin_run_status.emit(True)  # 发送消息，人物开始

        _count: int = 0  # 执行数量
        while 1:
            if not self.working:
                break
            for hwnd in self.windows_handle_list:

                if not self.working:
                    break

                time.sleep(1)
                res: bool = self.opt.find_get_all_button(hwnd)
                if res:
                    _count += 1
                    self.move_mouse(hwnd)
                    time.sleep(1)

                self.status_bar.emit(_count)

                if self.func_open.find_cailiao_item_backpack(hwnd):
                    time.sleep(2)
                    self.move_mouse(hwnd)
                    continue

                time.sleep(1)

                if self.func_open.find_red_item_backpack(hwnd):
                    self.move_mouse(hwnd)
                    time.sleep(2)
                    continue

        self.sin_out.emit("自动获取结束")
        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()
        return None
