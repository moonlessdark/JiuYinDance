# coding: utf-8
"""
尺度自适应定位器（仅模板匹配，不含 OCR）。

解决的核心问题：模板图片按某个分辨率采集，换窗口尺寸后直接匹配必然失败。
本模块的处理顺序是“先估一次尺度，再匹配一次”，而不是每个目标都做全范围多尺度扫描。

流程：
1. ScaleCalibrator 用若干高对比度 UI 锚点，在候选比例里各找一次最佳匹配；
2. 对所有有效锚点取中位数，得到“当前窗口 / 模板采集时”的缩放比例；
3. 按窗口句柄 + 客户区尺寸缓存，窗口尺寸变化后自动重新标定；
4. Locator 把模板缩放到该比例后只匹配一次；
5. 只有主尺度失败且调用方显式配置了 fallback_scale_range 时，才做小范围多尺度兜底。

线程约束：一个 Locator 实例带缓存和最近一次诊断信息，只能被单个任务线程使用。
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import cv2
import numpy as np

from Core.vision.screen import ScreenSource
from Core.vision.target import FULL_FRAME, RatioRect, TargetSpec
from Core.vision.template import find_all_template, load_template
from Core.windows.capture import PicCapture

# 缩放后的模板缓存上限。锚点数量有限，256 足够覆盖常见窗口尺寸组合。
_SCALED_TEMPLATE_CACHE_SIZE = 256


@lru_cache(maxsize=_SCALED_TEMPLATE_CACHE_SIZE)
def _scaled_template(template_path: str, scale: float) -> Optional[np.ndarray]:
    """
    读取模板并按比例缩放（带缓存）。

    缩放模板而不是缩放截图：模板尺寸小，插值误差小、耗时低，也不会让整帧变模糊。

    :param template_path: 模板绝对路径
    :param scale: 缩放比例，1.0 表示原尺寸
    :return: 缩放后的模板；路径无效时返回 None
    """
    template = load_template(template_path)
    if template is None:
        return None
    if abs(scale - 1.0) < 1e-6:
        return template

    new_width = max(1, int(round(template.shape[1] * scale)))
    new_height = max(1, int(round(template.shape[0] * scale)))
    # 缩小用 INTER_AREA 保留细节，放大用 INTER_CUBIC 减少锯齿
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    return cv2.resize(template, (new_width, new_height), interpolation=interpolation)


@dataclass(frozen=True)
class ScaleAnchor:
    """
    尺度标定锚点。

    锚点必须满足：每帧稳定出现、随游戏 UI 缩放同步变化、图案本身有足够对比度。
    建议选任务栏、小地图边框、固定技能栏这类不变元素。

    - roi：锚点在客户区中的大概位置，用比例描述；给得越准，标定越快越稳；
    - min_confidence：低于该匹配度视为该锚点本次无效。
    """

    name: str
    template: str
    roi: RatioRect = FULL_FRAME
    min_confidence: float = 0.6
    to_gray: bool = False


@dataclass(frozen=True)
class ScaleInfo:
    """
    一次尺度标定的结果。

    - scale：估计出的缩放比例，1.0 表示与模板采集时一致；
    - valid：是否达到有效锚点数量，False 时调用方应使用 1.0 或显式兜底；
    - samples：(锚点名, 最佳比例, 匹配度) 列表，用于排查锚点选得好不好。
    """

    scale: float
    valid: bool
    samples: tuple[tuple[str, float, float], ...] = ()


class ScaleCalibrator:
    """
    用多个 UI 锚点估计当前窗口的 UI 缩放比例。

    同一锚点在不同比例下各匹配一次，取匹配度最高的比例；多锚点结果取中位数，
    这样单个锚点误匹配不会把全局比例带偏。
    """

    def __init__(self, anchors: tuple[ScaleAnchor, ...] | list[ScaleAnchor],
                 scale_min: float = 0.7, scale_max: float = 2.0,
                 step: float = 0.05, min_valid_anchors: int = 1):
        """
        :param anchors: 锚点列表
        :param scale_min: 候选比例下限
        :param scale_max: 候选比例上限
        :param step: 候选比例步长，0.05 对应最大约 2.5% 的量化误差
        :param min_valid_anchors: 至少多少个锚点有效才认为标定可信
        """
        self.anchors = tuple(anchors)
        self._scale_min = float(scale_min)
        self._scale_max = float(scale_max)
        self._step = float(step)
        self._min_valid_anchors = max(1, int(min_valid_anchors))
        self._candidate_scales = self._build_candidate_scales()

    def _build_candidate_scales(self) -> tuple[float, ...]:
        """生成候选比例列表，使用整数计数避免浮点数累积误差。"""
        if self._step <= 0 or self._scale_max <= self._scale_min:
            return (1.0,)
        count = int(round((self._scale_max - self._scale_min) / self._step)) + 1
        return tuple(round(self._scale_min + index * self._step, 4) for index in range(count))

    def calibrate(self, pic: PicCapture) -> ScaleInfo:
        """
        对一帧截图做尺度标定。

        :param pic: 完整客户区截图
        :return: 标定结果；没有锚点或截图无效时返回 scale=1.0、valid=False
        """
        if pic is None or not self.anchors:
            return ScaleInfo(scale=1.0, valid=False)

        samples: list[tuple[ScaleAnchor, float, float]] = []
        for anchor in self.anchors:
            best_scale, best_score = self._match_anchor(pic, anchor)
            if best_scale is not None:
                samples.append((anchor, best_scale, best_score))

        if not samples:
            return ScaleInfo(scale=1.0, valid=False)

        valid_scales = [scale for anchor, scale, score in samples if score >= anchor.min_confidence]
        readable_samples = tuple(
            (anchor.name, round(scale, 4), round(score, 4)) for anchor, scale, score in samples
        )
        if len(valid_scales) < self._min_valid_anchors:
            return ScaleInfo(scale=1.0, valid=False, samples=readable_samples)

        return ScaleInfo(scale=round(float(statistics.median(valid_scales)), 4),
                         valid=True, samples=readable_samples)

    def _match_anchor(self, pic: PicCapture, anchor: ScaleAnchor) -> tuple[Optional[float], float]:
        """
        在候选比例中寻找单个锚点的最佳匹配比例。

        :return: (最佳比例, 最高匹配度)；模板无效或区域为空时返回 (None, -1)
        """
        crop_result = ScreenSource.crop_ratio(pic, anchor.roi)
        if crop_result is None:
            return None, -1.0
        source_crop, _ = crop_result

        best_scale: Optional[float] = None
        best_score = -1.0
        for scale in self._candidate_scales:
            template = _scaled_template(anchor.template, scale)
            if template is None:
                continue
            # 缩放后的模板比搜索区域还大时不可能匹配
            if template.shape[0] > source_crop.shape[0] or template.shape[1] > source_crop.shape[1]:
                continue

            # 阈值传 0，目的是拿到该比例下的最高分用于比较，而不是判断是否命中
            results = find_all_template(im_source=source_crop, im_template=template,
                                        threshold=0.0, max_cnt=1, to_gray=anchor.to_gray)
            if not results:
                continue
            score = float(results[0]["confidence"])
            if score > best_score:
                best_scale, best_score = scale, score
        return best_scale, best_score


@dataclass(frozen=True)
class MatchResult:
    """
    一次成功定位的结果。

    - point：客户区坐标中的中心点；
    - screen_point：屏幕坐标，spec.to_screen=False 时为 None；
    - region：客户区坐标中的匹配区域 (x, y, width, height)；
    - scale：实际使用的缩放比例；
    - confidence：模板匹配度。
    """

    name: str
    point: tuple[float, float]
    confidence: float
    scale: float
    screen_point: Optional[tuple[int, int]]
    region: tuple[int, int, int, int]


class Locator:
    """
    按 TargetSpec 定位目标。

    使用方式：
        locator = Locator(ScreenSource(), calibrator)
        result = locator.locate(hwnd, spec)
        if result:
            result.screen_point  # 可直接给鼠标使用

    失败时返回 None，最近一次尝试过程保存在 last_diagnostic 中，便于排查是
    “没截到图 / 模板不存在 / 尺度不对 / 阈值太高”中的哪一种。
    """

    def __init__(self, screen: ScreenSource, calibrator: Optional[ScaleCalibrator] = None):
        self._screen = screen
        self._calibrator = calibrator
        # key: (hwnd, 客户区宽, 客户区高) -> ScaleInfo
        self._scale_cache: dict[tuple[int, int, int], ScaleInfo] = {}
        self._last_diagnostic: dict = {}

    @property
    def last_diagnostic(self) -> dict:
        """最近一次 locate 的诊断信息，失败排查时使用。"""
        return self._last_diagnostic

    def clear_scale_cache(self, hwnd: Optional[int] = None) -> None:
        """
        清空尺度缓存。

        :param hwnd: 只清理指定窗口；None 表示清理全部
        """
        if hwnd is None:
            self._scale_cache.clear()
            return
        for key in list(self._scale_cache.keys()):
            if key[0] == hwnd:
                del self._scale_cache[key]

    def scale_of(self, hwnd: int, pic: PicCapture) -> ScaleInfo:
        """
        获取指定帧对应的尺度信息，同一窗口尺寸只标定一次。

        :param hwnd: 窗口句柄
        :param pic: 当前帧截图
        :return: 尺度信息；没有配置标定器时返回 scale=1.0、valid=False
        """
        if self._calibrator is None or not self._calibrator.anchors or pic is None:
            return ScaleInfo(scale=1.0, valid=False)

        key = (int(hwnd), pic.pic_width, pic.pic_height)
        cached = self._scale_cache.get(key)
        if cached is not None:
            return cached

        info = self._calibrator.calibrate(pic)
        self._scale_cache[key] = info
        return info

    def locate(self, hwnd: int, spec: TargetSpec,
               pic: Optional[PicCapture] = None) -> Optional[MatchResult]:
        """
        定位单个目标，返回第一个命中结果。

        :param hwnd: 窗口句柄
        :param spec: 目标描述
        :param pic: 可选，复用调用方已经截好的图，避免同一轮重复截图
        :return: 命中结果；失败返回 None
        """
        result, _ = self.locate_with_diagnostic(hwnd=hwnd, spec=spec, pic=pic)
        return result

    def locate_first(self, hwnd: int, specs: tuple[TargetSpec, ...] | list[TargetSpec],
                     pic: Optional[PicCapture] = None) -> Optional[MatchResult]:
        """
        依次尝试多个目标，返回第一个命中结果。

        典型用途：先彩色模板、再灰度模板。

        :param hwnd: 窗口句柄
        :param specs: 目标列表，按优先级排列
        :param pic: 可选，复用同一帧截图
        :return: 第一个命中结果；全部失败返回 None
        """
        if not specs:
            return None

        if pic is None:
            pic = self._screen.capture(hwnd)
        if pic is None:
            self._last_diagnostic = {"target": specs[0].name, "reason": "截图失败", "attempts": []}
            return None

        for spec in specs:
            result = self.locate(hwnd=hwnd, spec=spec, pic=pic)
            if result is not None:
                return result
        return None

    def locate_all(self, hwnd: int, spec: TargetSpec,
                   pic: Optional[PicCapture] = None) -> list[MatchResult]:
        """
        定位目标的所有命中结果（数量受 spec.max_cnt 限制）。

        :param hwnd: 窗口句柄
        :param spec: 目标描述
        :param pic: 可选，复用调用方已经截好的图
        :return: 命中结果列表；失败返回空列表
        """
        if pic is None:
            pic = self._screen.capture(hwnd)
        if pic is None:
            self._last_diagnostic = {"target": spec.name, "reason": "截图失败", "attempts": []}
            return []

        results = self._locate_template(hwnd=hwnd, spec=spec, pic=pic, want_all=True)[0]
        # 配置了多尺度兜底时，同一目标可能被不同尺度重复命中，这里按中心点去重
        unique_results: list[MatchResult] = []
        for item in results:
            if any(abs(item.point[0] - kept.point[0]) <= 2
                   and abs(item.point[1] - kept.point[1]) <= 2 for kept in unique_results):
                continue
            unique_results.append(item)

        unique_results.sort(key=lambda item: item.confidence, reverse=True)
        if spec.max_cnt and len(unique_results) > spec.max_cnt:
            return unique_results[:spec.max_cnt]
        return unique_results

    def locate_with_diagnostic(self, hwnd: int, spec: TargetSpec,
                               pic: Optional[PicCapture] = None) -> tuple[Optional[MatchResult], dict]:
        """
        定位目标并返回诊断信息。

        :return: (命中结果或 None, 诊断字典)
        """
        if pic is None:
            pic = self._screen.capture(hwnd)
        if pic is None:
            self._last_diagnostic = {"target": spec.name, "reason": "截图失败", "attempts": []}
            return None, self._last_diagnostic

        scale_info = self.scale_of(hwnd, pic)
        results, used_scale, trace = self._locate_template(hwnd=hwnd, spec=spec, pic=pic)

        attempts = [{"strategy": "template", "tried": trace}]
        if not spec.template:
            attempts[0]["reason"] = "未配置模板"

        hit = bool(results)
        self._last_diagnostic = self._build_diagnostic(spec, pic, scale_info, attempts,
                                                       hit=hit, scale=used_scale)
        if hit:
            return results[0], self._last_diagnostic
        return None, self._last_diagnostic

    def _locate_template(self, hwnd: int, spec: TargetSpec, pic: PicCapture,
                         want_all: bool = False) -> tuple[list[MatchResult], Optional[float], list[dict]]:
        """
        执行模板匹配。

        先用标定得到的比例匹配一次；失败后仅在调用方配置了 fallback_scale_range 时
        才做多尺度兜底，并优先尝试与主比例最接近的候选，尽快命中。

        :return: (命中结果列表, 实际使用的比例, 每个比例的尝试记录)
        """
        if not spec.template:
            return [], None, []

        crop_result = ScreenSource.crop_ratio(pic, spec.roi)
        if crop_result is None:
            return [], None, []
        source_crop, (offset_x, offset_y) = crop_result

        scale_info = self.scale_of(hwnd, pic)
        primary_scale = scale_info.scale if scale_info.valid else 1.0

        candidate_scales = [primary_scale]
        if spec.fallback_scale_range is not None:
            fallback_scales = self._build_fallback_scales(spec.fallback_scale_range, primary_scale)
            candidate_scales.extend(fallback_scales)

        results: list[MatchResult] = []
        trace: list[dict] = []
        used_scale: Optional[float] = None
        for scale in candidate_scales:
            template = _scaled_template(spec.template, scale)
            if template is None:
                trace.append({"scale": scale, "confidence": -1.0, "reason": "模板读取失败"})
                continue
            if template.shape[0] > source_crop.shape[0] or template.shape[1] > source_crop.shape[1]:
                trace.append({"scale": scale, "confidence": -1.0, "reason": "模板大于搜索区域"})
                continue

            max_cnt = spec.max_cnt if want_all else 1
            matches = find_all_template(im_source=source_crop, im_template=template,
                                        threshold=spec.threshold, max_cnt=max_cnt,
                                        to_gray=spec.to_gray)
            if not matches:
                trace.append({"scale": scale, "confidence": -1.0})
                continue

            # find_all_template 已按匹配度降序返回，第一项就是该比例下的最高分
            trace.append({"scale": scale, "confidence": float(matches[0]["confidence"])})
            for match in matches:
                results.append(self._build_match_result(hwnd=hwnd, spec=spec, match=match,
                                                        offset=(offset_x, offset_y), scale=scale))
            used_scale = scale
            if not want_all:
                break

        return results, used_scale, trace

    @staticmethod
    def _build_fallback_scales(scale_range: tuple[float, float, float],
                               primary_scale: float) -> list[float]:
        """
        生成兜底候选比例。

        :param scale_range: (最小比例, 最大比例, 步长)
        :param primary_scale: 主比例，候选结果会按与它的接近程度排序
        """
        scale_min, scale_max, step = scale_range
        if step <= 0 or scale_max <= scale_min:
            return []

        count = int(round((scale_max - scale_min) / step)) + 1
        scales = [round(scale_min + index * step, 4) for index in range(count)]
        # 去掉与主比例重复的候选，避免同一比例匹配两次
        scales = [scale for scale in scales if abs(scale - primary_scale) > 1e-6]
        scales.sort(key=lambda value: abs(value - primary_scale))
        return scales

    def _build_match_result(self, hwnd: int, spec: TargetSpec, match: dict,
                            offset: tuple[int, int], scale: float) -> MatchResult:
        """把 find_all_template 的结果转换为客户区/屏幕坐标。"""
        left, top = match["rectangle"][0]
        right, bottom = match["rectangle"][3]
        offset_x, offset_y = offset

        client_x = float(match["result"][0] + offset_x)
        client_y = float(match["result"][1] + offset_y)
        screen_point = self._screen.to_screen(hwnd, (client_x, client_y)) if spec.to_screen else None

        return MatchResult(
            name=spec.name,
            point=(client_x, client_y),
            confidence=float(match["confidence"]),
            scale=scale,
            screen_point=screen_point,
            region=(int(left + offset_x), int(top + offset_y),
                    int(right - left), int(bottom - top)),
        )

    @staticmethod
    def _build_diagnostic(spec: TargetSpec, pic: PicCapture, scale_info: ScaleInfo,
                          attempts: list[dict], hit: bool, scale: Optional[float]) -> dict:
        """组装诊断信息，失败时用来判断问题出在尺度、阈值还是素材。"""
        return {
            "target": spec.name,
            "hit": hit,
            "frame_size": (pic.pic_width, pic.pic_height),
            "scale": scale_info.scale,
            "scale_valid": scale_info.valid,
            "scale_samples": scale_info.samples,
            "used_scale": scale,
            "attempts": attempts,
        }


def clear_scaled_template_cache() -> None:
    """
    清空缩放模板缓存。

    模板文件被外部替换后，需要同时调用 Core.vision.template.clear_template_cache()
    和本函数，否则可能继续使用旧的缩放结果。
    """
    _scaled_template.cache_clear()
