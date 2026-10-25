# coding: utf-8
"""
截图与坐标的统一入口（视觉层）。

业务层只应该通过本模块获取图片和坐标，不再直接调用 WindowsCapture / win32gui：
1. 截图、客户区可见性判断集中在一处，后续换截图方式只需要改这里；
2. 比例 ROI 裁剪在这里完成，业务层不再手写 pic_content[a:b, c:d]；
3. 客户区坐标转屏幕坐标统一走 Core.windows.geometry，避免漏转换。
"""
from __future__ import annotations

from typing import Optional, Union

import numpy as np

from Core.vision.target import RatioRect
from Core.vision.template import find_all_template, load_template
from Core.windows.capture import PicCapture, WindowsCapture
from Core.windows.geometry import client_to_screen
from Core.windows.window import activate_windows, is_window_capturable

TemplateImage = Union[np.ndarray, str]


def resolve_template(template_image: TemplateImage) -> Optional[np.ndarray]:
    """
    将模板参数统一成 ndarray。

    :param template_image: ndarray 或图片路径
    :return: 模板图片；路径无效时返回 None
    """
    if template_image is None:
        return None
    if isinstance(template_image, str):
        return load_template(template_image)
    return template_image


def sort_match_result(match_result: list, result_type: int) -> list:
    """
    按指定规则排序匹配结果。

    result_type:
        0 - 置信度降序
        1 - 左上角 X 坐标升序
        2 - 先 Y 后 X 升序
    """
    if result_type == 0:
        match_result.sort(key=lambda item: item["confidence"], reverse=True)
    elif result_type == 1:
        match_result.sort(key=lambda item: item["result"][0])
    elif result_type == 2:
        match_result.sort(key=lambda item: (item["result"][1], item["result"][0]))
    else:
        raise ValueError("result_type参数错误")
    return match_result


class ScreenSource:
    """
    游戏窗口的截图源。

    本类无状态，可以被多个任务共享；截图结果的生命周期由调用方管理。
    """

    def __init__(self):
        self._capture = WindowsCapture()

    def capture(self, hwnd: int) -> Optional[PicCapture]:
        """
        截取整个客户区。

        :param hwnd: 游戏窗口句柄
        :return: 截图结果；窗口不可见、最小化或截图失败时返回 None
        """
        if hwnd is None:
            return None
        return self._capture.capture(hwnd)

    @staticmethod
    def is_visible(hwnd: int) -> bool:
        """判断窗口是否可以截图（存在、可见、非最小化）。"""
        return is_window_capturable(hwnd)

    @staticmethod
    def activate(hwnd: int) -> bool:
        """激活窗口。"""
        return activate_windows(hwnd)

    @staticmethod
    def crop_ratio(pic: PicCapture, roi: RatioRect) -> Optional[tuple[np.ndarray, tuple[int, int]]]:
        """
        按比例裁剪截图。

        :param pic: 完整客户区截图
        :param roi: 比例区域，通常来自 TargetSpec.roi
        :return: (裁剪后的图片, (裁剪区域左上角在客户区中的 x, y))；
                 截图为空或区域非法时返回 None
        """
        if pic is None or pic.pic_content is None:
            return None

        left, top, right, bottom = roi.to_box(pic.pic_width, pic.pic_height)
        if right <= left or bottom <= top:
            return None

        image = pic.pic_content[top:bottom, left:right]
        if image.size == 0:
            return None
        return image, (left, top)

    @staticmethod
    def to_screen(hwnd: int, point: tuple[float, float]) -> tuple[int, int]:
        """
        把客户区坐标转换为屏幕坐标，供鼠标点击使用。

        :param hwnd: 游戏窗口句柄
        :param point: 客户区坐标 (x, y)
        :return: 屏幕坐标 (x, y)
        """
        return client_to_screen(hwnd, point)


