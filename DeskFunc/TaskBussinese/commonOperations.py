"""
放一些通用的操作，会有很多地方用到的
目前有:
1、进度条
2、获取全部
"""
import time

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture, PicCapture
from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse
from Utils.dataClass import GoodsOptStatus
from Utils.loadResources import GetConfig


class CommonOperations:
    """
    游戏中的一些通用操作，在这里抽出来避免在其他任务中重复实现
    """
    def __init__(self):
        self._config: GoodsOptStatus = GetConfig().get_goods_opt_status()  # 获取物品使用
        self._windows_opt = WindowsHandle()
        self._windows_find = FindWindowsImageTemplate()
        self._ocr = FindPicOCR()
        self._windows_cap = WindowsCapture()

    @staticmethod
    def _load_pic(img_path: str) -> np.ndarray:
        """
        加载图片
        :param img_path:
        :return:
        """
        return cv2.imdecode(fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

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

    def _find_loading_bar_by_template(self, image: np.ndarray) -> bool:
        """
        查找进度条：通过模板匹配
        """
        loading_bar_pos: list = self._windows_find.get_windows_image_area(bigger_img=image,
                                                                           smaller_pic=self._load_pic(self._config.open_loading),
                                                                           threshold=0.7,
                                                                           to_gray=False)
        if loading_bar_pos is None:
            return False
        return True


    def _find_loading_bar_by_template_to_gray(self, image: np.ndarray) -> bool:
        """
        查找进度条：通过模板匹配
        """
        loading_bar_pos: list = self._windows_find.get_windows_image_area(bigger_img=image,
                                                                           smaller_pic=self._load_pic(self._config.open_loading),
                                                                           threshold=0.7,
                                                                           to_gray=True)
        if loading_bar_pos is None:
            return False
        return True


    def find_open_loading(self, hwnd: int) -> bool:
        """
        查询进度条是否出现
        """
        # 方法1：结构特征（上下边框）
        cap = self._windows_cap.capture(hwnd)
        cap_content = cap.pic_content[int(cap.pic_height * 0.5):int(cap.pic_height * 0.9),  # 高度范围
                                      int(cap.pic_width * 0.3):int(cap.pic_width * 0.7)]  # 宽度范围
        template_bool: bool = self._find_loading_bar_by_template(cap_content)
        template_bool_gray: bool = self._find_loading_bar_by_template_to_gray(cap_content)
        if template_bool or template_bool_gray:
            print(f"找到了进度条,模板:{template_bool}, 模板(灰色): {template_bool_gray}")
            return True
        return False


    def _find_get_all_button_pic(self, hwnd: int) -> bool:
        """
        查找“获取全部”按钮：通过模板匹配
        """
        get_all_button_pos: tuple = self._windows_find.get_windows_image_rect(hwnd,
                                                                              template_image=self._load_pic(self._config.get_all_goods),
                                                                              threshold=0.85,
                                                                              to_gray= False)
        if get_all_button_pos is None:
            return False

        return self.mouse_click_pos(hwnd, get_all_button_pos, 0)

    def _find_get_all_button_ocr(self, hwnd: int) -> bool:
        """
        查找“获取全部”按钮：通过OCR识别
        """
        cap: PicCapture = self._windows_cap.capture(hwnd)
        if cap is None:
            return False
        get_all_button_pos: list = self._ocr.find_ocr(cap.pic_content, "全部拾取")
        if get_all_button_pos is None:
            return False
        return self.mouse_click_pos(hwnd, tuple(get_all_button_pos), 0)

    def find_get_all_button(self, hwnd: int) -> bool:
        """
        查询“获取全部”按钮是否出现
        """
        # 方法1：模板匹配
        if self._find_get_all_button_pic(hwnd):
            # print("找到了获取全部的模板")
            return True
        # 方法2：OCR识别
        if self._find_get_all_button_ocr(hwnd):
            # print("找到了获取全部的OCR")
            return  True
        return False
