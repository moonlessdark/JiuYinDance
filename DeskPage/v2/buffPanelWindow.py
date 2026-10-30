# coding: utf-8
"""
PySide6 状态面板控件与倒计时调度。

职责分两层：
1. StatePanelWidget：可在主界面中嵌入的面板显示控件，按设置渲染大图标和布局；
2. PanelPresenter：持有最新一帧的命中状态，用 QTimer 高频刷新倒计时，
   让进度条平滑缩短而不是每秒跳一截。
   识别到的倒计时会与 QTimer 的值做同步：
   - 识别值比当前值大超过 1 秒，说明 BUFF 被重新施加，重置为识别值；
   - 识别值比当前值小超过 1 秒，说明真实时间更少，以识别值为准；
   - 差值在 1 秒以内视为误差，保留 QTimer 的连续递减结果。
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

from numpy import ndarray
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from DeskPage.v2.buffPanel import (CATEGORY_ORDER, BuffState, PanelSettings,
                                   bgr_to_qimage, render_state_panel,
                                   write_bgr_image)

# 进度条刷新间隔：50ms 约 20fps，肉眼看起来是连续缩短
_TICK_INTERVAL_MS = 50
# 卡片出现/消失动画时长（毫秒），淡入淡出与高度伸缩共用
_CARD_ANIM_MS = 180
# 连续多少个识别帧才确认新卡片出现：避免单帧误检导致卡片反复闪现
_CARD_CONFIRM_FRAMES = 2
# 卡片消失容忍帧数：默认约 1 秒一帧，BUFF 闪烁低谷可能连续漏检 2~3 帧，
# 若沿用“出现确认”的 2 帧会导致大图标在倒计时未结束时反复淡出再淡入，
# 因此这里单独放宽，宁可晚一点移除也不要在闪烁时闪没卡片。
_CARD_MISS_FRAMES = 5
# 倒计时轨迹短暂未检测到时保留多少帧，避免换位/闪烁导致进度条重置；
# 必须不小于卡片消失容忍，否则卡片还在、倒计时却先被清空。
_COUNTDOWN_MISS_FRAMES = _CARD_MISS_FRAMES


@dataclass
class _CardAnimation:
    """单个属性卡片的出现/消失动画状态。"""

    progress: float = 0.0
    target: int = 1
    # 连续未检测到的帧数，达到阈值后才开始淡出
    misses: int = 0
    # 消失动画期间继续使用的最后一份卡片内容快照
    entries: list[BuffState] = field(default_factory=list)


class StatePanelWidget(QWidget):
    """嵌入主界面的 BUFF 状态面板，显示尺寸由“大图标尺寸 + 布局”决定。"""

    def __init__(self) -> None:
        super().__init__()
        self.settings = PanelSettings()
        self._render_callback: Optional[
            Callable[[PanelSettings, float], Optional[ndarray]]] = None
        self._image: Optional[QImage] = None
        # 面板宽度做缓动，避免切换卡片数量时窗口宽度瞬间跳变
        self._display_width: Optional[float] = None
        self._target_width = 0
        self._last_size_time = time.monotonic()
        self._normal_flags = self.windowFlags()
        self._overlay_mode = False
        self.setMinimumSize(120, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 面板背景由渲染结果控制透明度，窗口本身需要支持透明合成
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

    def set_overlay_mode(self, enabled: bool) -> None:
        """
        切换“叠加显示”模式。

        执行时去掉标题栏边框并隐藏任务栏图标，同时置顶，方便叠在游戏窗口上；
        停止后恢复普通窗口外观。
        """
        if enabled == self._overlay_mode:
            return
        self._overlay_mode = enabled
        if enabled:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool
                                | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self._normal_flags)
        self.show()
        self.raise_()

    def set_render_callback(
            self, callback: Callable[[PanelSettings, float],
                                     Optional[ndarray]]) -> None:
        """注册渲染回调，刷新时由回调按当前设置和屏幕倍率生成图片。"""
        self._render_callback = callback

    def set_settings(self, settings: PanelSettings) -> None:
        """更新大图标尺寸/布局设置并立即重绘。"""
        self.settings = settings
        self.refresh()

    def show_image(self, image: ndarray, pixel_ratio: float = 1.0) -> None:
        """直接显示已经渲染好的 BGR 图片，避免重复渲染。"""
        self._image = bgr_to_qimage(image)
        # 标记逻辑尺寸，让高分屏按物理像素绘制而不是把低清图放大
        self._image.setDevicePixelRatio(pixel_ratio)
        logical_width = max(1, int(round(self._image.width() / pixel_ratio)))
        logical_height = max(1, int(round(self._image.height() / pixel_ratio)))

        # 宽度按真实经过时间缓动，避免卡片增减导致窗口宽度瞬间跳变
        now = time.monotonic()
        elapsed = min(max(now - self._last_size_time, 0.001), 0.05)
        self._last_size_time = now
        self._target_width = logical_width
        if self._display_width is None:
            self._display_width = float(logical_width)
        elif abs(self._display_width - logical_width) > 0.5:
            factor = 1.0 - math.exp(-elapsed / 0.04)
            self._display_width += (logical_width - self._display_width) * factor
            if abs(self._display_width - logical_width) <= 0.5:
                self._display_width = float(logical_width)
        else:
            self._display_width = float(logical_width)

        display_width = max(1, int(round(self._display_width)))
        if self.isWindow() and (self.width() != display_width
                                or self.height() != logical_height):
            self.resize(display_width, logical_height)
        self.updateGeometry()
        self.update()

    def size_animating(self) -> bool:
        """窗口宽度是否仍在缓动中，用于让 QTimer 继续刷新直到收敛。"""
        return (self._display_width is not None
                and abs(self._display_width - self._target_width) > 0.5)

    def refresh(self) -> None:
        """按当前设置和屏幕倍率重新渲染并刷新画面。"""
        if self._render_callback is None:
            return
        pixel_ratio = max(1.0, self.devicePixelRatioF())
        image = self._render_callback(self.settings, pixel_ratio)
        if image is None:
            return
        self.show_image(image, pixel_ratio)

    def paintEvent(self, event) -> None:
        """绘制面板图片；没有图片时显示居中提示。"""
        painter = QPainter(self)
        if self._image is not None:
            # 先用透明色清空整块区域，保证低透明度背景能露出下方游戏画面
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, self._image)
        else:
            painter.fillRect(self.rect(), QColor(13, 17, 23))
            painter.setPen(QColor(130, 138, 150))
            painter.drawText(self.rect(), int(Qt.AlignCenter),
                             "点击「开始执行」查看 BUFF 状态面板")
        painter.end()


# 兼容旧命名，外部若仍引用 StatePanelWindow 也能正常工作
StatePanelWindow = StatePanelWidget


class PanelPresenter:
    """维护当前帧状态、浮点倒计时，并负责面板渲染和刷新。"""

    def __init__(self,
                 window: Optional[StatePanelWidget],
                 icons: dict[str, ndarray],
                 max_seconds_by_buff: dict[object, int],
                 output_dir: str,
                 settings_provider: Optional[Callable[[], PanelSettings]] = None
                 ) -> None:
        self._window = window
        self._icons = icons
        self._max_seconds_by_buff = max_seconds_by_buff
        self._output_dir = output_dir
        self._settings_provider = settings_provider or (
            lambda: PanelSettings())
        self._states: list[BuffState] = []
        self._frame_name = ""
        # 分类 -> 属性出现顺序：新图标追加到末尾，旧图标消失后自动前移
        self._slot_order: dict[str, list[str]] = {
            category: [] for category in CATEGORY_ORDER}
        # track_id -> QTimer 维护的剩余秒数（浮点，便于进度条平滑变化）。
        # 同名 BUFF 可能同时存在两个，必须用跟踪 ID 而不是名称区分。
        self._countdown: dict[object, float] = {}
        # track key -> 连续未检测帧数，用于短暂保留倒计时进度
        self._countdown_missing: dict[object, int] = {}
        # (分类, 属性) -> 卡片出现/消失动画状态
        self._card_anim: dict[tuple[str, str], _CardAnimation] = {}
        # (分类, 属性) -> 连续出现帧数，用于过滤单帧误检
        self._pending_hits: dict[tuple[str, str], int] = {}
        # 首帧直接显示，避免启动时还要额外等待一个确认帧
        self._first_frame = True
        self._last_tick = time.monotonic()
        self._timer: Optional[QTimer] = None

        # 只有嵌入界面时才需要高频重绘；纯批处理只输出识别瞬间的图片
        if self._window is not None:
            self._window.set_render_callback(self._render_for_widget)
            self._timer = QTimer(self._window)
            self._timer.setInterval(_TICK_INTERVAL_MS)
            self._timer.timeout.connect(self._on_tick)
            self._timer.start()

    def update_frame(self, states: list[BuffState], frame_name: str) -> bool:
        """
        接收一帧新的识别结果。

        :return: 是否成功写出该帧的面板图片
        """
        if not self._icons:
            return False

        # 先把倒计时推进到当前时刻，再与识别值对齐
        self._advance()
        self._states = states
        self._frame_name = frame_name
        self._update_slot_order(states)
        self._sync_countdown(states)
        self._sync_card_animations()

        # 输出到磁盘的调试图保持“完整显示”，动画只作用于界面
        panel = self._render_panel(animate=False)
        if panel is None:
            return False

        if self._window is not None:
            self._window.refresh()

        # 实时运行时可以不写逐帧面板图，只刷新窗口，避免磁盘 IO 拖慢识别
        if not self._output_dir:
            return False
        return write_bgr_image(
            os.path.join(self._output_dir, frame_name), panel)

    def close(self) -> None:
        """停止倒计时并释放控件引用。"""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._window = None

    def _advance(self) -> bool:
        """
        按真实经过时间递减浮点倒计时，并推进卡片出现/消失动画。

        使用 monotonic 而不是固定减 1，避免 QTimer 被主线程阻塞时产生累计误差。
        :return: 倒计时或卡片动画是否发生变化
        """
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now
        if elapsed <= 0.0:
            return False

        changed = False
        for name, value in self._countdown.items():
            if value > 0.0:
                self._countdown[name] = max(0.0, value - elapsed)
                changed = True
        if self._advance_card_animations(elapsed):
            changed = True
        return changed

    def _advance_card_animations(self, elapsed: float) -> bool:
        """
        按经过时间推进卡片动画进度。

        进度从 0 淡入到 1，或从 1 淡出到 0；完全消失在 0 时移除动画状态。
        :return: 是否有卡片动画发生变化
        """
        if not self._card_anim:
            return False
        step = elapsed * 1000.0 / _CARD_ANIM_MS
        changed = False
        for key, animation in list(self._card_anim.items()):
            if animation.progress < animation.target:
                animation.progress = min(1.0, animation.progress + step)
                changed = True
            elif animation.progress > animation.target:
                animation.progress = max(0.0, animation.progress - step)
                changed = True
            if animation.progress <= 0.0 and animation.target == 0:
                del self._card_anim[key]
        return changed

    def _sync_card_animations(self) -> None:
        """
        用最新一帧的卡片集合更新动画目标。

        - 新属性连续出现若干帧后才开始淡入，过滤单帧误检；
        - 已显示的属性连续丢失若干帧后才开始淡出，避免一帧漏检就闪烁；
        - 消失过程中重新出现的属性继续使用当前进度淡入。
        """
        display_states = self._display_states()
        grouped: dict[tuple[str, str], list[BuffState]] = {}
        for state in display_states:
            grouped.setdefault(
                (state.category, state.attribute), []).append(state)

        if self._first_frame:
            # 第一帧直接按完整状态显示，避免启动时多等一个识别周期
            self._first_frame = False
            for key, entries in grouped.items():
                self._card_anim[key] = _CardAnimation(
                    progress=1.0, target=1, entries=entries)
            return

        for key, entries in grouped.items():
            animation = self._card_anim.get(key)
            if animation is not None:
                animation.target = 1
                animation.misses = 0
                animation.entries = entries
                self._pending_hits.pop(key, None)
                continue

            # 新卡片先累计连续出现帧数，确认稳定后再加入动画
            hits = self._pending_hits.get(key, 0) + 1
            if hits >= _CARD_CONFIRM_FRAMES:
                self._card_anim[key] = _CardAnimation(
                    progress=0.0, target=1, entries=entries)
                self._pending_hits.pop(key, None)
            else:
                self._pending_hits[key] = hits

        for key, animation in self._card_anim.items():
            if key in grouped:
                animation.misses = 0
                continue
            animation.misses += 1
            # 连续丢失达到放宽后的阈值后才真正开始淡出，跨过 BUFF 闪烁低谷
            if animation.misses >= _CARD_MISS_FRAMES:
                animation.target = 0

        # 未确认稳定就消失的误检直接丢弃计数
        for key in list(self._pending_hits):
            if key not in grouped:
                del self._pending_hits[key]

    def _update_slot_order(self, states: list[BuffState]) -> None:
        """
        维护大图标卡片的出现顺序。

        - 新出现的属性追加到所在分类的末尾；
        - 当前帧不再出现的属性在淡出动画期间仍保留位置，完全消失后再移除。
        """
        active = {(state.category, state.attribute) for state in states}
        # 正在淡出的卡片也保留槽位，避免动画中途卡片位置突然前移
        keep = active | {key for key, animation in self._card_anim.items()
                         if animation.progress > 0.0}
        for category in CATEGORY_ORDER:
            order = self._slot_order.setdefault(category, [])
            order[:] = [attribute for attribute in order
                        if (category, attribute) in keep]
            for state in states:
                if state.category != category:
                    continue
                if (category, state.attribute) in active \
                        and state.attribute not in order:
                    order.append(state.attribute)
            # 兜底：淡出中的属性如果尚未进入顺序，补到末尾
            for key in keep:
                if key[0] == category and key[1] not in order:
                    order.append(key[1])

    def _sync_countdown(self, states: list[BuffState]) -> None:
        """
        用最新识别值与 QTimer 倒计时对齐，并清理已经消失的 BUFF。

        1 秒误差用于抵消“识别发生在 QTimer 触发前后”造成的一秒抖动。
        key 使用 track_id：两个同名 BUFF 各自维护倒计时，换位后也能延续。
        """
        present: set[object] = set()
        for state in states:
            if not state.has_countdown:
                continue
            key = state.track_id if state.track_id >= 0 else state.name
            present.add(key)

            # 历史最大倒计时用于进度条比例
            if state.seconds is not None:
                self._max_seconds_by_buff[key] = max(
                    self._max_seconds_by_buff.get(key, 0),
                    int(state.seconds))

            current = self._countdown.get(key)
            if state.seconds is None:
                continue
            if current is None:
                self._countdown[key] = float(state.seconds)
            elif state.seconds > current + 1.0:
                # 倒计时突然增加，视为 BUFF 重新施加
                self._countdown[key] = float(state.seconds)
            elif state.seconds < current - 1.0:
                # 识别值明显更小，说明真实剩余时间更少，跟随识别值
                self._countdown[key] = float(state.seconds)

        # 当前帧未检测到的 BUFF 先保留几帧倒计时，避免换位/闪烁时进度条重置；
        # 连续缺失超过容忍帧数后再删除，防止陈旧数值一直残留。
        for key in list(self._countdown):
            if key in present:
                self._countdown_missing.pop(key, None)
                continue
            misses = self._countdown_missing.get(key, 0) + 1
            if misses > _COUNTDOWN_MISS_FRAMES:
                del self._countdown[key]
                self._countdown_missing.pop(key, None)
                self._max_seconds_by_buff.pop(key, None)
            else:
                self._countdown_missing[key] = misses

    def _on_tick(self) -> None:
        """QTimer 高频回调：平滑推进倒计时和卡片动画并重绘面板。"""
        if self._window is None:
            return
        if self._advance() or self._window.size_animating():
            self._window.refresh()

    def _with_live_countdown(self, state: BuffState) -> BuffState:
        """把 QTimer 维护的最新倒计时合并进单条状态，供正常渲染和淡出快照复用。"""
        if not state.has_countdown:
            return state
        key = state.track_id if state.track_id >= 0 else state.name
        seconds = self._countdown.get(key, state.seconds)
        if seconds == state.seconds:
            return state
        return replace(state, seconds=seconds)

    def _display_states(self) -> list[BuffState]:
        """把 QTimer 倒计时合并进当前帧状态，供渲染使用。"""
        return [self._with_live_countdown(state) for state in self._states]

    def _render_panel(
            self, settings: Optional[PanelSettings] = None,
            pixel_ratio: float = 1.0,
            animate: bool = True) -> Optional[ndarray]:
        """按当前设置渲染面板；settings 为空时从界面读取最新设置。"""
        if not self._icons:
            return None
        settings = settings or self._settings_provider()
        progress: Optional[dict[tuple[str, str], float]] = None
        ghosts: Optional[dict[tuple[str, str], list[BuffState]]] = None
        if animate and self._card_anim:
            progress = {key: animation.progress
                        for key, animation in self._card_anim.items()}
            # 淡出快照里的倒计时也要跟随 QTimer 继续推进，避免漏检期间秒数冻结
            ghosts = {
                key: [self._with_live_countdown(entry)
                      for entry in animation.entries]
                for key, animation in self._card_anim.items()
                if animation.entries}
        return render_state_panel(
            self._display_states(), self._icons, self._max_seconds_by_buff,
            self._frame_name, settings, self._slot_order, pixel_ratio,
            card_progress=progress, ghost_entries=ghosts)

    def _render_for_widget(
            self, settings: PanelSettings,
            pixel_ratio: float) -> Optional[ndarray]:
        """StatePanelWidget 的回调：按控件当前设置和屏幕倍率渲染。"""
        return self._render_panel(settings, pixel_ratio)
