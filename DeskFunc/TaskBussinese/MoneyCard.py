import time

import cv2
import numpy as np
from numpy import fromfile

from DeskFunc.TaskBussinese.commonOperations import CommonOperations
from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards
from Utils.loadResources import GetConfig


def bitwise_and(image: np.ndarray):
    """
    给图片加个掩膜遮罩，避免干扰
    :param image: 图片
    """
    if image is not None:
        # 绘制掩膜（矩形）
        # 参数分别为：图像、矩形左上角坐标、矩形右下角坐标、颜色（BGR）、线条粗细
        return cv2.rectangle(image, (33, 29), (39, 38), (0, 255, 0), -1)
    return image


def _load_pic(img_path: str) -> np.ndarray:
    """
    加载图片
    :param img_path:
    :return:
    """
    return cv2.imdecode(fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)


class FindGiftCard:

    def __init__(self):
        self._config = GetConfig().get_backpack_item_pic()  # 物品背包
        self._opt_status = GetConfig().get_goods_opt_status()  # 物品使用
        self.windows_opt = WindowsHandle()
        self.windows_find = FindWindowsImageTemplate()

        self._goods_pic_bag_unclick = _load_pic(self._config.goods_bag_tag_clickable)
        self._goods_pic_bag_clicked = _load_pic(self._config.goods_bag_tag_clicked)

        self._goods_pic_bag_gift_card = _load_pic(self._config.gift_card)
        self._goods_pic_bag_gift_card = bitwise_and(self._goods_pic_bag_gift_card)

        self.common_options = CommonOperations()  # 通用操作

        self.windows_cap = WindowsCapture()

    def find_backpack(self, hwnd: int) -> bool:
        """
        查询物品背包是否已经打开
        """
        for i in range(3):
            # 循环3次，避免出现被其他窗口遮挡的情况，最后一次可以显示出来


            clicked_pos = self.windows_find.get_windows_image_rect(
                hwnd,
                template_image=self._goods_pic_bag_clicked,
                threshold=0.85,
            )

            unclick_pos = self.windows_find.get_windows_image_rect(
                hwnd,
                template_image=self._goods_pic_bag_unclick,
                threshold=0.85,
            )

            if unclick_pos is not None and clicked_pos is not None:
                # 如果当前2个状态都找到了，那么就说明是刚登录游戏，背包还是默认状态，所以此时我就认为你还没有点击背包，需要点一下
                # 根据实测，这个方法进不来，但是保险起见还是留着吧
                self.common_options.mouse_click_pos(hwnd, clicked_pos, 0)
                time.sleep(0.5)
                return False

            if clicked_pos is not None:
                # 如果当前找到的是已打物品栏的图标,那就返回
                return True

            if unclick_pos is not None:
                # 如果当前找到的是未打物品栏的图标,那就点击一下
                self.common_options.mouse_click_pos(hwnd, unclick_pos, 0)
                return True
            # 如果压根没有打开包裹，按B，打开背包
            if not self.windows_opt.activate_windows(hwnd):
                return False
            time.sleep(0.2)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
            time.sleep(0.2)
        return False

    def find_gift_card(self, hwnd: int) -> bool:
        """
        找到第一个礼品卡(优先点击左上)
        """
        gift_card_pos: tuple = self.windows_find.get_windows_image_rect(hwnd,
                                                                        template_image=self._goods_pic_bag_gift_card,
                                                                        result_type=1)
        if gift_card_pos is None:
            return False
        return self.common_options.mouse_click_pos(hwnd, gift_card_pos, 1)

    def click_get_all(self, hwnd: int) -> bool:
        """
        拾取所有操作
        """
        return self.common_options.find_get_all_button(hwnd)

    def find_open_loading(self, hwnd: int) -> bool:
        """
        查询打开状态
        """
        return self.common_options.find_open_loading(hwnd)
