import os
import time

import cv2
from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex
from DeskFunc.TaskBussinese.findAuctionMarket import FindAuctionMarket
from Utils.FindWindowsImage import WindowsCapture, PicCapture


class WorldMarketGetGoodsQth(QThread):
    """
    世界竞拍,获取商品
    """
    sin_out = Signal(list)
    status_information = Signal(int)
    sin_run_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
        self.windows_handle: int = 0
        self.func = FindAuctionMarket()

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

    def get_param(self, windows_handle: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁
        self.sin_run_status.emit(True)  # 发送消息，人物开始

        while self.working:
            if not self.working:
                break

            cap_img: PicCapture = self.windows_cap.capture(self.windows_handle)
            if cap_img is None:
                self.working = False
                self.status_information.emit("未检测到竞拍关注列表的商品")

            _goods_list = self.func.find_goods_list(cap_img.pic_content)
            self.sin_out.emit(_goods_list)
            self.working = False

        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()
