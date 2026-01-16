import time

import cv2
import numpy as np
from numpy import fromfile

from DeskFunc.TaskBussinese.commonOperations import CommonOperations
from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse
from Utils.loadResources import GetConfig


def _load_pic(img_path: str) -> np.ndarray:
    """
    加载图片
    :param img_path:
    :return:
    """
    return cv2.imdecode(fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)


class ChangePoint2LuckyMoney:

    def __init__(self):
        self.windows_opt = WindowsHandle()
        self.windows_find = FindWindowsImageTemplate()
        pic_template = GetConfig().get_change_2_lucky_money()  # 所有用得到的图标模板

        self.pic_challenge_point_shop_book = _load_pic(pic_template.challenge_point_shop_book)  # 夺魄的列表
        self.pic_challenge_point_book_page = _load_pic(pic_template.challenge_point_book_page)  # 技能书页
        self.pic_challenge_point_exchange_button = _load_pic(pic_template.challenge_point_exchange_button)  # 兑换书页的按钮
        self.pic_backpack_item_pic = _load_pic(pic_template.backpack_item_pic)  # 背包中的夺魄书页
        self.pic_recycle_box = _load_pic(pic_template.recycle_box)  # 兑换窗口
        self.pic_recycle_box_result = _load_pic(pic_template.recycle_box_result)  # 兑换结果预览
        self.pic_exchange_ok = _load_pic(pic_template.exchange_ok)  # 兑换按钮
        self.pic_exchange_re_ok = _load_pic(pic_template.exchange_re_ok)  # 二次确认

        self.common_options = CommonOperations()  # 通用操作


    def _activity_and_click(self, res_point: tuple, hwnd: int):
        return self.common_options.mouse_click_pos(hwnd, res_point, 0)

    def find_change_point_shop_book(self, hwnd: int) -> bool:
        """
        查找夺魄的列表点击了没有
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_challenge_point_shop_book, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_change_point_book_page(self, hwnd: int) -> bool:
        """
        查找技能书页
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_challenge_point_book_page, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_change_point_exchange_button(self, hwnd: int) -> bool:
        """
        查找技能书页的兑换按钮
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_challenge_point_exchange_button,
                                                             threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return True

    def find_backpack_item_pic(self, hwnd: int) -> bool:
        """
        查找背包中的夺魄书页
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_backpack_item_pic, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_recycle_box(self, hwnd: int) -> bool:
        """
        查找兑换窗口
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_recycle_box, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_recycle_box_result(self, hwnd: int) -> bool:
        """
        查找兑换结果
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_recycle_box_result, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_exchange_ok(self, hwnd: int) -> bool:
        """
        查找二次确认
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_exchange_ok, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def find_exchange_re_ok(self, hwnd: int) -> bool:
        """
        查找二次确认
        :param hwnd:
        :return:
        """
        res: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_exchange_re_ok, threshold=0.9)
        if res is not None:
            return self._activity_and_click(res, hwnd)
        return False

    def check_pic_template_exist(self, hwnd: int) -> int:
        """
        检查图片模板是否存在
        :param hwnd:
        :return: -1: 未找到技能书页
                 -2: 未找到兑换窗口
                 0: 一切正常
        """
        res_book_page: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_challenge_point_book_page, threshold=0.9)
        res_recycle: tuple = self.windows_find.get_windows_image_rect(hwnd, self.pic_recycle_box, threshold=0.9)
        if res_book_page is None:
            return -1
        if res_recycle is None:
            return -2
        return 0

