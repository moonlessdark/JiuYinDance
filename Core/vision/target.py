# coding: utf-8
"""
视觉识别目标描述。

设计目标：
1. 用“比例”而不是“像素”描述区域，窗口分辨率变化时不需要改代码；
2. 把“找什么、在哪里找、匹配阈值”收敛到一个不可变对象里；
3. 目标定义写在 Python 中，便于 IDE 跳转、类型检查和重构。

本版本已移除 OCR 相关字段，识别策略只保留模板匹配。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RatioRect:
    """
    相对于窗口客户区的比例矩形，取值范围均为 0~1。

    x / y 是矩形左上角比例，width / height 是宽高比例。
    例如 (0.3, 0.5, 0.4, 0.4) 表示屏幕中间偏下、宽高各占 40% 的区域。
    """

    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0

    def to_box(self, client_width: int, client_height: int) -> tuple[int, int, int, int]:
        """
        把比例矩形换算成客户区像素坐标。

        :param client_width: 客户区宽度（像素）
        :param client_height: 客户区高度（像素）
        :return: (左上角 x, 左上角 y, 右下角 x, 右下角 y)
                 返回值已做边界裁剪，无法构成有效区域时右下角会等于左上角
        """
        client_width = max(1, int(client_width))
        client_height = max(1, int(client_height))

        left = int(round(self.x * client_width))
        top = int(round(self.y * client_height))
        right = int(round((self.x + self.width) * client_width))
        bottom = int(round((self.y + self.height) * client_height))

        # 比例写错（负数、越界、宽高为 0）时统一裁剪到合法范围，避免切片报错
        left = min(max(left, 0), client_width)
        top = min(max(top, 0), client_height)
        right = min(max(right, left), client_width)
        bottom = min(max(bottom, top), client_height)
        return left, top, right, bottom


# 全屏区域，作为 TargetSpec 的默认 ROI
FULL_FRAME = RatioRect()


@dataclass(frozen=True)
class TargetSpec:
    """
    一个识别目标的完整描述。

    字段说明：
    - name：目标名称，只用于日志和诊断，必须语义清晰；
    - template：模板图片绝对路径；
    - roi：在客户区中的查找范围，使用比例描述，窗口分辨率变化时无需修改；
    - threshold：模板匹配阈值；
    - to_gray：是否转灰度匹配。彩色图标建议 False，低对比度文字按钮建议 True；
    - max_cnt：最多返回多少个结果，locate() 只取第一个，locate_all() 会使用它；
    - to_screen：是否需要把结果转换为屏幕坐标（鼠标点击使用），离线验证时设为 False；
    - fallback_scale_range：(最小比例, 最大比例, 步长)。
      为空表示不做多尺度兜底；只有尺度标定失败或主尺度匹配失败时才会使用，
      避免每个目标都做全范围暴力扫描。
    """

    name: str
    template: str = ""
    roi: RatioRect = FULL_FRAME
    threshold: float = 0.8
    to_gray: bool = True
    max_cnt: int = 1
    to_screen: bool = True
    fallback_scale_range: tuple[float, float, float] | None = None
