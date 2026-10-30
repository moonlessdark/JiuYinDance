# coding: utf-8
"""
ShowBuff 状态面板渲染。

业务背景：
1. 每个 BUFF 图标都有“图标类型”（内功 / 武学）和“图标属性”
   （叠层 / 增伤 / 恢复 / 防御）；
2. Resources/ImageTemplate/PicBuff/ShowBuff 下的大图标用于单独展示对应属性的效果；
3. 状态面板按“内功”“武学”分区，只展示当前帧已激活的属性槽位，
   槽位内列出命中的 BUFF 名称、叠层数和倒计时；未检测到大图标时只显示提示行。

布局设置：
- 通过 PanelSettings 指定“大图标尺寸”和“布局模式”；
- 布局支持“2 行 N 列”（内功、武学各占一行）和“N 行 1 列”（纵向排列）；
- 卡片（大图标 + 右侧 BUFF 信息）保持固定宽高比例，随大图标尺寸整体缩放。

倒计时展现形式：
- 使用横向进度条表示“剩余时间占该 BUFF 观测到的最长倒计时的比例”，
  并在进度条右侧显示“12秒”这样的数字；
- 进度条颜色随剩余比例变化（充足为绿色、偏少为琥珀色、即将结束为红色），
  这样既能直观看到剩余比例，又不会丢失精确秒数；
- 该 BUFF 没有倒计时读数时显示灰色空进度条和“--”。

中文文字使用 PySide6 的 QPainter 离屏绘制，避免 OpenCV putText 不支持中文。
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, replace
from typing import Optional

import cv2
import numpy as np
from numpy import ndarray

# 属性顺序固定，保证每帧面板的槽位位置稳定，便于逐帧对比
ATTRIBUTE_ORDER = ("叠层", "增伤", "恢复", "防御")
# 业务上只有这两种图标类型，面板始终渲染这两个分区
CATEGORY_ORDER = ("内功", "武学")

# 大图标文件名约定：状态_叠层.png、状态_增伤.png ...
_SHOW_ICON_PREFIX = "状态_"

# 分区强调色，BGRA/RGB 使用同一组分量
_CATEGORY_COLORS = {
    "内功": (78, 200, 156),
    "武学": (238, 158, 68),
}

# 面板外框布局常量（像素，不随卡片缩放）
_MARGIN = 10
_TITLE_HEIGHT = 30
_SECTION_HEADER_HEIGHT = 22
_SECTION_GAP = 8
_CARD_GAP = 8
_INACTIVE_HEIGHT = 18

# 卡片基准尺寸（scale=1）。大图标尺寸变化时，卡片内部所有尺寸等比缩放，
# 保证“大图标”和右侧 BUFF 信息区的宽高比例始终固定。
_CARD_WIDTH = 180
_CARD_PADDING = 8
_TEXT_GAP = 6
_ATTR_HEIGHT = 20
_ICON_SIZE = 62
_ENTRY_HEIGHT = 32
_ENTRY_BASE_HEIGHT = 20

# 允许的大图标尺寸范围，主界面设置对话框也复用这组边界
ICON_SIZE_MIN = 48
ICON_SIZE_MAX = 160

# 卡片内文字基准字号（像素，随 scale 缩放）
_FONT_ATTR = 15
_FONT_NAME = 13
_FONT_SMALL = 9
# 小尺寸下的字号下限：大图标调得很小时文字仍然保持可读，避免糊成一团
_FONT_ATTR_MIN = 12
_FONT_NAME_MIN = 11
_FONT_SMALL_MIN = 8

# 倒计时进度条分档颜色：剩余比例 >= 0.5 / >= 0.25 / 其他
_BAR_COLORS = (
    (94, 200, 120),
    (240, 180, 70),
    (230, 90, 80),
)

# 中文界面统一字体：Windows 优先微软雅黑，缺失时由 Qt 自动回退
_CN_FONT = "Microsoft YaHei"

_app = None


@dataclass(frozen=True)
class BuffState:
    """
    单个 BUFF 在某一帧的展示数据。

    - name：BUFF 名称，例如“云海”；
    - category：图标类型，内功 / 武学；
    - attribute：图标属性，叠层 / 增伤 / 恢复 / 防御；
    - stack：图标右下角叠层数，注意与属性“叠层”没有关联；
    - seconds：底部倒计时剩余秒数（浮点，用于进度条平滑变化），
      未读取到时为 None；
    - has_countdown：该 BUFF 是否配置了倒计时元素。为 False 时
      大图标下方不绘制进度条和秒数文字；
    - track_id：跨帧跟踪 ID，用于区分两个同名 BUFF 的倒计时；
    - position：图标中心在截图中的坐标，便于排查同名 BUFF 的位置；
    - score：模板匹配度，便于面板/日志排查。
    """

    name: str
    category: str
    attribute: str
    stack: Optional[int] = None
    seconds: Optional[float] = None
    has_countdown: bool = False
    track_id: int = -1
    position: Optional[tuple[float, float]] = None
    score: float = 0.0


@dataclass(frozen=True)
class PanelSettings:
    """
    状态面板展示设置。

    - icon_size：大图标边长（像素），卡片内部其它尺寸按比例缩放；
    - layout_mode：rows 表示“2 行 N 列”，column 表示“N 行 1 列”；
    - show_attr_label：是否在图标下方显示属性名（叠层/增伤/恢复/防御）；
    - background_alpha：面板与卡片背景透明度，0 完全透明、255 完全不透明。
    """

    icon_size: int = _ICON_SIZE
    layout_mode: str = "rows"
    show_attr_label: bool = False
    background_alpha: int = 0


@dataclass(frozen=True)
class _Metrics:
    """卡片内部所有可缩放尺寸的集合，由统一 scale 计算得到。"""

    scale: float
    card_width: int
    card_padding: int
    text_gap: int
    icon_size: int
    icon_label_gap: int
    attr_height: int
    entry_height: int
    entry_base_height: int
    card_radius: int
    font_attr: int
    font_name: int
    font_small: int


@dataclass
class _PanelPlan:
    """一次渲染采用的排版方案。"""

    mode: str  # rows：2 行 N 列；column：N 行 1 列
    metrics: _Metrics
    columns: int
    show_attr_label: bool
    background_alpha: int
    # (分类, 属性) -> 卡片高度（已按 scale 计算）
    card_heights: dict[tuple[str, str], int]
    # (分类, 属性) -> 动画前的完整高度，用于固定内容位置，避免淡入淡出时文字滑动
    base_card_heights: dict[tuple[str, str], int] = field(default_factory=dict)
    # (分类, 属性) -> 卡片动画进度（0 消失、1 完全显示），用于淡入淡出
    progress: dict[tuple[str, str], float] = field(default_factory=dict)


def load_show_icons(directory: str) -> dict[str, ndarray]:
    """
    加载 ShowBuff 大图标。

    文件名约定为 `状态_{属性}.png`，例如 `状态_叠层.png`。
    缺图不会中断流程，只是对应属性槽位不显示大图标。

    :param directory: ShowBuff 目录
    :return: {属性: BGRA/BGR 图}
    """
    icons: dict[str, ndarray] = {}
    for attribute in ATTRIBUTE_ORDER:
        path = os.path.join(directory, f"{_SHOW_ICON_PREFIX}{attribute}.png")
        image = _read_image(path)
        if image is None:
            print(f"ShowBuff 大图标读取失败，已跳过：{path}")
            continue
        icons[attribute] = image
    return icons


def render_state_panel(states: list[BuffState],
                       icons: dict[str, ndarray],
                       max_seconds_by_buff: dict[object, int],
                       title: str,
                       settings: Optional[PanelSettings] = None,
                       slot_order: Optional[dict[str, list[str]]] = None,
                       pixel_ratio: float = 1.0,
                       card_progress: Optional[
                           dict[tuple[str, str], float]] = None,
                       ghost_entries: Optional[
                           dict[tuple[str, str], list[BuffState]]] = None
                       ) -> ndarray:
    """
    渲染一帧的 BUFF 状态面板。

    只有当前帧真正命中的属性才会生成卡片：未激活的大图标和空槽位直接省略，
    面板宽高随激活数量变化，避免界面里出现大量灰色占位。

    :param states: 本帧命中的 BUFF 列表
    :param icons: 属性 -> 大图标
    :param max_seconds_by_buff: BUFF 名称 -> 历史最大倒计时，用于进度条比例
    :param title: 面板标题，通常为帧文件名
    :param settings: 大图标尺寸与布局模式；不传时使用默认设置
    :param slot_order: 分类 -> 属性出现顺序；用于保持新图标追加、旧图标前移
    :param pixel_ratio: 高分屏渲染倍率，输出文件保持 1.0
    :param card_progress: (分类, 属性) -> 动画进度，0 隐藏、1 完全显示；
        不传时所有卡片直接按完全显示渲染
    :param ghost_entries: (分类, 属性) -> 消失前的卡片内容，用于淡出动画
    :return: BGRA 图片
    """
    _ensure_app()
    from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter

    settings = settings or PanelSettings()
    raw_progress = card_progress or {}
    animated = card_progress is not None

    def progress_of(key: tuple[str, str]) -> float:
        """读取指定卡片的动画进度，缺省视为完全显示。"""
        return max(0.0, min(1.0, raw_progress.get(key, 1.0)))

    grouped: dict[tuple[str, str], list[BuffState]] = {}
    for state in states:
        key = (state.category, state.attribute)
        # 动画刚出现时进度可能还是 0，此时先不参与布局
        if animated and progress_of(key) <= 0.0:
            continue
        grouped.setdefault(key, []).append(state)

    # 正在淡出的卡片用消失前的快照继续参与布局，避免瞬间塌陷
    for key, entries in (ghost_entries or {}).items():
        if key in grouped or not entries:
            continue
        if animated and progress_of(key) <= 0.0:
            continue
        grouped[key] = entries

    # 每个分类只保留有命中 BUFF 的属性；有传入顺序时按“出现先后”排列
    visible: dict[str, list[str]] = {}
    for category in CATEGORY_ORDER:
        active = {attribute for attribute in ATTRIBUTE_ORDER
                  if grouped.get((category, attribute))}
        order = list(slot_order.get(category, [])) if slot_order else []
        ordered = [attribute for attribute in order if attribute in active]
        # 兜底：把尚未记录进顺序的激活属性追加到末尾
        ordered.extend(attribute for attribute in ATTRIBUTE_ORDER
                       if attribute in active and attribute not in ordered)
        visible[category] = ordered

    plan = _plan_panel(grouped, visible, settings, pixel_ratio)

    # 宽屏布局下同一分类保持统一基准高度，动画时只让新增/消失的卡片伸缩
    if plan.mode == "rows":
        for category in CATEGORY_ORDER:
            heights = [plan.card_heights[(category, attribute)]
                       for attribute in visible[category]]
            if not heights:
                continue
            uniform_height = max(heights)
            for attribute in visible[category]:
                plan.card_heights[(category, attribute)] = uniform_height

    # 记录动画前的完整高度，内容按完整高度布局，动画时只裁剪不滑动
    base_card_heights = dict(plan.card_heights)

    # 按动画进度缩放卡片高度并记录透明度，进度为 1 时与普通渲染完全一致
    if animated:
        eased_progress: dict[tuple[str, str], float] = {}
        for key, height in list(plan.card_heights.items()):
            eased = _ease(progress_of(key))
            eased_progress[key] = eased
            plan.card_heights[key] = max(1, int(round(height * eased)))
        plan = replace(plan, progress=eased_progress,
                       base_card_heights=base_card_heights)
    else:
        plan.progress = {key: 1.0 for key in plan.card_heights}
        plan.base_card_heights = base_card_heights

    metrics = plan.metrics

    # 面板尺寸：先按方案算出卡片区，再保证标题不会被裁掉
    panel_width, panel_height = _panel_size(plan, visible, title)

    image = QImage(panel_width, panel_height, QImage.Format_ARGB32)
    # 背景透明度可配置：0 表示完全透明，仅保留图标、文字和边框
    image.fill(QColor(13, 17, 23, plan.background_alpha))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    _draw_title(painter, title, panel_width)

    if plan.mode == "rows":
        _draw_rows_layout(painter, plan, visible, grouped, icons,
                          max_seconds_by_buff)
    else:
        _draw_column_layout(painter, plan, visible, grouped, icons,
                            max_seconds_by_buff)

    painter.end()
    return _qimage_to_bgra(image)


def _sp(value: float, scale: float) -> int:
    """按缩放比例计算像素值，至少保留 1px。"""
    return max(1, int(round(value * scale)))


def _ease(progress: float) -> float:
    """平滑缓动曲线，让卡片出现/消失的透明度与高度变化更自然。"""
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def _make_metrics(scale: float, pixel_ratio: float = 1.0) -> _Metrics:
    """
    根据统一缩放比例生成卡片内部尺寸。

    pixel_ratio 用于高分屏：所有像素乘以倍率渲染，再由 QImage 标记逻辑尺寸，
    避免窗口把低分辨率图片放大造成模糊。字号同时设置下限，防止小图标糊字。
    """
    physical_scale = scale * pixel_ratio

    def size(base: float, minimum: float = 0.0) -> int:
        value = max(base * physical_scale, minimum * pixel_ratio)
        return max(1, int(round(value)))

    font_attr = size(_FONT_ATTR, _FONT_ATTR_MIN)
    font_name = size(_FONT_NAME, _FONT_NAME_MIN)
    font_small = size(_FONT_SMALL, _FONT_SMALL_MIN)
    return _Metrics(
        scale=physical_scale,
        card_width=size(_CARD_WIDTH),
        card_padding=size(_CARD_PADDING),
        text_gap=size(_TEXT_GAP),
        icon_size=size(_ICON_SIZE),
        icon_label_gap=size(4),
        attr_height=size(_ATTR_HEIGHT, _FONT_ATTR_MIN + 6),
        entry_height=size(_ENTRY_HEIGHT, _FONT_NAME_MIN + 20),
        entry_base_height=size(_ENTRY_BASE_HEIGHT, _FONT_NAME_MIN + 8),
        card_radius=size(10),
        font_attr=font_attr,
        font_name=font_name,
        font_small=font_small,
    )


def _entry_height(entry: BuffState, metrics: _Metrics) -> int:
    """单条 BUFF 的占用高度：有倒计时元素时多预留一行进度条。"""
    return metrics.entry_height if entry.has_countdown else metrics.entry_base_height


def _card_height(entries: list[BuffState], metrics: _Metrics,
                 show_attr_label: bool = True) -> int:
    """
    计算单张属性卡片高度。

    左侧是“大图标 + 下方属性名”（隐藏属性名时只算图标），
    右侧是 BUFF 明细，取两者较高的一方。
    """
    entries_height = sum(_entry_height(entry, metrics) for entry in entries)
    icon_block = metrics.icon_size
    if show_attr_label:
        icon_block += metrics.icon_label_gap + metrics.attr_height
    body = max(icon_block, entries_height)
    return metrics.card_padding * 2 + body


def _plan_panel(grouped: dict[tuple[str, str], list[BuffState]],
                visible: dict[str, list[str]],
                settings: PanelSettings,
                pixel_ratio: float = 1.0) -> _PanelPlan:
    """
    根据用户设置生成排版方案。

    大图标尺寸决定统一的 scale，卡片内部所有尺寸等比缩放；
    布局模式直接采用设置里的 rows / column，不再随窗口大小自动切换。
    """
    icon_size = max(ICON_SIZE_MIN, min(ICON_SIZE_MAX, int(settings.icon_size)))
    scale = icon_size / _ICON_SIZE
    mode = settings.layout_mode if settings.layout_mode in ("rows", "column") \
        else "rows"
    metrics = _make_metrics(scale, pixel_ratio)
    columns = max((len(items) for items in visible.values()), default=1)
    columns = max(1, columns)
    show_attr_label = bool(settings.show_attr_label)
    background_alpha = max(0, min(255, int(settings.background_alpha)))
    card_heights = {
        (category, attribute): _card_height(
            grouped[(category, attribute)], metrics, show_attr_label)
        for category in CATEGORY_ORDER
        for attribute in visible[category]
    }
    return _PanelPlan(mode=mode, metrics=metrics, columns=columns,
                      show_attr_label=show_attr_label,
                      background_alpha=background_alpha,
                      card_heights=card_heights)


def _section_card_height(plan: _PanelPlan, category: str,
                         visible: dict[str, list[str]]) -> int:
    """rows 方案下同一分类的卡片统一等高，取该分类最高的卡片。"""
    return max((plan.card_heights[(category, attribute)]
                for attribute in visible[category]), default=0)


def _panel_size(plan: _PanelPlan, visible: dict[str, list[str]],
                title: str) -> tuple[int, int]:
    """根据排版方案计算最终面板宽高，并保证标题完整显示。"""
    from PySide6.QtGui import QFont, QFontMetrics

    metrics = plan.metrics
    if plan.mode == "rows":
        width = (_MARGIN * 2 + plan.columns * metrics.card_width
                 + (plan.columns - 1) * _CARD_GAP)
        height = (_MARGIN * 2 + _TITLE_HEIGHT
                  + (len(CATEGORY_ORDER) - 1) * _SECTION_GAP)
        for category in CATEGORY_ORDER:
            height += _SECTION_HEADER_HEIGHT
            if visible[category]:
                height += _section_card_height(plan, category, visible)
            else:
                height += _INACTIVE_HEIGHT
    else:
        width = _MARGIN * 2 + metrics.card_width
        height = (_MARGIN * 2 + _TITLE_HEIGHT
                  + (len(CATEGORY_ORDER) - 1) * _SECTION_GAP)
        for category in CATEGORY_ORDER:
            height += _SECTION_HEADER_HEIGHT
            if visible[category]:
                for index, attribute in enumerate(visible[category]):
                    if index:
                        height += _CARD_GAP
                    height += plan.card_heights[(category, attribute)]
            else:
                height += _INACTIVE_HEIGHT

    # 面板可能只剩一个槽位，宽度不能小于标题本身，否则帧文件名会被裁掉
    title_text = f"BUFF 状态面板  {title}"
    title_font = QFont(_CN_FONT)
    title_font.setPixelSize(15)
    title_font.setBold(True)
    title_width = QFontMetrics(title_font).horizontalAdvance(title_text)
    width = max(width, title_width + _MARGIN * 2)
    return width, height


def _draw_rows_layout(painter, plan: _PanelPlan,
                      visible: dict[str, list[str]],
                      grouped: dict[tuple[str, str], list[BuffState]],
                      icons: dict[str, ndarray],
                      max_seconds_by_buff: dict[object, int]) -> None:
    """宽屏布局：每个分类占一行，分类内卡片横向排列。"""
    metrics = plan.metrics
    y = _MARGIN + _TITLE_HEIGHT
    for category in CATEGORY_ORDER:
        color = _CATEGORY_COLORS.get(category, (200, 200, 200))
        active = bool(visible[category])
        _draw_section_header(painter, category, color, y, active)

        card_y = y + _SECTION_HEADER_HEIGHT
        if active:
            # 同一分类基准高度一致；动画时各卡片按自身进度伸缩
            section_height = _section_card_height(plan, category, visible)
            for index, attribute in enumerate(visible[category]):
                card_height = plan.card_heights[(category, attribute)]
                card_x = (_MARGIN + index * (metrics.card_width + _CARD_GAP))
                _draw_card(
                    painter, card_x, card_y, metrics.card_width, card_height,
                    attribute, color, grouped[(category, attribute)],
                    icons.get(attribute), metrics, max_seconds_by_buff,
                    plan.show_attr_label, plan.background_alpha,
                    plan.progress.get((category, attribute), 1.0),
                    plan.base_card_heights.get(
                        (category, attribute), card_height))
            y = card_y + section_height
        else:
            _draw_inactive_hint(painter, card_y)
            y = card_y + _INACTIVE_HEIGHT
        y += _SECTION_GAP


def _draw_column_layout(painter, plan: _PanelPlan,
                        visible: dict[str, list[str]],
                        grouped: dict[tuple[str, str], list[BuffState]],
                        icons: dict[str, ndarray],
                        max_seconds_by_buff: dict[object, int]) -> None:
    """窄屏布局：所有卡片纵向排成一列，分类标题照常分节。"""
    metrics = plan.metrics
    y = _MARGIN + _TITLE_HEIGHT
    for category in CATEGORY_ORDER:
        color = _CATEGORY_COLORS.get(category, (200, 200, 200))
        active = bool(visible[category])
        _draw_section_header(painter, category, color, y, active)

        card_y = y + _SECTION_HEADER_HEIGHT
        if active:
            for index, attribute in enumerate(visible[category]):
                card_height = plan.card_heights[(category, attribute)]
                _draw_card(
                    painter, _MARGIN, card_y, metrics.card_width, card_height,
                    attribute, color, grouped[(category, attribute)],
                    icons.get(attribute), metrics, max_seconds_by_buff,
                    plan.show_attr_label, plan.background_alpha,
                    plan.progress.get((category, attribute), 1.0),
                    plan.base_card_heights.get(
                        (category, attribute), card_height))
                card_y += card_height
                if index < len(visible[category]) - 1:
                    card_y += _CARD_GAP
            y = card_y
        else:
            _draw_inactive_hint(painter, card_y)
            y = card_y + _INACTIVE_HEIGHT
        y += _SECTION_GAP


def _draw_title(painter, title: str, panel_width: int) -> None:
    """绘制面板标题。"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont

    font = QFont(_CN_FONT)
    font.setPixelSize(15)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(232, 238, 246))
    painter.drawText(
        QRectF(_MARGIN, _MARGIN, panel_width - _MARGIN * 2, _TITLE_HEIGHT - 8),
        int(Qt.AlignLeft | Qt.AlignVCenter),
        f"BUFF 状态面板  {title}",
    )


