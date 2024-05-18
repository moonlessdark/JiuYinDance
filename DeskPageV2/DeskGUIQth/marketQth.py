# coding: utf-8

import random
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import PicCapture
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.Utils.keyEvenQTAndGhost import qt_key_get_ghost_key_code

from DeskPageV2.DeskFindPic.findAuctionMarket import FindAuctionMarket


class MarKetQth(QThread):
    """
    世界竞拍
    """
    sin_out: Signal(str) = Signal(str)
    status_bar: Signal(str) = Signal(str)
    sin_work_status: Signal(bool) = Signal(bool)

    def __init__(self):
        super().__init__()

        self.__market_func = FindAuctionMarket()
        self.__market_windows_cap = WindowsCapture()

        self.__market_working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle = 0

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.__market_working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.__market_working = False
        self.windows_handle = 0

    @staticmethod
    def __min_price(goods_res: dict) -> dict:
        """
        拿出最小的产品，排除已经竞拍成功
        """
        __min_price = 0
        __min_goods = None

        for goods_key in goods_res:
            __goods = goods_res.get(goods_key)
            if __goods.get("goods_person_is_self") == 1:
                continue

            if __min_price == 0:
                __min_price = __goods.get("goods_price")

            if __goods.get("goods_price") <= __min_price:
                __min_price = __goods.get("goods_price")
                __min_goods = __goods
        return __min_goods

    def get_param(self, windows_handle: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.__market_working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁

        while 1:
            if self.__market_working is False:
                break
            __market_pic_contents: PicCapture = self.__market_windows_cap.capture_and_clear_black_area(
                self.windows_handle)
            time.sleep(1)
            __res: dict = self.__market_func.find_goods(__market_pic_contents.pic_content)
            if len(__res) > 0:
                __min_goods_res = self.__min_price(__res)
                if __min_goods_res is None:
                    time.sleep(1)
                    continue
                __goods_pic_pos = __min_goods_res["goods_pic_pos"]
                __goods_name = __min_goods_res["goods_name"]
                __goods_price = __min_goods_res["goods_price"]

                if self.windows_handle == 0:
                    break
                # 点击最低价的物品

                if self.windows_opt.activate_windows(self.windows_handle) is False:
                    continue
                __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle, coordinate=__goods_pic_pos)
                SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                SetGhostMouse().click_mouse_left_button()

                time.sleep(0.5)

                # 点击右侧的加价按钮
                __market_pic_contents: PicCapture = self.__market_windows_cap.capture_and_clear_black_area(
                    self.windows_handle)
                __plus_price_pos = self.__market_func.find_plus_price(__market_pic_contents.pic_content)
                __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle, coordinate=__plus_price_pos)
                SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                SetGhostMouse().click_mouse_left_button()

                time.sleep(0.5)
                # 判断“确认出价按钮是否高亮”
                __summit_pic_button_pos = self.__market_func.find_summit_price(self.__market_windows_cap.capture_and_clear_black_area(self.windows_handle).pic_content)
                if __summit_pic_button_pos is not None:
                    __plus_price_pos = self.__market_func.find_plus_price(__market_pic_contents.pic_content)
                    __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle,
                                                                      coordinate=__summit_pic_button_pos)
                    SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                    # SetGhostMouse().click_mouse_left_button()

            time.sleep(1)

        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