class FindWindowsImageTemplate:
    """
    在游戏窗口截图中查找模板，并把结果转换为屏幕坐标。

    这是业务层使用的稳定接口，内部实现已迁移到 Core：
    - 截图走 Core.windows.capture；
    - 模板匹配走 Core.vision.template；
    - 坐标转换走 Core.windows.geometry（ClientToScreen，不再推算窗口边框）。
    """

    def __init__(self):
        self._windows_cap = WindowsCapture()

    def get_windows_image_rect(self, hwnd: int, template_image: TemplateImage,
                               threshold: float = 0.7,
                               max_cnt: int = 0,
                               auto_scale: tuple[float, float, float] = None,
                               edge: bool = False,
                               to_gray: bool = True,
                               result_type: int = 0,
                               coordinate_change_to_windows: bool = True,
                               region: tuple[int, int, int, int] = None) -> Optional[tuple]:
        """
        查询图标模板在游戏窗口中的匹配度最高的坐标，并映射为屏幕坐标。

        :param hwnd: 窗口句柄
        :param template_image: 模板，支持 ndarray 或图片路径
        :param threshold: 匹配度 0 - 1
        :param max_cnt: 最大匹配数量
        :param auto_scale: 是否需要缩放，格式 (min_scale, max_scale, step)
        :param edge: 是否先做边缘提取
        :param to_gray: 是否转灰度匹配
        :param result_type: 0-匹配度最高；1-最靠左；2-最靠上
        :param coordinate_change_to_windows: 是否转换为屏幕坐标
        :param region: 只在客户区的指定区域匹配 (x, y, width, height)
        :return: None 或 (x, y)
        """
        template = resolve_template(template_image)
        if template is None:
            return None

        capture: Optional[PicCapture] = self._windows_cap.capture(hwnd)
        if capture is None:
            return None

        source_image = capture.pic_content
        offset_x, offset_y = 0, 0
        if region is not None:
            region_x, region_y, region_width, region_height = region
            if region_width <= 0 or region_height <= 0:
                return None
            source_image = source_image[region_y:region_y + region_height,
                                        region_x:region_x + region_width]
            if source_image.size == 0:
                return None
            offset_x, offset_y = region_x, region_y

        match_result = find_all_template(im_source=source_image, im_template=template,
                                         threshold=threshold,
                                         edge=edge,
                                         max_cnt=max_cnt,
                                         auto_scale=auto_scale,
                                         to_gray=to_gray)
        if not match_result:
            return None

        match_result = sort_match_result(match_result, result_type)
        coordinate_x, coordinate_y = match_result[0]["result"]
        coordinate_x += offset_x
        coordinate_y += offset_y

        if coordinate_change_to_windows:
            coordinate_x, coordinate_y = client_to_screen(hwnd, (coordinate_x, coordinate_y))
        return coordinate_x, coordinate_y

    @staticmethod
    def get_windows_image_all_rect(source_image: np.ndarray, template_image: TemplateImage,
                                   threshold: float = 0.7,
                                   edge: bool = False,
                                   max_cnt: int = 0,
                                   auto_scale: tuple[float, float, float] = None,
                                   to_gray: bool = True,
                                   coordinate_change_to_windows: bool = True,
                                   hwnd: int = None,
                                   use_alpha_mask: bool = False) -> Optional[list]:
        """
        查询所有相似度匹配的坐标。

        :param source_image: 原图（客户区截图或已裁剪的局部图）
        :param template_image: 模板，支持 ndarray 或图片路径
        :param threshold: 相似度
        :param edge: 是否先做边缘提取
        :param max_cnt: 最大匹配数量
        :param auto_scale: 是否需要缩放匹配
        :param to_gray: 是否转灰度
        :param coordinate_change_to_windows: 是否转换为屏幕坐标
        :param hwnd: 窗口句柄，用于坐标转换
        :param use_alpha_mask: 是否按 alpha 通道做透明模板匹配
        :return: None 或 [(x1, y1), (x2, y2)]
        """
        template = resolve_template(template_image)
        if template is None or source_image is None:
            return None

        match_result = find_all_template(im_source=source_image, im_template=template,
                                         threshold=threshold,
                                         edge=edge,
                                         max_cnt=max_cnt,
                                         auto_scale=auto_scale,
                                         to_gray=to_gray,
                                         use_alpha_mask=use_alpha_mask)
        if not match_result:
            return None

        img_result = []
        for result in match_result:
            coordinate_x, coordinate_y = result["result"]
            if coordinate_change_to_windows and hwnd is not None:
                coordinate_x, coordinate_y = client_to_screen(hwnd, (coordinate_x, coordinate_y))
            img_result.append((coordinate_x, coordinate_y))
        return img_result

    @staticmethod
    def get_windows_image_area(bigger_img: np.ndarray, smaller_pic: TemplateImage,
                               threshold: float = 0.7,
                               edge: bool = False,
                               auto_scale: tuple[float, float, float] = None,
                               to_gray: bool = True,
                               result_type: int = 0,
                               use_alpha_mask: bool = False) -> Optional[list]:
        """
        通过模板匹配，返回匹配度最高的 4 个角坐标（非圆心点）。

        :param bigger_img: 大图
        :param smaller_pic: 模板，支持 ndarray 或图片路径
        :param threshold: 相似度
        :param edge: 是否边缘计算
        :param auto_scale: 缩放参数
        :param to_gray: 是否灰度计算
        :param result_type: 0-匹配度最高；1-最靠左；2-最靠上
        :param use_alpha_mask: 是否按 alpha 通道做透明模板匹配
        :return: [(左上角, 右上角, 左下角, 右下角), 相似度] 或 None
        """
        template = resolve_template(smaller_pic)
        if template is None or bigger_img is None:
            return None

        match_result = find_all_template(im_source=bigger_img, im_template=template,
                                         threshold=threshold, edge=edge,
                                         auto_scale=auto_scale, to_gray=to_gray,
                                         use_alpha_mask=use_alpha_mask)
        if not match_result:
            return None

        match_result = sort_match_result(match_result, result_type)
        match = match_result[0]
        rect = match["rectangle"]
        confidence: float = round(match["confidence"], 2)
        return [
            (rect[0][0], rect[0][1]),  # 左上角
            (rect[2][0], rect[2][1]),  # 右上角
            (rect[1][0], rect[1][1]),  # 左下角
            (rect[3][0], rect[3][1]),  # 右下角
            confidence,
        ]
