# coding: utf-8
"""
BUFF 倒计时与叠层数字识别。

在已经定位到 BUFF 图标的前提下：
1. 以图标矩形为基准，推算下方倒计时文字区域；
2. 在文字区域内逐个匹配 0~9 数字模板，收集所有高分位置；
3. 按横坐标顺序拼接数字，支持 0、9、14 这类一位/多位秒数；
4. 叠层数字锚定图标右下角，右对齐，最多两位。

数字区域统一取 BGR 三通道最小值转灰度：游戏数字是白色文字，背景可能
是橙色/红色，直接转普通灰度会把彩色背景也提亮，导致数字匹配度偏低。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from numpy import ndarray

from Core.vision.template import load_template

# 单个数字的默认匹配阈值
DEFAULT_DIGIT_THRESHOLD = 0.8
# BUFF 图标模板的基准高度（像素），用于把文字区域偏移换算到当前缩放比例
ICON_REFERENCE_HEIGHT = 32.0
# 倒计时文字相对 BUFF 图标矩形的偏移（基于基准尺寸）
COUNTDOWN_TEXT_TOP_OFFSET = 2.0
COUNTDOWN_TEXT_HEIGHT = 16.0
COUNTDOWN_TEXT_LEFT_PAD = 4.0
COUNTDOWN_TEXT_RIGHT_PAD = 10.0
# 同一字符可能被多个数字模板命中，中心距离小于该值视为重复
DIGIT_DEDUP_TOLERANCE = 3.0
# 叠层数字区域：锚定图标右下角，按图标尺寸比例向上、向左扩展
STACK_WIDTH_RATIO = 0.70
STACK_HEIGHT_RATIO = 0.62
STACK_RIGHT_PAD = 2.0
STACK_BOTTOM_PAD = 1.0
# 叠层数字最多两位；误匹配出更多候选时只保留最靠右的两位
STACK_MAX_DIGITS = 2


@dataclass(frozen=True)
class CountdownResult:
    """倒计时识别结果。"""

    seconds: int
    digits: str
    confidence: float
    region: tuple[int, int, int, int]


@dataclass(frozen=True)
class StackCountResult:
    """图标右下角叠层数字识别结果。"""

    count: int
    digits: str
    confidence: float
    region: tuple[int, int, int, int]


def load_digit_templates(directory: str) -> dict[int, ndarray]:
    """
    从目录加载 0~9 数字模板。

    :param directory: 数字模板目录绝对路径
    :return: {数字: 模板图}；缺图时对应数字无法被识别，不抛异常
    """
    templates: dict[int, ndarray] = {}
    for digit in range(10):
        template = load_template(os.path.join(directory, f"{digit}.png"))
        if template is not None:
            templates[digit] = template
    return templates


def read_countdown(image: ndarray,
                   buff_region: tuple[int, int, int, int],
                   digit_templates: dict[int, ndarray],
                   threshold: float = DEFAULT_DIGIT_THRESHOLD
                   ) -> Optional[CountdownResult]:
    """
    读取 BUFF 图标下方的倒计时秒数。

    :param image: 完整客户区截图（BGR/BGRA/灰度）
    :param buff_region: 已定位到的 BUFF 图标区域 (x, y, width, height)
    :param digit_templates: 数字模板字典
    :param threshold: 单个数字的匹配阈值
    :return: 识别结果；区域无效或没有识别到数字时返回 None
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return None
    if not digit_templates:
        return None

    text_region = _build_text_region(image, buff_region)
    if text_region is None:
        return None
    x1, y1, x2, y2 = text_region
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    gray_roi = _to_digit_gray(roi)
    scale = (buff_region[3] / ICON_REFERENCE_HEIGHT) if buff_region[3] > 0 else 1.0

    candidates = _collect_digit_candidates(gray_roi, digit_templates, threshold, scale)
    if not candidates:
        return None

    kept = _dedup_candidates(candidates, DIGIT_DEDUP_TOLERANCE * scale)
    kept.sort(key=lambda item: item[2])

    digits = "".join(str(digit) for _, digit, _, _ in kept)
    if not digits:
        return None

    return CountdownResult(
        seconds=int(digits),
        digits=digits,
        confidence=min(confidence for confidence, _, _, _ in kept),
        region=(x1, y1, x2 - x1, y2 - y1),
    )


