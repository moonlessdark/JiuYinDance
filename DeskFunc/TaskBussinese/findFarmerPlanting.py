import time

import cv2
import numpy as np
from numpy import fromfile
from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from Utils.loadResources import GetConfig


def bitwise_and_seed(image_path: str):
    """
    给种子模板图片加个掩膜遮罩，避免干扰
    :param image_path: 图片路径
    """
    img_array = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # 获取图片尺寸
    height, width = img.shape[:2]

    # 创建掩码
    mask = np.zeros((height, width), dtype=np.uint8)

    # 定义两个点的坐标
    # 左侧点：(0, height * 0.9)
    left_y = int(height * 0.9)
    # 右侧点：(width, height * 0.6)
    right_y = int(height * 0.5)

    # 创建一个三角形区域，包含这条线以下的所有像素
    # 使用cv2.fillPoly填充多边形
    points = np.array([
        [0, height],  # 左下角
        [0, left_y],  # 左侧点
        [width, right_y],  # 右侧点
        [width, height]  # 右下角
    ], dtype=np.int32)

    # 填充多边形区域
    cv2.fillPoly(mask, [points], 255)

    # 应用掩码（将掩盖区域设为黑色）
    img_masked = img.copy()
    img_masked[mask == 255] = [0, 0, 0]  # 设置为黑色
    return img_masked


