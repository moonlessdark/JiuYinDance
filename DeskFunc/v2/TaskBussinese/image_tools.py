# coding: utf-8
"""
v2 业务层共用的图像小工具。

这里只放“多个业务都会用到、且不包含业务流程”的纯函数：
1. 通道转换；
2. 模板局部遮罩；
3. 匹配点去重。

真正的模板匹配仍然调用 Core.vision.template，业务对象不再各自重复实现。
"""
from __future__ import annotations

from typing import Optional

import cv2
import numpy as np


def to_gray(image: np.ndarray) -> Optional[np.ndarray]:
    """
    把截图或模板转换为灰度图。

    :param image: 单通道 / BGR / BGRA 图片
    :return: 灰度图；输入无效或通道数不支持时返回 None
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return None
    if image.ndim == 2:
        return image
    channel = image.shape[2]
    if channel == 1:
        return image[:, :, 0]
    if channel == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if channel == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return None


def to_bgr(image: np.ndarray) -> Optional[np.ndarray]:
    """把 BGRA 截图转成 BGR，供颜色判断使用。"""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return None
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def mask_template_region(image: np.ndarray,
                         left: int, top: int, right: int, bottom: int,
                         color: tuple[int, int, int] = (0, 255, 0)) -> Optional[np.ndarray]:
    """
    在模板副本上涂掉指定区域，避免物品数量、角标等动态内容干扰匹配。

    必须复制后再绘制：load_template 返回的是缓存对象，原地修改会污染后续所有调用。

    :param image: 原始模板
    :param left/top/right/bottom: 需要遮挡的矩形，使用模板自身像素坐标
    :param color: 填充颜色，默认纯绿
    :return: 处理后的模板副本；输入无效时返回 None
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return None
    masked = image.copy()
    cv2.rectangle(masked, (int(left), int(top)), (int(right), int(bottom)), color, -1)
    return masked


def deduplicate_points(points: list[dict], distance: float) -> list[dict]:
    """
    对同一位置的重复匹配去重，保留匹配度最高的一项。

    :param points: 每项至少包含 result=(x, y) 和 confidence
    :param distance: 两个中心点距离不超过该值时视为同一个目标
    :return: 去重后的匹配结果列表
    """
    if not points:
        return []
    distance_square = float(distance) * float(distance)
    kept: list[dict] = []
    for point in sorted(points, key=lambda item: float(item.get("confidence", 0.0)), reverse=True):
        x, y = point["result"]
        if all((x - exist["result"][0]) ** 2 + (y - exist["result"][1]) ** 2 > distance_square
               for exist in kept):
            kept.append(point)
    return kept