def read_stack_count(image: ndarray,
                     buff_region: tuple[int, int, int, int],
                     digit_templates: dict[int, ndarray],
                     threshold: float = DEFAULT_DIGIT_THRESHOLD
                     ) -> Optional[StackCountResult]:
    """
    读取 BUFF 图标右下角的叠层数字。

    :param image: 完整客户区截图（BGR/BGRA/灰度）
    :param buff_region: 已定位到的 BUFF 图标区域 (x, y, width, height)
    :param digit_templates: 数字模板字典
    :param threshold: 单个数字的匹配阈值
    :return: 识别结果；区域无效或没有识别到数字时返回 None
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return None
    if not digit_templates:
        return None

    search_region = _build_stack_region(image, buff_region)
    if search_region is None:
        return None
    x1, y1, x2, y2 = search_region
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    gray_roi = _to_digit_gray(roi)
    scale = (buff_region[3] / ICON_REFERENCE_HEIGHT) if buff_region[3] > 0 else 1.0

    candidates = _collect_digit_candidates(gray_roi, digit_templates, threshold, scale)
    if not candidates:
        return None

    kept = _dedup_candidates(candidates, DIGIT_DEDUP_TOLERANCE * scale)
    kept.sort(key=lambda item: item[2])
    # 叠层数字右对齐，误匹配出更多候选时保留最靠右的两位
    if len(kept) > STACK_MAX_DIGITS:
        kept = kept[-STACK_MAX_DIGITS:]

    digits = "".join(str(digit) for _, digit, _, _ in kept)
    if not digits:
        return None

    return StackCountResult(
        count=int(digits),
        digits=digits,
        confidence=min(confidence for confidence, _, _, _ in kept),
        region=(x1, y1, x2 - x1, y2 - y1),
    )


def _build_stack_region(image: ndarray,
                        buff_region: tuple[int, int, int, int]
                        ) -> Optional[tuple[int, int, int, int]]:
    """根据 BUFF 图标矩形推算右下角叠层数字搜索区域，并裁剪到图片边界内。"""
    left, top, width, height = (int(round(value)) for value in buff_region)
    if width <= 0 or height <= 0:
        return None

    scale = height / ICON_REFERENCE_HEIGHT
    image_height, image_width = image.shape[:2]

    x2 = left + width + int(round(STACK_RIGHT_PAD * scale))
    y2 = top + height + int(round(STACK_BOTTOM_PAD * scale))
    x1 = x2 - int(round(STACK_WIDTH_RATIO * width))
    y1 = y2 - int(round(STACK_HEIGHT_RATIO * height))

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image_width, x2)
    y2 = min(image_height, y2)
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        return None
    return x1, y1, x2, y2


def _build_text_region(image: ndarray,
                       buff_region: tuple[int, int, int, int]
                       ) -> Optional[tuple[int, int, int, int]]:
    """根据 BUFF 图标矩形推算倒计时文字区域，并裁剪到图片边界内。"""
    left, top, width, height = (int(round(value)) for value in buff_region)
    if width <= 0 or height <= 0:
        return None

    scale = height / ICON_REFERENCE_HEIGHT
    image_height, image_width = image.shape[:2]

    x1 = left - int(round(COUNTDOWN_TEXT_LEFT_PAD * scale))
    x2 = left + width + int(round(COUNTDOWN_TEXT_RIGHT_PAD * scale))
    y1 = top + height + int(round(COUNTDOWN_TEXT_TOP_OFFSET * scale))
    y2 = y1 + int(round(COUNTDOWN_TEXT_HEIGHT * scale))

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image_width, x2)
    y2 = min(image_height, y2)
    if x2 - x1 <= 0 or y2 - y1 <= 0:
        return None
    return x1, y1, x2, y2


def _collect_digit_candidates(gray_roi: ndarray,
                              digit_templates: dict[int, ndarray],
                              threshold: float,
                              scale: float
                              ) -> list[tuple[float, int, float, float]]:
    """在文字区域内匹配所有数字模板，返回 (匹配度, 数字, 中心x, 中心y) 候选。"""
    candidates: list[tuple[float, int, float, float]] = []
    for digit, template in digit_templates.items():
        scaled_template = _resize_template(template, scale)
        scaled_template = _to_gray(scaled_template)
        if (scaled_template.shape[0] > gray_roi.shape[0]
                or scaled_template.shape[1] > gray_roi.shape[1]):
            continue

        result = cv2.matchTemplate(gray_roi, scaled_template, cv2.TM_CCOEFF_NORMED)
        result = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
        ys, xs = np.where(result >= float(threshold))
        template_height, template_width = scaled_template.shape[:2]
        for y, x in zip(ys, xs):
            candidates.append((
                float(result[y, x]),
                digit,
                float(x) + template_width / 2.0,
                float(y) + template_height / 2.0,
            ))
    return candidates


def _dedup_candidates(candidates: list[tuple[float, int, float, float]],
                      tolerance: float) -> list[tuple[float, int, float, float]]:
    """合并同一字符被多个数字模板命中的候选点，只按横坐标去重。"""
    ordered = sorted(candidates, key=lambda item: item[0], reverse=True)
    kept: list[tuple[float, int, float, float]] = []
    for candidate in ordered:
        _, _, center_x, _ = candidate
        if any(abs(center_x - kept_x) <= tolerance for _, _, kept_x, _ in kept):
            continue
        kept.append(candidate)
    return kept


def _resize_template(template: ndarray, scale: float) -> ndarray:
    """按当前窗口缩放比例调整数字模板尺寸。"""
    if abs(scale - 1.0) < 1e-3:
        return template
    new_width = max(1, int(round(template.shape[1] * scale)))
    new_height = max(1, int(round(template.shape[0] * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    return cv2.resize(template, (new_width, new_height), interpolation=interpolation)


def _to_gray(image: ndarray) -> ndarray:
    """统一转灰度；已经是灰度图时直接返回。"""
    if image.ndim == 2:
        return image
    channel = image.shape[2]
    if channel == 1:
        return image[:, :, 0]
    if channel == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if channel == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise RuntimeError(f"不支持对 {channel} 通道图片做灰度处理")


def _to_digit_gray(image: ndarray) -> ndarray:
    """
    把数字搜索区域转成“取三通道最小值”的灰度图。

    白色数字在三个通道都接近 255，而橙色/红色背景的通道最小值明显偏低，
    取最小值可压暗彩色背景、保留白色数字，显著提升匹配度。
    """
    if image.ndim == 2:
        return image
    channel = image.shape[2]
    if channel == 1:
        return image[:, :, 0]
    if channel >= 3:
        return image[:, :, :3].min(axis=2)
    return _to_gray(image)
