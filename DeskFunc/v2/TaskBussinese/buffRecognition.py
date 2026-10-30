# coding: utf-8
"""
BUFF 识别业务核心。

输入是“一帧游戏窗口客户区截图”，输出是本帧真正检测到的 BUFF 列表。
图像来源由调用方负责（屏幕截图），本模块不读取本地截图文件。

识别流程：
1. 按配置 ROI 裁剪右上角 BUFF 区域；
2. 灰度 CCOEFF 模板匹配，收集同一图标的全部候选位置；
3. 颜色二次校验（彩色像素占比 + 色相直方图），过滤同形状不同颜色的误匹配；
4. 跨模板同位置去重，只保留分数最高的模板结果；
5. 对保留位置读取倒计时和右下角叠层数字；
6. 同一 BUFF 每帧只保留一个结果，再交给 BuffTracker 延续 track_id；
7. 只把本帧真正检测到的轨迹返回给面板，未检测轨迹保留在跟踪器内部。
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np
from numpy import ndarray

from Core.config.paths import PathUtil
from Core.vision.buff_matcher import (find_matches_gray,
                                      preprocess_gray_template)
from Core.vision.template import load_template
from DeskFunc.v2.TaskBussinese.buffConfig import (
    TEMPLATE_CATEGORIES,
    enabled_template_map,
    is_template_enabled,
    load_buff_config,
)
from DeskFunc.v2.TaskBussinese.buffCountdown import (
    DEFAULT_DIGIT_THRESHOLD,
    load_digit_templates,
    read_countdown,
    read_stack_count,
)
from DeskFunc.v2.TaskBussinese.buffTracker import (
    BuffTracker,
    TrackDetection,
)

# 单个模板在一帧内最多保留多少个命中位置
MAX_MATCHES_PER_TEMPLATE = 16
# 跨模板同位置去重距离（像素）；两个真实 BUFF 中心间距约 40px
DEDUP_DISTANCE = 16.0
# 未给某个 BUFF 配置 threshold 时使用的默认匹配阈值
DEFAULT_MATCH_THRESHOLD = 0.7
# 配置未提供 roi 时的默认搜索区域 [左, 上, 右, 下]（0~1 比例）
DEFAULT_ROI = (0.70, 0.00, 0.98, 0.20)
# 颜色二次校验默认值
DEFAULT_COLOR_SATURATION = 60.0
DEFAULT_COLOR_MAX_RATIO_DIFF = 0.5
DEFAULT_COLOR_FLICKER_MAX_RATIO_DIFF = 0.55
DEFAULT_COLOR_MAX_HUE_DIFF = 0.35
COLOR_HUE_BINS = 18
COLOR_HUE_MIN_PIXELS = 20
# 闪烁丢失容忍帧数
DEFAULT_FLICKER_MAX_MISS_FRAMES = 2


@dataclass
class BuffDetection:
    """识别器输出的一条 BUFF 状态，供面板和日志使用。"""

    name: str
    category: str
    attribute: str
    stack: Optional[int] = None
    seconds: Optional[int] = None
    has_countdown: bool = False
    track_id: int = -1
    position: Optional[tuple[float, float]] = None
    score: float = 0.0


@dataclass
class BuffTemplate:
    """一个 BUFF 模板的配置和预处理数据。"""

    name: str
    path: str
    image: ndarray
    category: str
    template_name: str
    attribute: str
    countdown: bool
    threshold: float
    mask: Optional[ndarray]
    color_ratio: float
    hue_hist: Optional[ndarray]
    gray_image: Optional[ndarray]


@dataclass
class _Candidate:
    """单帧内某个模板的一次候选命中。"""

    template_index: int
    score: float
    rect: tuple[int, int, int, int]
    position: tuple[float, float]
    seconds: Optional[int] = None
    stack: Optional[int] = None


def _resolve_path(path: str) -> str:
    """把配置里的相对路径转换为项目根目录下的绝对路径。"""
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(PathUtil().get_root_path() + path)


def _parse_roi(value) -> tuple[float, float, float, float]:
    """解析 [左, 上, 右, 下] 比例搜索区域。"""
    if isinstance(value, (list, tuple)) and len(value) >= 4:
        return tuple(float(item) for item in value[:4])
    return DEFAULT_ROI


def _crop_roi(image: ndarray, roi: tuple[float, float, float, float]
              ) -> tuple[ndarray, tuple[int, int]]:
    """按比例裁剪搜索区域，返回 (裁剪图, 左上角在整图中的偏移)。"""
    height, width = image.shape[:2]
    left = max(0, int(roi[0] * width))
    top = max(0, int(roi[1] * height))
    right = min(width, int(roi[2] * width))
    bottom = min(height, int(roi[3] * height))
    if right < left:
        left, right = right, left
    if bottom < top:
        top, bottom = bottom, top
    return image[top:bottom, left:right], (left, top)


def _to_gray_image(image: ndarray) -> Optional[ndarray]:
    """把 ROI 统一转成灰度图；每帧只调用一次，供所有模板复用。"""
    if image is None or image.size == 0:
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


def _saturation_ratio(bgr: ndarray, mask: Optional[ndarray],
                      saturation_threshold: float) -> float:
    """统计饱和度高像素的占比，用于区分灰色/彩色两种图标状态。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    values = saturation[mask > 0] if mask is not None else saturation.reshape(-1)
    if values.size == 0:
        return 0.0
    return float(np.count_nonzero(values >= saturation_threshold)) / values.size


