"""
连续开禁地包裹
"""
import time

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse
from Utils.dataClass import GoodsOptStatus
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



class OpenHiddenRealmItems:

    def __init__(self):
        self._config_opt: GoodsOptStatus = GetConfig().get_goods_opt_status()  # 获取物品使用
        self._config_item = GetConfig().get_backpack_item_pic()  # 物品背包
        self._windows_opt = WindowsHandle()
        self._windows_find = FindWindowsImageTemplate()
        self._windows_cap = WindowsCapture()

        _red_items_backpack = _load_pic(self._config_item.hidden_realm_item_package)
        self.red_item_backpack = bitwise_and(_red_items_backpack)
        self.cailiao_item_package = _load_pic(self._config_item.material_item_package)

    def mouse_click_pos(self, hwnd: int, move_pos: tuple, mouse_type: int) -> bool:
        """
        鼠标点击一下
        :param hwnd 句柄
        :param move_pos 需要移动的坐标(必须是经过Windows转换的)
        :param mouse_type 0-左键 1-右键 2-中键
        """
        if not self._windows_opt.activate_windows(hwnd):
            return False
        x, y = move_pos
        SetGhostMouse().move_mouse_to(x, y)
        time.sleep(0.1)
        if mouse_type == 0:
            SetGhostMouse().click_mouse_left_button()
        elif mouse_type == 1:
            SetGhostMouse().click_mouse_right_button()
        elif mouse_type == 2:
            SetGhostMouse().click_mouse_middle_button()
        else:
            # 如果鼠标类型不是0-1-2，那么就默认点击左键
            SetGhostMouse().click_mouse_left_button()
        time.sleep(0.3)  # 点击之后等待一下，给游戏窗口响应时间
        return True

    def find_red_item_backpack(self, hwnd: int):
        """
        寻找禁地物品包
        """
        res_point = self._windows_find.get_windows_image_rect(hwnd=hwnd, template_image=self.red_item_backpack)
        if res_point is None:
            return False
        self.mouse_click_pos(hwnd, res_point, mouse_type=1)
        return True

    def find_cailiao_item_backpack(self, hwnd: int):
        """
        寻找禁地物品包打开的材料包
        """
        res_point = self._windows_find.get_windows_image_rect(hwnd=hwnd, template_image=self.cailiao_item_package)
        if res_point is None:
            return False
        self.mouse_click_pos(hwnd, res_point, mouse_type=1)
        return True