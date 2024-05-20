# coding: utf-8
import difflib
import random
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import PicCapture
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList

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
        self.__market_goods_price: dict = {}

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

    def __check_goods_name_similarity(self, name_a: str):
        """
        检测2个物品名称的相似度
        """
        for key in self.__market_goods_price:
            for g_name in key:
                self.sin_out.emit(f"正在查询物品: {name_a} 是否已经设置最大价格，当前匹配值 {g_name}")
                ratio = difflib.SequenceMatcher(None, name_a, g_name).ratio()
                if round(ratio, 2) > 0.70:
                    self.sin_out.emit(f"已经找到物品: {g_name} 的最大价格 {key.get(g_name)}")
                    return key.get(g_name)
        self.sin_out.emit(f"没有找到物品: {name_a} 的最大价格")
        return None

    def __min_price(self, goods_res: dict) -> dict:
        """
        拿出最小的产品，排除已经竞拍成功
        """
        __min_price = 0
        __min_goods = None

        for goods_key in goods_res:
            __goods = goods_res.get(goods_key)
            if __goods.get("goods_person_is_self") == 1:
                self.sin_out.emit(f"检测到物品: {__goods.get('goods_name')} 已经加价成功，本次查询跳过此物品")
                # 过滤掉已经加价成功的
                continue

            _goods_price_temp: int = self.__check_goods_name_similarity(__goods.get("goods_name"))
            if _goods_price_temp is not None:
                self.sin_out.emit(f"物品: {__goods.get('goods_name')}(价格{int(__goods.get('goods_price'))})) 开始检测是否符合条件")
                # 拿出物品名字，和外面传进来的最大价格对比一下，如果超出了就跳过
                if int(__goods.get("goods_price")) >= int(_goods_price_temp):
                    # print(f"物品: {__goods.get('goods_name')}(当前价格{int(__goods.get('goods_price'))})(最大价格{_goods_price_temp}) 已经到达设置的最大上限")
                    self.sin_out.emit(f"物品: {__goods.get('goods_name')}(当前价格{int(__goods.get('goods_price'))})(最大价格{_goods_price_temp}) 已经到达设置的最大上限")
                    continue

                if __min_price == 0:
                    # 如果为0，就初始化一下
                    __min_price = __goods.get("goods_price")

                if __goods.get("goods_price") <= __min_price:
                    __min_price = __goods.get("goods_price")
                    __min_goods = __goods
        self.sin_out.emit(f"当前页面可以竞拍的价格最小的产品的价格是({__min_price})")
        # print(f"当前可以竞拍的价格最小的产品是 {__min_goods}(价格 {__min_price})")
        return __min_goods

    def get_param(self, windows_handle: int, goods_price_list: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.__market_working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle
        self.__market_goods_price: list = goods_price_list

    def run(self):
        self.mutex.lock()  # 先加锁

        while 1:
            if self.__market_working is False:
                break

            time.sleep(0.5)
            __market_pic_contents: PicCapture = self.__market_windows_cap.capture(self.windows_handle)

            if self.__market_func.check_in_follow_page(__market_pic_contents.pic_content) is False:
                self.sin_out.emit("关注的列表中已经没有物品，程序即将停止")
                break

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

                time.sleep(0.3)

                # 点击右侧的加价按钮
                __market_pic_contents: PicCapture = self.__market_windows_cap.capture(self.windows_handle)
                __plus_price_pos = self.__market_func.find_plus_price(__market_pic_contents.pic_content)
                __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle, coordinate=__plus_price_pos)
                SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                SetGhostMouse().click_mouse_left_button()

                time.sleep(0.3)
                # 判断“确认出价按钮是否高亮”
                __summit_pic_button_pos = self.__market_func.find_summit_price(
                    self.__market_windows_cap.capture(self.windows_handle).pic_content)
                if __summit_pic_button_pos is not None:
                    __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle,
                                                                      coordinate=__summit_pic_button_pos)
                    SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                    SetGhostMouse().click_mouse_left_button()

                time.sleep(0.2)

                if self.__market_func.check_in_follow_page(__market_pic_contents.pic_content) is False:
                    self.sin_out.emit("关注的列表中已经没有物品，程序即将停止")
                    break

                # 点击再次确认竞拍小窗口
                __re_summit_pic_button_pos = self.__market_func.find_re_summit_price(
                    self.__market_windows_cap.capture(self.windows_handle).pic_content)
                if __re_summit_pic_button_pos is not None:
                    __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle,
                                                                      coordinate=__re_summit_pic_button_pos)
                    SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                    SetGhostMouse().click_mouse_left_button()

            time.sleep(0.2)

        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None
