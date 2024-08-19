# coding: utf-8

import random
import time

import cv2

from DeskPageV2.DeskFindPic.findChengyuInput import ChengYuInput
from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import PicCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture


class ChengYuSearchQth(QThread):
    """
    成语填空
    """
    sin_out: Signal(list) = Signal(list)
    sin_out_non: Signal(str) = Signal(str)
    status_bar: Signal(str) = Signal(str)
    sin_work_status: Signal(bool) = Signal(bool)

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle: list = []

        self._chengyu = ChengYuInput()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False
        self.windows_handle = []

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def get_param(self, windows_handle: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle: list = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁
        if len(self.windows_handle) > 0:

            if self.working is False:
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None

            for windows_handle_id in self.windows_handle:
                _cap_content = WindowsCapture().capture(windows_handle_id).pic_content
                _chengyu_res: list = self._chengyu.check_chengyu(_cap_content)
                if len(_chengyu_res) > 0:
                    self.sin_out.emit(_chengyu_res)
                else:
                    self.sin_out_non.emit(f"窗口ID{windows_handle_id}未能成功识别到成语填空界面")
        self.mutex.unlock()  # 解锁
        self.sin_work_status.emit(False)
        return None


class ChengYuScreenGetQth(QThread):
    """
    获取成语
    """
    sin_out: Signal(list) = Signal(list)
    sin_out_non: Signal(str) = Signal(str)
    status_bar: Signal(str) = Signal(str)
    sin_work_status: Signal(bool) = Signal(bool)

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle: list = []

        self._chengyu = ChengYuInput()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False
        self.windows_handle: list = []

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def get_param(self, windows_handle: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle: list = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁
        if len(self.windows_handle) > 0:
            is_get: bool = False
            if self.working is False:
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None
            for windows_handle_s in self.windows_handle:
                _cap_content = WindowsCapture().capture(windows_handle_s).pic_content
                _chengyu_res, _chengyu_res_2 = self._chengyu.get_chengyu_string_key(_cap_content)
                _chengyu_res_new = list(set(_chengyu_res + _chengyu_res_2))
                if len(_chengyu_res_new) > 0:
                    self.sin_out.emit(_chengyu_res+_chengyu_res_2)
                    is_get = True
                    break
            if is_get is False:
                self.sin_out_non.emit(f"窗口未能成功识别到成语填空界面")
        self.mutex.unlock()  # 解锁
        self.sin_work_status.emit(False)
        return None