def _draw_section_header(painter, category: str, color: tuple[int, int, int],
                         y: int, active: bool) -> None:
    """绘制“内功 / 武学”分区标题和强调色竖条。"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont

    display_color = QColor(*color) if active else QColor(110, 118, 130)
    painter.setPen(Qt.NoPen)
    painter.setBrush(display_color)
    painter.drawRoundedRect(QRectF(_MARGIN, y + 4, 3, 14), 2, 2)

    font = QFont(_CN_FONT)
    font.setPixelSize(14)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(display_color)
    painter.drawText(
        QRectF(_MARGIN + 10, y, 160, _SECTION_HEADER_HEIGHT),
        int(Qt.AlignLeft | Qt.AlignVCenter),
        f"{category}状态",
    )


def _draw_inactive_hint(painter, y: int) -> None:
    """分类未命中时只显示一行提示，不绘制任何大图标。"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont

    font = QFont(_CN_FONT)
    font.setPixelSize(12)
    painter.setFont(font)
    painter.setPen(QColor(105, 113, 125))
    painter.drawText(
        QRectF(_MARGIN + 10, y, 200, _INACTIVE_HEIGHT),
        int(Qt.AlignLeft | Qt.AlignVCenter),
        "未检测到激活状态",
    )


def _draw_card(painter, x: int, y: int, width: int, height: int,
               attribute: str, color: tuple[int, int, int],
               entries: list[BuffState], icon: Optional[ndarray],
               metrics: _Metrics,
               max_seconds_by_buff: dict[object, int],
               show_attr_label: bool = True,
               background_alpha: int = 255,
               progress: float = 1.0,
               content_height: Optional[int] = None) -> None:
    """绘制单个已激活属性槽位：左侧大图标（可按设置隐藏名称），右侧 BUFF 明细。"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QPen

    if progress <= 0.0:
        return
    # 淡入淡出时整体降低透明度，并裁剪到动画后的卡片高度，形成展开/收拢效果
    painter.save()
    painter.setOpacity(max(0.0, min(1.0, progress)))
    painter.setClipRect(QRectF(x, y, width, height))

    painter.setBrush(QColor(24, 30, 38, background_alpha))
    painter.setPen(QPen(QColor(color[0], color[1], color[2], 190), 1.4))
    painter.drawRoundedRect(
        QRectF(x, y, width, height), metrics.card_radius, metrics.card_radius)

    icon_x = x + metrics.card_padding
    icon_y = y + metrics.card_padding
    if icon is not None:
        target = QRectF(icon_x, icon_y, metrics.icon_size, metrics.icon_size)
        painter.drawImage(target, bgr_to_qimage(icon))

    # 属性名放在大图标正下方并居中对齐；用户可在设置中关闭
    if show_attr_label:
        label_y = icon_y + metrics.icon_size + metrics.icon_label_gap
        label_font = QFont(_CN_FONT)
        label_font.setPixelSize(metrics.font_attr)
        label_font.setBold(True)
        painter.setFont(label_font)
        painter.setPen(QColor(*color))
        painter.drawText(
            QRectF(icon_x, label_y, metrics.icon_size, metrics.attr_height),
            int(Qt.AlignHCenter | Qt.AlignVCenter),
            attribute,
        )

    # 右侧信息区：多条 BUFF 作为整体垂直居中，条目之间保持紧凑间距，
    # 剩余高度平均留在顶部和底部，避免条目被拉到卡片上下两端。
    text_x = icon_x + metrics.icon_size + metrics.text_gap
    text_width = max(1, x + width - metrics.card_padding - text_x)
    entries_height = sum(_entry_height(entry, metrics) for entry in entries)
    body_y = y + metrics.card_padding
    # 内容按完整高度布局，动画时只被裁剪，避免文字随着卡片伸缩上下滑动
    layout_height = content_height if content_height is not None else height
    body_height = max(0, layout_height - metrics.card_padding * 2)
    row_y = float(body_y + max(0, (body_height - entries_height) // 2))
    for entry in entries:
        _draw_entry(painter, text_x, int(round(row_y)), text_width, entry,
                    color, metrics, max_seconds_by_buff)
        row_y += _entry_height(entry, metrics)
    painter.restore()


def _draw_entry(painter, x: int, y: int, width: int, entry: BuffState,
                color: tuple[int, int, int], metrics: _Metrics,
                max_seconds_by_buff: dict[object, int]) -> None:
    """绘制一条 BUFF 明细：名称 + 叠层数 + 倒计时进度条。"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QFontMetrics

    row_height = max(_sp(20, metrics.scale),
                     metrics.font_name + _sp(4, metrics.scale))
    bar_offset = max(_sp(24, metrics.scale),
                     row_height + _sp(4, metrics.scale))
    bar_height = max(3, _sp(7, metrics.scale))

    # 秒数文字宽度按实际内容测量，不再固定预留 40px，避免窄卡片下把进度条挤得过短
    seconds_font = QFont(_CN_FONT)
    seconds_font.setPixelSize(metrics.font_small)
    # 文字向上取整：剩余 12.4 秒仍显示 12 秒，满 13 秒前保持 13 秒
    seconds_text = (f"{max(0, math.ceil(entry.seconds))}秒"
                    if entry.seconds is not None else "--")
    seconds_width = max(
        _sp(12, metrics.scale),
        QFontMetrics(seconds_font).horizontalAdvance(seconds_text)
        + _sp(2, metrics.scale))
    seconds_gap = _sp(4, metrics.scale)

    # 第一行：BUFF 名称（左）和层数（右）
    name_font = QFont(_CN_FONT)
    name_font.setPixelSize(metrics.font_name)
    name_font.setBold(True)
    painter.setFont(name_font)
    painter.setPen(QColor(236, 242, 250))
    painter.drawText(
        QRectF(x, y, width, row_height),
        int(Qt.AlignLeft | Qt.AlignVCenter),
        entry.name,
    )

    stack_font = QFont(_CN_FONT)
    stack_font.setPixelSize(metrics.font_small)
    painter.setFont(stack_font)
    painter.setPen(QColor(170, 200, 225))
    stack_text = ("层数 " + str(entry.stack)) if entry.stack is not None else "层数 --"
    painter.drawText(
        QRectF(x, y, width, row_height),
        int(Qt.AlignRight | Qt.AlignVCenter),
        stack_text,
    )

    # 该 BUFF 没有倒计时元素时，整个进度条和秒数文字都隐藏
    if not entry.has_countdown:
        return

    # 第二行：倒计时进度条 + 剩余秒数
    bar_x = x
    bar_y = y + bar_offset
    bar_width = max(10, width - seconds_width - seconds_gap)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(48, 56, 68))
    painter.drawRoundedRect(
        QRectF(bar_x, bar_y, bar_width, bar_height), 3, 3)

    seconds = entry.seconds
    # 同名 BUFF 会出现多条，必须用 track_id 区分历史最大倒计时；
    # 预览数据没有 track_id 时回退到名称，保持兼容。
    max_key = entry.track_id if entry.track_id >= 0 else entry.name
    max_seconds = max_seconds_by_buff.get(max_key, 0)
    if seconds is not None and max_seconds > 0:
        ratio = max(0.0, min(1.0, seconds / max_seconds))
        if ratio >= 0.5:
            bar_color = _BAR_COLORS[0]
        elif ratio >= 0.25:
            bar_color = _BAR_COLORS[1]
        else:
            bar_color = _BAR_COLORS[2]
        # 比例为 0 时保持空条；大于 0 时至少留 3px，避免刚出现就看不见
        if ratio > 0.0:
            fill_width = max(3.0, bar_width * ratio)
            painter.setBrush(QColor(*bar_color))
            painter.drawRoundedRect(
                QRectF(bar_x, bar_y, fill_width, bar_height), 3, 3)
    elif seconds is not None:
        # 没有历史最大值时退化为满格，至少保证有倒计时能被看见
        painter.setBrush(QColor(*_BAR_COLORS[0]))
        painter.drawRoundedRect(
            QRectF(bar_x, bar_y, bar_width, bar_height), 3, 3)

    painter.setFont(seconds_font)
    painter.setPen(QColor(220, 226, 236) if seconds is not None
                   else QColor(110, 118, 130))
    painter.drawText(
        QRectF(x + width - seconds_width, y + _sp(16, metrics.scale),
               seconds_width, row_height),
        int(Qt.AlignRight | Qt.AlignVCenter),
        seconds_text,
    )


