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
   - 差值在 1 秒以内视为误差，保留 QTimer 的连续递减结果；
   - 剩余小于 FLICKER_SECONDS 时图标闪烁、读数抖动，此时只有识别到大于
     阈值的秒数才刷新，其余情况保持 QTimer 的连续递减。
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

from numpy import ndarray
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QSizePolicy, QWidget

from Core.windows.window import (activate_windows_ex, is_window_alive,
                                 set_window_above, set_window_topmost)
from DeskFunc.v2.TaskBussinese.buffCountdown import FLICKER_SECONDS
from DeskPage.v2.buffPanel import (CATEGORY_ORDER, BuffState, PanelSettings,
                                   bgr_to_qimage, render_state_panel,
                                   write_bgr_image)

# 进度条刷新间隔：50ms 约 20fps，肉眼看起来是连续缩短
_TICK_INTERVAL_MS = 50
# 卡片出现/消失动画时长（毫秒），淡入淡出与高度伸缩共用
_CARD_ANIM_MS = 180
# 漏检容忍默认值（秒），“普通”档位；实际值由设置界面的检测灵敏度决定。
# 按真实时间判断，与期间识别了多少帧无关。
_DEFAULT_MISS_SECONDS = 0.5
# 面板 Z 序跟随间隔：目标游戏窗口的 Z 序随时可能变化（激活、被其它窗口
# 覆盖、同级窗口插入等），需要高频检查并重新贴到目标窗口正上方。
# 50ms 约 20Hz，肉眼基本感知不到延迟；真正调用 SetWindowPos 只发生在面板
# 不再紧贴目标时，因此高频检查本身开销很小。
_ABOVE_TARGET_REFRESH_MS = 50


def _state_key(state: BuffState) -> object:
    """BUFF 状态在倒计时和快照中的唯一键；预览数据没有 track_id 时退回名称。"""
    return state.track_id if state.track_id >= 0 else state.name