def _hue_histogram(bgr: ndarray, mask: Optional[ndarray],
                   saturation_threshold: float) -> Optional[ndarray]:
    """统计彩色像素的归一化色相直方图，用于区分金/紫/绿等相似图标。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    selected = saturation >= saturation_threshold
    if mask is not None:
        if mask.shape[:2] != selected.shape:
            mask = cv2.resize(mask, (selected.shape[1], selected.shape[0]),
                              interpolation=cv2.INTER_NEAREST)
        selected = selected & (mask > 0)
    count = int(np.count_nonzero(selected))
    if count < COLOR_HUE_MIN_PIXELS:
        return None
    hist, _ = np.histogram(hue[selected], bins=COLOR_HUE_BINS, range=(0, 180))
    hist = hist.astype(np.float32)
    hist /= hist.sum()
    return hist


def _measure_color_diff(image: ndarray, rect: tuple[int, int, int, int],
                        template: BuffTemplate,
                        saturation_threshold: float
                        ) -> tuple[float, float, Optional[float]]:
    """计算命中区域与模板的彩色占比差异和色相直方图差异。"""
    x, y, width, height = rect
    patch = image[y:y + height, x:x + width]
    if patch.ndim == 3 and patch.shape[2] == 4:
        patch = patch[:, :, :3]
    elif patch.ndim == 2:
        patch = cv2.cvtColor(patch, cv2.COLOR_GRAY2BGR)
    if patch.size == 0:
        return 0.0, 1.0, None

    mask = template.mask
    if mask is not None and mask.shape[:2] != patch.shape[:2]:
        mask = cv2.resize(mask, (patch.shape[1], patch.shape[0]),
                          interpolation=cv2.INTER_NEAREST)
    ratio = _saturation_ratio(patch, mask, saturation_threshold)

    hue_diff = None
    if template.hue_hist is not None:
        patch_hist = _hue_histogram(patch, mask, saturation_threshold)
        if patch_hist is not None:
            hue_diff = 0.5 * float(np.abs(template.hue_hist - patch_hist).sum())
    return ratio, abs(template.color_ratio - ratio), hue_diff


def _choose_best(template: BuffTemplate,
                 candidates: list[_Candidate]) -> _Candidate:
    """
    同一个 BUFF 一帧只保留一个结果。

    - 有倒计时：取剩余秒数最大的位置；
    - 无倒计时：取叠层数最多的位置；
    - 读数相同或都缺失时，取匹配度最高的位置。
    """
    if template.countdown:
        return max(candidates, key=lambda item: (
            item.seconds if item.seconds is not None else -1,
            item.score))
    return max(candidates, key=lambda item: (
        item.stack if item.stack is not None else -1,
        item.score))


def _dedup_candidates(candidates: list[_Candidate]) -> list[_Candidate]:
    """跨模板同位置去重，保留分数最高的模板结果。"""
    ordered = sorted(candidates, key=lambda item: item.score, reverse=True)
    kept: list[_Candidate] = []
    for candidate in ordered:
        center = candidate.position
        duplicate = any(
            math.hypot(center[0] - other.position[0],
                       center[1] - other.position[1]) <= DEDUP_DISTANCE
            for other in kept)
        if not duplicate:
            kept.append(candidate)
    return kept


class BuffRecognizer:
    """加载 BUFF 模板，并把一帧截图识别成 BUFF 状态列表。"""

    def __init__(self, config_path: str) -> None:
        """
        :param config_path: buff_config.json 的绝对路径
        """
        self.config = load_buff_config(config_path)
        self._roi = _parse_roi(self.config.get("roi"))
        self._threshold = float(
            self.config.get("threshold", DEFAULT_MATCH_THRESHOLD))
        self._digit_threshold = float(
            self.config.get("digit_threshold", DEFAULT_DIGIT_THRESHOLD))
        digit_dir = _resolve_path(
            self.config.get("digit_template_dir", "")
            or "Resources/ImageTemplate/PicBuff/number")
        self._digit_templates = load_digit_templates(digit_dir)

        color_cfg = self.config.get("color_check", {})
        self._color_enabled = bool(color_cfg.get("enabled", True))
        self._color_saturation = float(
            color_cfg.get("saturation_threshold", DEFAULT_COLOR_SATURATION))
        self._color_max_diff = float(
            color_cfg.get("max_ratio_diff", DEFAULT_COLOR_MAX_RATIO_DIFF))
        self._color_max_hue = float(
            color_cfg.get("max_hue_diff", DEFAULT_COLOR_MAX_HUE_DIFF))
        self._color_flicker_max_diff = float(
            color_cfg.get("flicker_max_ratio_diff",
                          DEFAULT_COLOR_FLICKER_MAX_RATIO_DIFF))

        self._flicker_max_miss = int(
            self.config.get("flicker", {}).get(
                "max_miss_frames", DEFAULT_FLICKER_MAX_MISS_FRAMES))
        self._tracker = BuffTracker(max_miss_frames=self._flicker_max_miss + 3)
        self.templates = self._load_templates()
        self.scan_interval_ms = max(
            200, int(self.config.get("scan_interval_ms", 1000)))

    @property
    def panel_settings(self) -> dict:
        """返回面板外观设置，供界面层构造 PanelSettings。"""
        panel = self.config.get("panel", {})
        return panel if isinstance(panel, dict) else {}

    @property
    def showbuff_dir(self) -> str:
        """ShowBuff 大图标目录绝对路径。"""
        return _resolve_path(
            self.config.get("showbuff_dir", "")
            or "Resources/ImageTemplate/PicBuff/ShowBuff")

    def _load_templates(self) -> list[BuffTemplate]:
        """
        按“模版类型 -> 模版名称 -> BUFF 信息”三级结构加载模板。

        只加载 enabled_templates 中勾选的模版组；模板 alpha 透明区在匹配前
        由 buff_matcher 自动填充，这里保留原始图用于颜色统计。
        """
        templates: list[BuffTemplate] = []
        buffs = self.config.get("buffs", {})
        if not isinstance(buffs, dict):
            return templates

        enabled_map = enabled_template_map(self.config)
        for category, groups in buffs.items():
            if not isinstance(groups, dict):
                continue
            if category not in TEMPLATE_CATEGORIES:
                print(f"BUFF 配置警告：未知模版类型 {category}")
            for template_name, items in groups.items():
                if not isinstance(items, dict):
                    continue
                if not is_template_enabled(enabled_map, category, template_name):
                    continue

                for name, item in sorted(
                        items.items(), key=lambda kv: kv[1].get("order", 0)):
                    if not isinstance(item, dict):
                        continue
                    path = _resolve_path(item.get("template", ""))
                    image = load_template(path)
                    if image is None:
                        print(f"BUFF 模板读取失败，已跳过：{name} -> {path}")
                        continue

                    has_alpha = image.ndim == 3 and image.shape[2] == 4
                    mask = None
                    if has_alpha:
                        mask = (image[:, :, 3] > 0).astype(np.uint8)
                    # 颜色占比和色相直方图必须在转成 BGR 之前计算
                    color_ratio = _saturation_ratio(
                        image[:, :, :3], mask, self._color_saturation)
                    hue_hist = _hue_histogram(
                        image[:, :, :3], mask, self._color_saturation)

                    templates.append(BuffTemplate(
                        name=str(name),
                        path=path,
                        image=image,
                        category=str(category),
                        template_name=str(template_name),
                        attribute=str(item.get("attribute", "叠层")),
                        countdown=bool(item.get("countdown", False)),
                        threshold=float(item.get("threshold", self._threshold)),
                        mask=mask,
                        color_ratio=color_ratio,
                        hue_hist=hue_hist,
                        gray_image=preprocess_gray_template(image),
                    ))
        return templates

    def reset(self) -> None:
        """清空跨帧跟踪状态，重新开始监控或切换窗口时调用。"""
        self._tracker.reset()

    def recognize(self, frame: ndarray) -> list[BuffDetection]:
        """
        识别一帧完整客户区截图。

        :param frame: 屏幕截图（BGR/BGRA/灰度）
        :return: 本帧真正检测到的 BUFF 列表；没有模板或截图无效时返回空列表
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return []
        if not self.templates:
            return []

        roi_image, offset = _crop_roi(frame, self._roi)
        if roi_image.size == 0:
            return []
        roi_gray = _to_gray_image(roi_image)
        if roi_gray is None:
            return []

        candidates = self._collect_candidates(frame, roi_gray, offset)
        kept = _dedup_candidates(candidates)
        self._read_digits(frame, kept)
        selected = self._select_by_template(kept)

        detections = [
            TrackDetection(
                name=self.templates[candidate.template_index].name,
                center=candidate.position,
                rect=candidate.rect,
                score=candidate.score,
                category=self.templates[candidate.template_index].category,
                attribute=self.templates[candidate.template_index].attribute,
                stack=candidate.stack,
                seconds=candidate.seconds,
                has_countdown=self.templates[candidate.template_index].countdown,
            )
            for candidate in selected
        ]
        tracks = self._tracker.update(detections)
        return [
            BuffDetection(
                name=track.name,
                category=track.category,
                attribute=track.attribute,
                stack=track.stack,
                seconds=track.seconds,
                has_countdown=track.has_countdown,
                track_id=track.track_id,
                position=track.center,
                score=track.score,
            )
            for track in tracks if track.detected
        ]

    def _collect_candidates(self, frame: ndarray, roi_gray: ndarray,
                            offset: tuple[int, int]) -> list[_Candidate]:
        """逐模板匹配并做颜色二次校验，收集全部候选命中。"""
        candidates: list[_Candidate] = []
        offset_x, offset_y = offset

        for template_index, template in enumerate(self.templates):
            if template.gray_image is None:
                continue
            matches, _best_score = find_matches_gray(
                roi_gray, template.gray_image, template.threshold,
                max_cnt=MAX_MATCHES_PER_TEMPLATE)

            for match in matches:
                left, top = match["rectangle"][0]
                right, bottom = match["rectangle"][3]
                rect = (int(left + offset_x), int(top + offset_y),
                        int(right - left), int(bottom - top))
                position = (float(match["result"][0] + offset_x),
                            float(match["result"][1] + offset_y))

                if self._color_enabled and not self._color_ok(frame, rect, template):
                    continue

                candidates.append(_Candidate(
                    template_index=template_index,
                    score=float(match["confidence"]),
                    rect=rect,
                    position=position,
                ))
        return candidates

    def _color_ok(self, frame: ndarray, rect: tuple[int, int, int, int],
                  template: BuffTemplate) -> bool:
        """颜色二次校验：彩色占比 + 色相直方图。"""
        _ratio, color_diff, hue_diff = _measure_color_diff(
            frame, rect, template, self._color_saturation)
        ratio_limit = (self._color_flicker_max_diff
                       if template.countdown else self._color_max_diff)
        if color_diff > ratio_limit:
            return False
        if hue_diff is not None and hue_diff > self._color_max_hue:
            return False
        return True

    def _read_digits(self, frame: ndarray, candidates: list[_Candidate]) -> None:
        """只对最终保留的位置读取叠层/倒计时，避免相邻图标数字串读。"""
        for candidate in candidates:
            template = self.templates[candidate.template_index]
            if template.countdown:
                countdown = read_countdown(
                    frame, candidate.rect, self._digit_templates,
                    threshold=self._digit_threshold)
                if countdown is not None:
                    candidate.seconds = countdown.seconds
            stack_result = read_stack_count(
                frame, candidate.rect, self._digit_templates,
                threshold=self._digit_threshold)
            if stack_result is not None:
                candidate.stack = stack_result.count

    def _select_by_template(self, candidates: list[_Candidate]
                            ) -> list[_Candidate]:
        """同一模板每帧只保留一个结果。"""
        by_template: dict[int, list[_Candidate]] = {}
        for candidate in candidates:
            by_template.setdefault(candidate.template_index, []).append(candidate)

        selected: list[_Candidate] = []
        for template_index, items in by_template.items():
            selected.append(_choose_best(self.templates[template_index], items))
        return selected