def write_bgr_image(path: str, image: ndarray) -> bool:
    """写出 BGR 图片，兼容中文路径；失败返回 False。"""
    extension = os.path.splitext(path)[1] or ".png"
    try:
        ok, buffer = cv2.imencode(extension, image)
    except cv2.error:
        return False
    if not ok:
        return False
    try:
        buffer.tofile(path)
    except OSError:
        return False
    return True


def _read_image(path: str) -> Optional[ndarray]:
    """用 OpenCV 读取图片，兼容中文路径；失败返回 None。"""
    if not path or not os.path.exists(path):
        return None
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    try:
        return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    except cv2.error:
        return None


def _ensure_app() -> None:
    """按需创建 QGuiApplication，供离屏文字渲染使用。"""
    global _app
    from PySide6.QtGui import QGuiApplication

    if QGuiApplication.instance() is None:
        _app = QGuiApplication([])


def bgr_to_qimage(image: ndarray):
    """把 OpenCV 图片转成带透明通道的 QImage。"""
    from PySide6.QtGui import QImage

    if image.ndim == 2:
        rgba = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
    elif image.shape[2] == 4:
        rgba = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
    else:
        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    rgba = np.ascontiguousarray(rgba)
    height, width = rgba.shape[:2]
    return QImage(rgba.data, width, height, width * 4,
                  QImage.Format_RGBA8888).copy()


def _qimage_to_bgra(image) -> ndarray:
    """把 QImage 转成保留透明通道的 OpenCV BGRA 图片。"""
    from PySide6.QtGui import QImage

    image = image.convertToFormat(QImage.Format_RGBA8888)
    width, height = image.width(), image.height()
    buffer = np.frombuffer(image.constBits(), dtype=np.uint8,
                           count=height * image.bytesPerLine())
    rows = buffer.reshape(height, image.bytesPerLine())[:, :width * 4]
    rgba = rows.reshape(height, width, 4)
    return cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
