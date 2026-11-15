# coding: utf-8
"""
挑战点兑换书页。

全流程都是模板匹配，没有 OCR：
1. 检查技能书页、兑换窗口是否存在；
2. 依次点击夺魄书页、兑换按钮、背包书页、回收栏、结果预览；
3. 点击确认兑换和二次确认。

识别优化（第二轮开始生效）：
- 首次匹配成功后记录图标在客户区中的坐标，后续优先在该坐标附近的小 ROI 内匹配；
- 小 ROI 未命中时回退全屏匹配，命中后更新坐标，未命中则保留旧坐标；
- 客户区尺寸变化时缓存自动作废，连续两次全屏失配也会丢弃缓存；
- ROI 命中要求比全屏更高的置信度，避免小区域里误匹配到相邻图标。

图标允许玩家拖动，所以缓存只是“优先尝试”，全屏兜底必须保留。
坐标缓存只在本任务线程内使用，不做跨线程共享。
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from Core.vision.locator import MatchResult
from Core.vision.target import RatioRect, TargetSpec
from Core.vision.template import load_template
from Core.windows.capture import PicCapture, WindowsCapture
from Utils.resource_config import get_resources

from DeskFunc.v2.TaskBussinese.common_operations import CommonOperations


@dataclass
class _TargetCache:
    """单个图标的坐标缓存。"""

    point: tuple[float, float]  # 客户区坐标中心点
    frame_size: tuple[int, int]  # 写入缓存时的客户区尺寸
    misses: int = 0  # 连续全屏失配次数


class ChallengePointExchange:
    """挑战点兑换书页的界面操作。"""

    # ROI 命中要求比全屏阈值更高，避免小区域里误匹配到相邻图标
    CACHE_CONFIDENCE_MARGIN = 0.02
    # 连续多少次全屏都找不到就丢弃该目标的缓存
    CACHE_CLEAR_MISSES = 2
    # ROI 在图标四周额外留出的搜索边距（像素）
    ROI_MIN_MARGIN = 40
    ROI_MARGIN_RATIO = 0.6
    # 允许的坐标偏差下限（像素），超出说明匹配到的不是缓存的那个图标
    CACHE_NEAR_MIN = 40.0

    def __init__(self):
        config = get_resources().challenge_point_2_lucky_money
        self._common = CommonOperations()
        self._capture = WindowsCapture()

        # 兑换相关按钮都比较小，统一使用 0.9 的严格阈值
        self.spec_shop_book = TargetSpec(
            name="夺魄书页",
            template=config.challenge_point_shop_book,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_book_page = TargetSpec(
            name="技能书页",
            template=config.challenge_point_book_page,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_exchange_button = TargetSpec(
            name="书页兑换按钮",
            template=config.challenge_point_exchange_button,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_backpack_item = TargetSpec(
            name="背包中的书页",
            template=config.backpack_item_pic,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_recycle_box = TargetSpec(
            name="回收物品存放栏",
            template=config.recycle_box,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_recycle_result = TargetSpec(
            name="兑换结果预览",
            template=config.recycle_box_result,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_exchange_ok = TargetSpec(
            name="确定兑换",
            template=config.exchange_ok,
            threshold=0.9,
            to_gray=True,
        )
        self.spec_exchange_re_ok = TargetSpec(
            name="二次确认兑换",
            template=config.exchange_re_ok,
            threshold=0.9,
            to_gray=True,
        )
        # 偶发弹窗：出现后会遮挡兑换界面，必须先点掉才能继续识别
        self.spec_continue_practice = TargetSpec(
            name="继续修炼弹窗",
            template=config.continue_practice,
            threshold=0.85,
            to_gray=True,
        )

        # key: TargetSpec.name -> 坐标缓存
        self._cache: dict[str, _TargetCache] = {}
        self._last_hit_mode = "miss"

    @property
    def last_hit_mode(self) -> str:
        """最近一次定位的命中方式：roi / full / miss，用于失败排查。"""
        return self._last_hit_mode

    def capture(self, hwnd: int) -> Optional[PicCapture]:
        """截取客户区，供调用方在同一帧上连续识别多个目标。"""
        return self._capture.capture(hwnd)

    def locate_target(self, hwnd: int, spec: TargetSpec,
                      pic: Optional[PicCapture] = None) -> Optional[MatchResult]:
        """
        定位目标：缓存 ROI 优先，全屏兜底。

        :param hwnd: 窗口句柄
        :param spec: 目标描述
        :param pic: 可选，复用调用方已经截好的图
        :return: 命中结果；未命中返回 None
        """
        if pic is None:
            pic = self._capture.capture(hwnd)
        if pic is None:
            self._last_hit_mode = "miss"
            return None

        frame_size = (pic.pic_width, pic.pic_height)
        cache = self._cache.get(spec.name)
        if cache is not None and cache.frame_size != frame_size:
            # 客户区尺寸变化后，图标位置和尺寸都可能变化，缓存直接作废
            del self._cache[spec.name]
            cache = None

        if cache is not None:
            fast_spec, tolerance = self._build_cache_spec(spec, cache, pic)
            if fast_spec is not None:
                result = self._common.locate(hwnd, fast_spec, pic=pic)
                if result is not None and self._accept_cached_result(spec, result, cache, tolerance):
                    cache.point = result.point
                    cache.misses = 0
                    self._last_hit_mode = "roi"
                    return result

        result = self._common.locate(hwnd, spec, pic=pic)
        if result is not None:
            self._write_cache(spec, result.point, frame_size)
            self._last_hit_mode = "full"
            return result

        # 全屏也没找到才累计失配次数，ROI 失败不影响缓存
        if cache is not None:
            cache.misses += 1
            if cache.misses >= self.CACHE_CLEAR_MISSES:
                del self._cache[spec.name]
        self._last_hit_mode = "miss"
        return None

    def click_match(self, hwnd: int, match: Optional[MatchResult],
                    react_delay: float = 0.3) -> bool:
        """点击匹配结果中心点对应的屏幕坐标。"""
        if match is None or match.screen_point is None:
            return False
        return self._common.mouse_click_pos(hwnd, match.screen_point, 0, react_delay=react_delay)

    def check_pic_template_exist(self, hwnd: int) -> int:
        """
        检查兑换所需的关键界面是否存在。

        :return: -1 未找到技能书页；-2 未找到兑换窗口；0 正常
        """
        pic = self._capture.capture(hwnd)
        if pic is None:
            return -2
        book_page = self.locate_target(hwnd, self.spec_book_page, pic=pic)
        recycle_box = self.locate_target(hwnd, self.spec_recycle_box, pic=pic)
        if book_page is None:
            return -1
        if recycle_box is None:
            return -2
        return 0

    def _write_cache(self, spec: TargetSpec, point: tuple[float, float],
                     frame_size: tuple[int, int]) -> None:
        """全屏命中后写入或刷新坐标缓存。"""
        cache = self._cache.get(spec.name)
        if cache is None:
            self._cache[spec.name] = _TargetCache(point=point, frame_size=frame_size)
            return
        cache.point = point
        cache.frame_size = frame_size
        cache.misses = 0

    def _accept_cached_result(self, spec: TargetSpec, result: MatchResult,
                              cache: _TargetCache, tolerance: float) -> bool:
        """
        判断 ROI 内的匹配结果是否可以采信。

        条件：
        1. 置信度必须高于全屏阈值（ROI 小，相邻图标误匹配概率更高）；
        2. 命中点不能偏离缓存点太远，否则说明匹配到的是另一个相似图标。
        """
        min_confidence = min(spec.threshold + self.CACHE_CONFIDENCE_MARGIN, 0.99)
        if result.confidence < min_confidence:
            return False
        return (abs(result.point[0] - cache.point[0]) <= tolerance
                and abs(result.point[1] - cache.point[1]) <= tolerance)

    def _build_cache_spec(self, spec: TargetSpec, cache: _TargetCache,
                          pic: PicCapture) -> tuple[Optional[TargetSpec], float]:
        """
        以缓存点为中心构造小 ROI 的 TargetSpec。

        ROI 大小 = 图标尺寸 + 四周搜索边距：边距既覆盖玩家轻微拖动，
        也给点击/渲染误差留出余量。

        :return: (带 ROI 的 spec, 允许的坐标偏差)；无法构造时返回 (None, 0.0)
        """
        template = load_template(spec.template)
        if template is None:
            return None, 0.0

        template_height, template_width = template.shape[:2]
        margin_x = max(self.ROI_MIN_MARGIN, int(template_width * self.ROI_MARGIN_RATIO))
        margin_y = max(self.ROI_MIN_MARGIN, int(template_height * self.ROI_MARGIN_RATIO))

        center_x, center_y = cache.point
        left = max(0, int(center_x - template_width / 2) - margin_x)
        top = max(0, int(center_y - template_height / 2) - margin_y)
        right = min(pic.pic_width, int(center_x + template_width / 2) + margin_x)
        bottom = min(pic.pic_height, int(center_y + template_height / 2) + margin_y)

        # ROI 裁到客户区边界后必须还能放下完整模板
        if right - left < template_width or bottom - top < template_height:
            return None, 0.0

        roi = RatioRect(
            x=left / pic.pic_width,
            y=top / pic.pic_height,
            width=(right - left) / pic.pic_width,
            height=(bottom - top) / pic.pic_height,
        )
        tolerance = max(self.CACHE_NEAR_MIN, float(max(margin_x, margin_y)))
        return replace(spec, roi=roi), tolerance
