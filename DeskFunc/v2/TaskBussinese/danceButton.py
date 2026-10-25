# coding: utf-8
"""
团练授业 / 势力修炼的按键识别（v2）。

识别目标：屏幕上依次出现的“上、下、左、右、J、K”按键提示，返回顺序与画面从左到右一致。

旧版（v1）在游戏由白天切换到黑夜后经常识别失效，原因有两类：
1. v1 的灰色按键走 Canny 边缘匹配，但 Canny 阈值写死为 100/200。夜间画面整体变暗后，
   源图边缘大量消失，而模板是白天采集的强边缘，两边边缘图对不上；
2. 游戏昼夜切换本质上是给画面叠加了一层颜色/亮度变化，按钮又是半透明材质，
   按钮背后的场景也跟着变化，直接整块像素匹配的相似度会被背景拉低。

v2 的做法：
- 不再调用 FindWindowsImageTemplate / GetConfig 这类旧封装，直接使用 Core 的截图、模板读取、模板匹配原语；
- 每个模板按“灰度直接匹配 -> 自适应阈值边缘匹配 -> 直方图均衡匹配”的顺序逐级兜底，白天用最快的第一级，夜间第一级失效时自动进入对亮度不敏感的边缘/均衡匹配；
- 自适应 Canny 的阈值跟随图像中位数变化，亮度整体变暗时阈值同步下降，夜间不会丢失边缘；
- 模板只在初始化时预处理一次，识别过程中不再修改模板，避免缓存对象被意外污染。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

import cv2
import numpy as np

from Core.vision.template import find_all_template, load_template
from Core.windows.capture import PicCapture, WindowsCapture
from Utils.resourceConfig import get_resources

# 按键类型：灰色按钮用于团练授业，绿色按钮用于漠西风涛等玩法
DANCE_TYPE_GREY = "grey"
DANCE_TYPE_GREEN = "green"

# 资源字段与按键名的对应关系，顺序同时决定同一横坐标下的返回顺序（与 v1 保持一致）
_GREY_BUTTON_FIELDS: tuple[tuple[str, str], ...] = (
    ("UP", "dance_Up"),
    ("Down", "dance_Down"),
    ("Left", "dance_Left"),
    ("Right", "dance_Right"),
    ("J", "dance_J"),
    ("K", "dance_K"),
)

_GREEN_BUTTON_FIELDS: tuple[tuple[str, str], ...] = (
    ("UP", "dance_Up"),
    ("Down", "dance_Down"),
    ("Left", "dance_Left"),
    ("Right", "dance_Right"),
)

ImageLike = Union[np.ndarray, PicCapture]


@dataclass(frozen=True)
class DanceButtonMatch:
    """
    一次按键命中的结果。

    - name：按键名（UP / Down / Left / Right / J / K）；
    - x、y：命中区域中心点在窗口客户区中的坐标；
    - confidence：该策略下的最终匹配度；
    - strategy：实际命中的策略，gray / edge / equalized，排查夜间问题时使用。
    """

    name: str
    x: float
    y: float
    confidence: float
    strategy: str


@dataclass(frozen=True)
class _DanceTemplate:
    """预处理后的按键模板，初始化后只读。"""

    name: str
    gray: np.ndarray
    edge: np.ndarray
    equalized: np.ndarray


def _to_gray(image: np.ndarray) -> Optional[np.ndarray]:
    """
    把截图或模板统一转换为灰度图。

    支持单通道、BGR、BGRA 三种常见格式；其他通道数返回 None，交给上层跳过识别。
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


def _normalize_light(gray: np.ndarray) -> np.ndarray:
    """
    拉伸整体亮度范围，削弱昼夜切换带来的“整体偏暗/偏亮”。

    使用 1%~99% 分位数而不是最小/最大值，避免界面上的极亮图标或极暗像素把范围撑坏。
    拉伸属于线性变换，不会破坏按键本身的形状和边缘。
    """
    low, high = np.percentile(gray, (1, 99))
    if high - low < 1:
        return gray
    normalized = (gray.astype(np.float32) - float(low)) * (255.0 / float(high - low))
    return np.clip(normalized, 0, 255).astype(np.uint8)


