import time

import cv2
import numpy as np
from numpy import fromfile

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import WindowsHandle
from DeskPageV2.Utils.dataClass import FindTruckCarTaskNPC, Team, TruckCarPic, TruckCarReceiveTask, Goods, MapPic
from DeskPageV2.Utils.load_res import GetConfig


def bitwise_and(image: np.ndarray):
    """
    给图片加个掩膜遮罩，避免干扰
    :param image: 图片
    :param mask_position: # 指定掩膜位置（左上角坐标， 右下角坐标） mask_position = (50, 50, 200, 200)
    """
    if image is not None:
        # 绘制掩膜（矩形）
        # 参数分别为：图像、矩形左上角坐标、矩形右下角坐标、颜色（BGR）、线条粗细
        return cv2.rectangle(image, (33, 29), (39, 38), (0, 255, 0), -1)
    return image


class FindGiftCard:

    def __init__(self):
        self._find_tag_goods = None  # 物品背包
        self._config = GetConfig().get_bag_goods()
        bu = GetConfig().get_track_car().receive_task_confirm
        self.windows = WindowsCapture()
        self._goods_pic_bag_unclick = cv2.imdecode(fromfile(self._config.goods_bag_tag_clickable, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self._goods_pic_bag_clicked = cv2.imdecode(fromfile(self._config.goods_bag_tag_clicked, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

        self._goods_pic_bag_gift_card = cv2.imdecode(fromfile(self._config.gift_card, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self._goods_pic_bag_gift_card = bitwise_and(self._goods_pic_bag_gift_card)

        self._button_ok = cv2.imdecode(fromfile(bu, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def open_bag(self, hwnd: int) -> bool:
        """
        获取物品背包
        """
        # 先检查一下包裹打开了没有
        __rec_goods_bag_tag_clicked = self.windows.find_windows_coordinate_rect(hwnd, img=self._goods_pic_bag_clicked)
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._goods_pic_bag_unclick)
        if __rec_goods_bag_tag_clicked is None and __rec_goods_bag_tag_clickable is None:
            # 包裹还没打开啊
            WindowsHandle().activate_windows(hwnd)
            time.sleep(0.5)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
            time.sleep(0.5)

        # 打开了，再检查一次
        __rec_goods_bag_tag_clicked = self.windows.find_windows_coordinate_rect(hwnd, img=self._goods_pic_bag_clicked)
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._goods_pic_bag_unclick)

        if __rec_goods_bag_tag_clicked is None and __rec_goods_bag_tag_clickable is not None:
            # 如果当前没有选中物品包裹栏
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            SetGhostMouse().click_mouse_left_button()
            time.sleep(0.5)

        if self.find_gift_card(hwnd):
            return True
        return False

    def find_gift_card(self, hwnd: int) -> bool:
        """
        找到第一个礼品卡(优先点击左上)
        """
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._goods_pic_bag_gift_card)
        if __rec_goods_bag_tag_clickable is not None:
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            return True
        return False

    def click_ok(self, hwnd: int):
        """
        点击确定按钮
        """
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._button_ok)
        if __rec_goods_bag_tag_clickable is not None:
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()
            return True
        return False