@dataclass
class _CardAnimation:
    """单个属性卡片的出现/消失动画状态。"""

    progress: float = 0.0
    target: int = 1
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
        self._overlay_mode = False
        # 绑定的目标游戏窗口句柄，0 表示未绑定
        self._target_hwnd = 0
        # 拖动状态：仅任务未启动时允许拖动面板位置
        self._drag_enabled = False
        self._dragging = False
        self._drag_offset = None
        # 定时把面板抬到目标窗口上方，避免游戏窗口激活后压住面板
        self._above_target_timer = QTimer(self)
        self._above_target_timer.setInterval(_ABOVE_TARGET_REFRESH_MS)
        self._above_target_timer.timeout.connect(self._keep_above_target)
        self.setMinimumSize(120, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 面板背景由渲染结果控制透明度，窗口本身需要支持透明合成
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

    def set_overlay_mode(self, enabled: bool) -> None:
        """
        切换“叠加显示”模式。

        开启时去掉标题栏边框并隐藏任务栏图标，方便叠在游戏窗口上；
        这里不再使用 WindowStaysOnTopHint 全局置顶，面板是否显示在其它窗口
        之上由目标窗口的 Z 序决定：只贴在目标游戏窗口上方，用户切到其它
        程序时会被正常盖住。

        注意：这里只负责显示，不启动 Z 序跟随。预览阶段（刚点击“BUFF监控”
        但还没开始执行）应让面板作为普通激活窗口展示在最前；只有任务真正
        开始执行、调用 bind_target_window 后才开始跟随游戏窗口。

        关闭时只解除置顶和目标窗口绑定，始终保持无边框样式，
        避免停止任务后重新出现系统标题栏或任务栏按钮。
        """
        if enabled:
            if not self._overlay_mode:
                self._overlay_mode = True
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
            self.show()
            self.raise_()
            return

        was_visible = self.isVisible()
        self._overlay_mode = False
        self._above_target_timer.stop()
        self._target_hwnd = 0
        if was_visible:
            set_window_topmost(int(self.winId()), False)

    def activate_panel(self) -> None:
        """
        把面板设为当前激活（前台）窗口。

        用于刚点击“BUFF监控”、面板首次弹出时：此时任务还没开始执行，
        不需要跟随游戏窗口，先把面板正常举到最前，方便用户查看和拖动。
        """
        self.show()
        self.raise_()
        self.activateWindow()
        activate_windows_ex(int(self.winId()))

    def bind_target_window(self, hwnd: int) -> None:
        """
        绑定目标游戏窗口，让面板始终显示在该窗口的上一层。

        只有任务开始执行后才会调用，调用后启动 Z 序跟随定时器。

        :param hwnd: 目标游戏窗口句柄
        """
        try:
            target_hwnd = int(hwnd)
        except (TypeError, ValueError):
            return
        self._target_hwnd = target_hwnd
        self._keep_above_target()
        if self._overlay_mode and not self._above_target_timer.isActive():
            self._above_target_timer.start()

    def unbind_target_window(self) -> None:
        """解除目标窗口绑定，停止 Z 序跟随。"""
        self._target_hwnd = 0
        self._above_target_timer.stop()

    def set_draggable(self, enabled: bool) -> None:
        """设置是否允许拖动面板位置，任务执行中应关闭。"""
        self._drag_enabled = enabled
        if not enabled:
            self._dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor if enabled
                       else Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:
        """叠加模式下按住左键记录拖动起点。"""
        if (self._overlay_mode and self._drag_enabled
                and event.button() == Qt.MouseButton.LeftButton):
            self._dragging = True
            self._drag_offset = (event.globalPosition().toPoint()
                                 - self.frameGeometry().topLeft())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """拖动过程中跟随鼠标移动窗口。"""
        if (self._dragging and self._drag_offset is not None
                and event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """松开左键结束拖动并恢复光标。"""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor
                           if self._drag_enabled
                           else Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _keep_above_target(self) -> None:
        """
        把面板抬到目标窗口上方。

        只有确认目标窗口已经关闭时才解除绑定。Z 序切换瞬间 SetWindowPos
        可能临时失败，若此时解绑会导致面板从此不再跟随、被游戏窗口盖住，
        因此失败时保留绑定，交给下一次定时检查继续重试。
        """
        if not self._overlay_mode or not self._target_hwnd:
            return
        if not self.isVisible():
            return
        if not is_window_alive(self._target_hwnd):
            self._target_hwnd = 0
            return
        set_window_above(int(self.winId()), self._target_hwnd)

    def showEvent(self, event) -> None:
        """显示时立即抬升一次，保证弹出瞬间就在目标窗口上方。"""
        super().showEvent(event)
        self._keep_above_target()

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

        # 独立窗口固定为渲染内容尺寸，窗口大小始终跟着卡片宽高变化
        if self.isWindow() and (self.width() != logical_width
                                or self.height() != logical_height):
            self.setFixedSize(logical_width, logical_height)
        self.updateGeometry()
        self.update()

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
                 settings_provider: Optional[Callable[[], PanelSettings]] = None,
                 miss_seconds: float = _DEFAULT_MISS_SECONDS
                 ) -> None:
        self._window = window
        self._icons = icons
        self._max_seconds_by_buff = max_seconds_by_buff
        self._output_dir = output_dir
        self._settings_provider = settings_provider or (
            lambda: PanelSettings())
        # 漏检容忍秒数：无倒计时和有倒计时共用同一档位，由检测灵敏度设置覆盖
        self.set_miss_seconds(miss_seconds, refresh=False)
        self._states: list[BuffState] = []
        self._frame_name = ""
        # 分类 -> 属性出现顺序：新图标追加到末尾，旧图标消失后自动前移
        self._slot_order: dict[str, list[str]] = {
            category: [] for category in CATEGORY_ORDER}
        # track_id -> QTimer 维护的剩余秒数（浮点，便于进度条平滑变化）。
        # 同名 BUFF 可能同时存在两个，必须用跟踪 ID 而不是名称区分。
        self._countdown: dict[object, float] = {}
        # track key -> 最后一次检测到的状态快照（有/无倒计时都记录）。
        # 漏检容忍期内用它补全显示，避免偶发漏检把卡片清掉。
        self._snapshots: dict[object, BuffState] = {}
        # track key -> 首次漏检的 monotonic 时间，用于按毫秒判断是否真正消失
        self._missing_since: dict[object, float] = {}
        # (分类, 属性) -> 卡片出现/消失动画状态
        self._card_anim: dict[tuple[str, str], _CardAnimation] = {}

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
        self._sync_states(states)
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

    def set_miss_seconds(self, miss_seconds: float,
                         refresh: bool = True) -> None:
        """
        更新漏检容忍秒数。

        :param miss_seconds: 检测灵敏度换算出的秒数，过小值会被限制到 0.05 秒
        :param refresh: 是否立即重绘面板
        """
        value = max(0.05, float(miss_seconds))
        self._countdown_miss_seconds = value
        self._card_miss_seconds = value
        if refresh and self._window is not None:
            self._window.refresh()

    def _miss_limit(self, has_countdown: bool) -> float:
        """按 BUFF 类型返回当前漏检容忍秒数。"""
        return (self._countdown_miss_seconds if has_countdown
                else self._card_miss_seconds)

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
        # 消失判定按真实时间推进，不必等下一个识别帧
        if self._advance_missing_cards(now):
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

        - 新属性检测到就立即完整显示，不做出现确认；
        - 已显示的属性只在漏检超过灵敏度设置的时长后才淡出，见 _display_states；
        - 消失过程中重新出现的属性继续使用当前进度淡入。
        """
        display_states = self._display_states()
        grouped: dict[tuple[str, str], list[BuffState]] = {}
        for state in display_states:
            grouped.setdefault(
                (state.category, state.attribute), []).append(state)

        if self._first_frame:
            # 第一帧直接按完整状态显示
            self._first_frame = False
            for key, entries in grouped.items():
                self._card_anim[key] = _CardAnimation(
                    progress=1.0, target=1, entries=entries)
            return

        for key, entries in grouped.items():
            animation = self._card_anim.get(key)
            if animation is not None:
                animation.target = 1
                animation.entries = entries
                continue

            # 检测到新属性立即完整显示，不等待后续帧确认
            self._card_anim[key] = _CardAnimation(
                progress=1.0, target=1, entries=entries)

        for key, animation in self._card_anim.items():
            # 未超时漏检的卡片已经被 _display_states 补全，这里缺失就是真消失
            animation.target = 1 if key in grouped else 0

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

    def _sync_states(self, states: list[BuffState]) -> None:
        """
        用最新识别结果对齐倒计时，并按毫秒判断漏检的 BUFF 是否已经消失。

        1 秒误差用于抵消“识别发生在 QTimer 触发前后”造成的一秒抖动。
        key 使用 track_id：两个同名 BUFF 各自维护倒计时，换位后也能延续。

        闪烁处理：识别读数小于 FLICKER_SECONDS 时一律不重置已有倒计时，
        继续沿用 QTimer 的连续递减。60 秒这类数字被误读成个位数的情况很常见，
        真实进入 10 秒内后让 QTimer 自己走即可；只有识别到不小于阈值的秒数
        才按 1 秒误差规则对齐。

        漏检容忍按真实时间计算，与期间识别了多少帧无关：没有倒计时的图标
        1 秒、有倒计时的图标 2 秒仍未再次检测到才清理。倒计时不会被强制
        走到 0 后清除，BUFF 因其他原因提前消失时也能及时移除。
        """
        now = time.monotonic()
        present: set[object] = set()
        for state in states:
            key = _state_key(state)
            present.add(key)
            # 记录最新快照，漏检容忍期内用它补全显示
            self._snapshots[key] = state
            self._missing_since.pop(key, None)

            if not state.has_countdown:
                continue

            current = self._countdown.get(key)
            seconds = state.seconds

            # 已有倒计时时，小于闪烁阈值的识别读数不重置当前秒数：
            # 避免 60 秒被误读成 9 秒后进度条突然跳变
            if (current is not None and seconds is not None
                    and seconds < FLICKER_SECONDS):
                continue

            # 历史最大倒计时用于进度条比例；只认可本次读数时才更新，
            # 避免闪烁期间的误读把进度条比例拉偏
            if seconds is not None:
                self._max_seconds_by_buff[key] = max(
                    self._max_seconds_by_buff.get(key, 0),
                    int(seconds))

            if seconds is None:
                continue
            if current is None:
                self._countdown[key] = float(seconds)
            elif seconds > current + 1.0:
                # 倒计时突然增加，视为 BUFF 重新施加
                self._countdown[key] = float(seconds)
            elif seconds < current - 1.0:
                # 识别值明显更小，说明真实剩余时间更少，跟随识别值
                self._countdown[key] = float(seconds)

        # 漏检达到容忍时长才清理；倒计时数值本身不参与判断
        for key, snapshot in list(self._snapshots.items()):
            if key in present:
                continue
            since = self._missing_since.get(key)
            if since is None:
                self._missing_since[key] = now
                continue
            if now - since < self._miss_limit(snapshot.has_countdown):
                continue
            self._forget_state(key)

    def _advance_missing_cards(self, now: float) -> bool:
        """
        漏检超过容忍时长时立即让卡片开始淡出并清理状态，不必等识别帧。

        卡片下所有 BUFF 都超时才淡出，避免同属性还有 BUFF 正常显示时误伤。
        :return: 是否有卡片开始淡出
        """
        changed = False
        for animation in self._card_anim.values():
            if animation.target != 1 or not animation.entries:
                continue
            if not all(self._is_entry_missing(entry, now)
                       for entry in animation.entries):
                continue
            animation.target = 0
            changed = True
            # 超时的 BUFF 不再保留倒计时和快照，重新检测时按新出现处理
            for entry in animation.entries:
                self._forget_state(_state_key(entry))
        return changed

    def _is_entry_missing(self, entry: BuffState, now: float) -> bool:
        """单条 BUFF 是否已经超过漏检容忍时长。"""
        since = self._missing_since.get(_state_key(entry))
        if since is None:
            return False
        return now - since >= self._miss_limit(entry.has_countdown)

    def _forget_state(self, key: object) -> None:
        """彻底清理某条 BUFF 的倒计时、显示快照和漏检计时。"""
        self._snapshots.pop(key, None)
        self._missing_since.pop(key, None)
        self._countdown.pop(key, None)
        self._max_seconds_by_buff.pop(key, None)

    def _on_tick(self) -> None:
        """QTimer 高频回调：平滑推进倒计时和卡片动画并重绘面板。"""
        if self._window is None:
            return
        if self._advance():
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
        """
        把 QTimer 倒计时合并进显示状态，供渲染使用。

        漏检但仍在容忍时长内的 BUFF 用最后一次快照补全，继续显示实时倒计时；
        超过检测灵敏度设置的时长后不再补全，卡片随即淡出。
        这样复杂背景偶发漏检不会闪没，BUFF 真正消失时也能按时清掉。
        """
        now = time.monotonic()
        shown_keys: set[object] = set()
        display: list[BuffState] = []
        for state in self._states:
            shown_keys.add(_state_key(state))
            display.append(self._with_live_countdown(state))

        for key, snapshot in self._snapshots.items():
            if key in shown_keys:
                continue
            since = self._missing_since.get(key)
            if since is None:
                continue
            if now - since >= self._miss_limit(snapshot.has_countdown):
                continue
            display.append(self._with_live_countdown(snapshot))
        return display

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
        if animate:
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
