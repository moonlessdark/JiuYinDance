import time

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from Utils.loadResources import GetConfig
from Utils.ImageUtils.FindImageOCR import FindPicOCR


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


def _load_pic(img_path: str) -> np.array:
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

        self._goods_pic_open_loading = _load_pic(self._opt_status.open_loading)
        self._button_ok = _load_pic(self._opt_status.get_all_goods)

        self.ocr = FindPicOCR()
        self.windows_cap = WindowsCapture()

    def click_pos(self, hwnd: int, pos: tuple) -> bool:
        """
        点击一下坐标
        """
        if not self.windows_opt.activate_windows(hwnd):
            return False
        time.sleep(0.2)
        SetGhostMouse().move_mouse_to(pos[0], pos[1])
        time.sleep(0.1)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.1)
        return True

    def find_backpack(self, hwnd: int) -> bool:
        """
        查询物品背包是否已经打开
        """
        for i in range(3):
            # 循环3次，避免出现被其他窗口遮挡的情况，最后一次可以显示出来


            clicked_pos = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._goods_pic_bag_clicked,
                threshold=0.85,
            )

            unclick_pos = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._goods_pic_bag_unclick,
                threshold=0.85,
            )

            # print(f"已点击：{clicked_pos}, 未点击:{unclick_pos}")

            if unclick_pos is not None and clicked_pos is not None:
                # print(1)
                # 如果当前2个状态都找到了，那么就说明是刚登录游戏，背包还是默认状态，所以此时我就认为你还没有点击背包，需要点一下
                # 根据实测，这个方法进不来，但是保险起见还是留着吧
                self.click_pos(hwnd, unclick_pos)
                time.sleep(0.5)
                return False

            if clicked_pos is not None:
                # print(2)
                # 如果当前找到的是已打物品栏的图标,那就返回
                return True

            if unclick_pos is not None:
                # print(3)
                # 如果当前找到的是未打物品栏的图标,那就点击一下
                self.click_pos(hwnd, unclick_pos)
                return True
            # print(4)
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
        __rec_goods_bag_tag_clickable = self.windows_find.get_windows_image_rect(hwnd, read_image=self._goods_pic_bag_gift_card)
        if __rec_goods_bag_tag_clickable is not None:
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            return True
        return False

    def click_ok(self, hwnd: int):
        """
        点击确定按钮
        """
        __rec_goods_bag_tag_clickable = self.windows_find.get_windows_image_rect(hwnd, read_image=self._button_ok, threshold=0.5, edge=True)
        if __rec_goods_bag_tag_clickable is not None:
            self.windows_opt.activate_windows(hwnd)
            time.sleep(0.5)
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            SetGhostMouse().click_mouse_left_button()
            return True
        return False

    def click_get_all(self, hwnd: int):
        """
        拾取所有操作
        """
        pic = self.windows_cap.capture(hwnd)
        if pic is not None:
            text_rec = self.ocr.find_ocr(pic.pic_content, "全部拾取")
            if text_rec is not None:
                self.windows_opt.activate_windows(hwnd)
                time.sleep(0.5)
                _p: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=tuple(text_rec))
                SetGhostMouse().move_mouse_to(_p[0], _p[1])
                SetGhostMouse().click_mouse_left_button()
                return True
        return None

    @staticmethod
    def find_progress_bar_by_color(roi):
        """
        检测颜色
        """
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))

        # 1. 检查是否存在连续长条
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > h * 3 and w > 80:  # 长条且足够长
                # print("长度 ", w)
                return True
        return  False

    def find_progress_bar_by_template(self, roi):
        """
        使用模板匹配查找进度条
        :param roi: 待检测区域
        :return: 是否找到进度条
        """
        result = cv2.matchTemplate(roi, self._goods_pic_open_loading, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # print("max_val:", max_val)
        if max_val > 0.8:
            return True
        return False

    def find_open_loading(self, hwnd: int):
        """
        查询打开状态
        """

        cap = self.windows_cap.capture(hwnd)
        cap_content = cap.pic_content[
            int(cap.pic_height * 0.5):int(cap.pic_height * 0.9),  # 高度范围
            int(cap.pic_width * 0.3):int(cap.pic_width * 0.7)  # 宽度范围
        ]
        # 方法1：结构特征（上下边框）
        color_bool: bool = self.find_progress_bar_by_color(cap_content)
        template_bool: bool = self.find_progress_bar_by_template(cap_content)
        # 方法2：模板匹配（备用）
        if color_bool and template_bool:
            # print("正在打开中...")
            # cv2.imshow("进度条", cap_content)
            # cv2.waitKey(0)
            return True
        return False