def _auto_canny(gray: np.ndarray) -> np.ndarray:
    """
    自适应阈值 Canny。

    阈值按图像中位数动态计算：夜间画面整体变暗时中位数同步下降，阈值一起下降，
    因此同一按键在白天/黑夜都能提取出相近的边缘结构，这是修复昼夜识别失效的关键。
    """
    median = float(np.median(gray))
    lower = int(max(10.0, 0.66 * median))
    upper = int(max(float(lower + 10), min(255.0, 1.33 * median)))
    return cv2.Canny(gray, lower, upper)


def _extract_image(image: ImageLike) -> Optional[np.ndarray]:
    """兼容直接传入 ndarray 和传入 PicCapture 两种调用方式。"""
    if image is None:
        return None
    if isinstance(image, np.ndarray):
        return image
    content = getattr(image, "pic_content", None)
    return content if isinstance(content, np.ndarray) else None


def _build_templates(pic_config, button_fields: tuple[tuple[str, str], ...]) -> tuple[_DanceTemplate, ...]:
    """
    读取并预处理一组按键模板。

    :param pic_config：资源中的按键路径配置对象（dance_grey / dance_green）；
    :param button_fields：(按键名, 资源字段名) 列表；
    :return: 预处理后的模板元组；图片缺失或格式异常的按键会被跳过
    """
    templates: list[_DanceTemplate] = []
    for name, field in button_fields:
        path = getattr(pic_config, field, "")
        image = load_template(path)
        gray = _to_gray(image)
        if gray is None:
            continue
        templates.append(_DanceTemplate(
            name=name,
            gray=gray,
            # 边缘模板基于亮度拉伸后的图生成，与源图保持同一套预处理流程
            edge=_auto_canny(_normalize_light(gray)),
            equalized=cv2.equalizeHist(gray),
        ))
    return tuple(templates)