def bitwise_and_fertilizer(img_path: str):
    """
    给肥料图片加个掩膜遮罩，避免干扰
    :param img_path: 图片
    """
    img_array = np.fromfile(img_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # 获取图片尺寸
    height, width = img.shape[:2]

    # 创建掩码
    mask = np.zeros((height, width), dtype=np.uint8)

    # 计算右下角正方形区域的尺寸和位置
    square_size = int(min(height, width) * 0.38)  # 宽高1/4
    start_x = width - square_size  # 右侧起始x坐标
    start_y = height - square_size  # 下侧起始y坐标

    # 在掩码上标记右下角的正方形区域
    mask[start_y:start_y + square_size, start_x:start_x + square_size] = 255

    # 应用掩码（将掩盖区域设为黑色）
    img_masked = img.copy()
    img_masked[mask == 255] = [0, 0, 0]  # 设置为黑色
    return img_masked


def _load_pic(img_path: str):
    """
    加载图片
    :param img_path:
    :return:
    """
    return cv2.imdecode(fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)


class FindFarmerPlanting:

    def __init__(self):
        self._config = GetConfig().get_backpack_item_pic()  # 物品背包
        self._opt_status = GetConfig().get_goods_opt_status()  # 物品使用
        self.windows_opt = WindowsHandle()
        self.windows_find = FindWindowsImageTemplate()
        self.ocr = FindPicOCR()
        self.windows_capture = WindowsCapture()

        """
        加载一个图片
        """
        # 材料背包
        self._material_pic_bag_unclick = _load_pic(self._config.material_bag_tag_clickable)
        self._material_pic_bag_clicked = _load_pic(self._config.material_bag_tag_clicked)
        # 种子
        self.pic_item_seed = bitwise_and_seed(self._config.seed)  # 加个掩膜遮罩，避免干扰
        # 肥料
        self.pic_item_fertilizer = bitwise_and_fertilizer(self._config.fertilizer)  # 加个掩膜遮罩，避免干扰

        # 进度条和确定收货按钮
        self._goods_pic_open_loading = _load_pic(self._opt_status.open_loading)
        self._button_ok = _load_pic(self._opt_status.get_all_goods)

    def click_pos_left_mouse(self, hwnd: int, pos: tuple) -> bool:
        """
        鼠标左键点击一下坐标
        """
        if not self.windows_opt.activate_windows(hwnd):
            return False
        time.sleep(0.2)
        SetGhostMouse().move_mouse_to(pos[0], pos[1])
        time.sleep(0.1)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.1)
        return True

    def click_pos_right_mouse(self, hwnd: int, pos: tuple) -> bool:
        """
        鼠标右键点击一下坐标
        """
        if not self.windows_opt.activate_windows(hwnd):
            return False
        time.sleep(0.2)
        SetGhostMouse().move_mouse_to(pos[0], pos[1])
        time.sleep(0.1)
        SetGhostMouse().click_mouse_right_button()
        time.sleep(0.1)
        return True

    def find_fertilizer_backpack(self, hwnd: int) -> bool:
        """
        查询材料背包是否已经打开
        """
        for i in range(3):
            # 循环3次，避免出现被其他窗口遮挡的情况，最后一次可以显示出来
            for pic in [self._material_pic_bag_unclick, self._material_pic_bag_clicked]:
                pic_rec = self.windows_find.get_windows_image_rect(hwnd, read_image=pic)
                if pic_rec is None:
                    continue
                else:
                    # 如果当前找到的是未打物品栏的图标,那就点击一下
                    self.click_pos_left_mouse(hwnd, pic_rec)
                    return True
            # 按B，打开背包
            if not self.windows_opt.activate_windows(hwnd):
                return False
            time.sleep(1)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
            time.sleep(0.2)
        return False

    def check_fertilizer_in_bag(self, hwnd: int) -> bool:
        """
        查找肥料是否在背包内
        """
        _fertilizer_res: tuple = self.windows_find.get_windows_image_rect(hwnd, read_image=self.pic_item_fertilizer, edge=True, threshold=0.5)
        if _fertilizer_res is None:
            return False
        else:
            return True

    def check_seed_in_bag(self, hwnd: int) -> bool:
        """
        查找种子是否在背包内
        """
        _seed_res: tuple = self.windows_find.get_windows_image_rect(hwnd, read_image=self.pic_item_seed, edge=True, threshold=0.6)
        if _seed_res is None:
            return False
        else:
            return True

    def find_fertilizer_and_use(self, hwnd: int) -> bool:
        """
        查找肥料并使用
        """
        _fertilizer_res: tuple = self.windows_find.get_windows_image_rect_first_pos(hwnd, read_image=self.pic_item_fertilizer, edge=True, threshold=0.6)
        if _fertilizer_res is None:
            return False
        else:
            self.click_pos_right_mouse(hwnd, _fertilizer_res)
            return True

    def find_seed_and_use(self, hwnd: int) -> bool:
        """
        查找种子并使用
        """
        _seed_res: tuple = self.windows_find.get_windows_image_rect_first_pos(hwnd, read_image=self.pic_item_seed, edge=True, threshold=0.5)
        if _seed_res is None:
            return False
        else:
            self.click_pos_right_mouse(hwnd, _seed_res)
            return True

    def find_crops_pos(self, hwnd: int) -> bool:
        """
        查找农作物坐标
        如果出现了距离 ** 米，就说明鼠标所在的位置就是可以农作物了
        """
        pic = self.windows_capture.capture(hwnd)
        if pic is None:
            return False
        # 创建掩码
        # mask = np.zeros((pic.pic_height, pic.pic_width), dtype=np.uint8)
        #
        # # 计算左右边界
        # left_boundary = int(pic.pic_width * 0.3)  # 左侧30%
        # right_boundary = int(pic.pic_height * 0.7)  # 右侧70%
        #
        # # 在掩码上标记需要掩盖的区域（左侧0%-30% 和 右侧70%-100%）
        # mask[:, :left_boundary] = 255  # 左侧区域
        # mask[:, right_boundary:] = 255  # 右侧区域
        #
        # # 应用掩码（将掩盖区域设为黑色）
        # img_masked = pic.pic_content.copy()
        # # img_masked[mask == 255] = [0, 0, 0]  # 设置为黑色
        # black_pixel = np.full((img_masked.shape[2],), 0, dtype=np.uint8)
        # img_masked[mask == 255] = black_pixel

        pic_text_list: list = self.ocr.find_ocr_all(pic.pic_content)
        for pic_text_box in pic_text_list:
            line_text: str = pic_text_box.ocr_text
            if "距离" in line_text and "米" in line_text:
                return True
        return False

    def find_crops_mature(self, hwnd: int) -> bool:
        """
        农作物是否成功
        """
        pic = self.windows_capture.capture(hwnd)
        if pic is None:
            return False

        # # 创建掩码
        # mask = np.zeros((pic.pic_height, pic.pic_width), dtype=np.uint8)
        #
        # # 计算左右边界
        # left_boundary = int(pic.pic_width * 0.3)  # 左侧30%
        # right_boundary = int(pic.pic_height * 0.7)  # 右侧70%
        #
        # # 在掩码上标记需要掩盖的区域（左侧0%-30% 和 右侧70%-100%）
        # mask[:, :left_boundary] = 255  # 左侧区域
        # mask[:, right_boundary:] = 255  # 右侧区域
        #
        # # 应用掩码（将掩盖区域设为黑色）
        # img_masked = pic.pic_content.copy()
        # black_pixel = np.full((img_masked.shape[2],), 0, dtype=np.uint8)
        # img_masked[mask == 255] = black_pixel

        pic_text_list: list = self.ocr.find_ocr_all(pic.pic_content)
        for pic_text_box in pic_text_list:
            line_text: str = pic_text_box.ocr_text
            if "种植的" in line_text and "成熟" in line_text:
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

    def find_open_loading(self, hwnd: int):
        """
        查询打开状态
        """
        __rec_goods_bag_open_loading = self.windows_find.get_windows_image_rect(hwnd,
                                                                                read_image=self._goods_pic_open_loading,
                                                                                threshold=0.75)
        if __rec_goods_bag_open_loading is not None:
            return True
        return False