class FindDanceButton:
    """
    团练授业、势力修炼的绿色/灰色上下左右按键识别。

    典型用法：
        finder = FindDanceButton()
        keys = finder.find_button_in_window(hwnd, DANCE_TYPE_GREY)
        if keys:
            # keys 已经是画面从左到右的顺序，直接按顺序发送按键即可
            ...

    线程约束：模板只读，可以被多个任务共享；内部截图对象无状态，同一实例也可复用。
    """

    def __init__(self, threshold: float = 0.8,
                 edge_threshold: float = 0.72,
                 equalized_threshold: float = 0.8,
                 conflict_distance: float = 18.0):
        """
        :param threshold: 灰度直接匹配阈值，白天正常画面使用；
        :param edge_threshold: 边缘兜底阈值；边缘图是二值结构，匹配度略低于彩色灰度图属正常现象；
        :param equalized_threshold: 直方图均衡兜底阈值；
        :param conflict_distance: 不同模板命中点相距小于该像素值时视为同一个按键，只保留匹配度最高的一项。
        """
        self._threshold = float(threshold)
        self._edge_threshold = float(edge_threshold)
        self._equalized_threshold = float(equalized_threshold)
        self._conflict_distance = float(conflict_distance)

        resources = get_resources()
        self._grey_templates = _build_templates(resources.dance_grey, _GREY_BUTTON_FIELDS)
        self._green_templates = _build_templates(resources.dance_green, _GREEN_BUTTON_FIELDS)
        self._capture = WindowsCapture()

    def find_button(self, image: ImageLike) -> list[str]:
        """识别灰色按键（团练授业），返回从左到右的按键名列表。"""
        return [match.name for match in self.find_button_matches(image, DANCE_TYPE_GREY)]

    def find_button_green(self, image: ImageLike) -> list[str]:
        """识别绿色按键（漠西风涛等玩法），返回从左到右的按键名列表。"""
        return [match.name for match in self.find_button_matches(image, DANCE_TYPE_GREEN)]

    def find_button_in_window(self, hwnd: int,
                              dance_type: str = DANCE_TYPE_GREY) -> list[str]:
        """截图并识别指定窗口中的按键，返回从左到右的按键名列表。"""
        return [match.name for match in self.find_button_matches_in_window(hwnd, dance_type)]

    def find_button_matches_in_window(self, hwnd: int,
                                      dance_type: str = DANCE_TYPE_GREY) -> list[DanceButtonMatch]:
        """截图并返回完整的命中结果（包含客户区坐标和命中所用策略）。"""
        capture = self._capture.capture(hwnd)
        if capture is None:
            return []
        return self.find_button_matches(capture.pic_content, dance_type)

    def find_button_matches(self, image: ImageLike,
                            dance_type: str = DANCE_TYPE_GREY) -> list[DanceButtonMatch]:
        """
        在给定截图中识别按键。

        :param image: 客户区截图（ndarray 或 PicCapture）；
        :param dance_type: grey / green；
        :return: 按横坐标升序排列的命中结果；识别失败返回空列表
        """
        gray = _to_gray(_extract_image(image))
        if gray is None:
            return []

        templates = self._templates_for(dance_type)

        # 边缘图和均衡图只在需要兜底时才计算，白天走第一级匹配时不会产生额外开销
        normalized: Optional[np.ndarray] = None
        edge_source: Optional[np.ndarray] = None
        equalized_source: Optional[np.ndarray] = None

        matches: list[DanceButtonMatch] = []
        for template in templates:
            # 第一级：普通灰度匹配，速度最快，正常白天画面由它完成识别
            found = self._match_template(gray, template.gray, template.name,
                                         self._threshold, "gray")

            # 第二级：自适应边缘匹配。白天到黑夜后整体亮度、半透明背景都会变化，
            # 但按键轮廓仍然存在，用相对阈值提取边缘可以稳定命中。
            if not found:
                if edge_source is None:
                    if normalized is None:
                        normalized = _normalize_light(gray)
                    edge_source = _auto_canny(normalized)
                found = self._match_template(edge_source, template.edge, template.name,
                                             self._edge_threshold, "edge")

            # 第三级：直方图均衡匹配。极端偏暗/偏亮、对比度被压缩时，均衡后重新拉开灰度分布。
            if not found:
                if equalized_source is None:
                    equalized_source = cv2.equalizeHist(gray)
                found = self._match_template(equalized_source, template.equalized, template.name,
                                             self._equalized_threshold, "equalized")

            matches.extend(found)

        # 上下左右四个模板的外圈按钮底图非常相似，同一个按键可能被多个模板同时命中。
        # 先按匹配度去重，保证一个画面位置只输出一个按键，再接 v1 的横坐标排序。
        matches = self._deduplicate_matches(matches)
        matches.sort(key=lambda item: item.x)
        return matches

    def _deduplicate_matches(self, matches: list[DanceButtonMatch]) -> list[DanceButtonMatch]:
        """
        合并不同模板在同一位置的重复命中。

        保留匹配度最高的一项；两个真实按键的中心距离远大于 conflict_distance，
        因此不会把左右相邻的两个不同按键误合并。
        """
        if not matches:
            return []
        threshold_square = self._conflict_distance * self._conflict_distance
        kept: list[DanceButtonMatch] = []
        for match in sorted(matches, key=lambda item: item.confidence, reverse=True):
            duplicated = False
            for exist in kept:
                distance_square = (match.x - exist.x) ** 2 + (match.y - exist.y) ** 2
                if distance_square <= threshold_square:
                    duplicated = True
                    break
            if not duplicated:
                kept.append(match)
        return kept

    def _templates_for(self, dance_type: str) -> tuple[_DanceTemplate, ...]:
        """按类型取模板集合，未知类型直接报错，避免静默返回空结果掩盖配置问题。"""
        if dance_type == DANCE_TYPE_GREY:
            return self._grey_templates
        if dance_type == DANCE_TYPE_GREEN:
            return self._green_templates
        raise ValueError(f"未知的按键类型：{dance_type}，仅支持 {DANCE_TYPE_GREY} / {DANCE_TYPE_GREEN}")

    @staticmethod
    def _match_template(source: np.ndarray, template: np.ndarray, name: str,
                        threshold: float, strategy: str) -> list[DanceButtonMatch]:
        """
        执行一次模板匹配并转换为业务结果。

        find_all_template 内部已按匹配度降序返回并做了重叠抑制；
        两张图都是灰度图，to_gray=True 只是让底层跳过通道转换。
        """
        results = find_all_template(
            im_source=source,
            im_template=template,
            threshold=threshold,
            max_cnt=0,
            to_gray=True,
        )
        if not results:
            return []
        return [
            DanceButtonMatch(
                name=name,
                x=float(result["result"][0]),
                y=float(result["result"][1]),
                confidence=float(result["confidence"]),
                strategy=strategy,
            )
            for result in results
        ]
