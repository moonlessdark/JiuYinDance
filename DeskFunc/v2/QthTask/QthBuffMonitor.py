# coding: utf-8
"""
BUFF 监控任务线程。

与其它任务的区别：本任务只读取游戏窗口截图并识别 BUFF，不激活窗口、
不发送按键。图像来源是 WindowsCapture 的客户区实时截图，不读取本地文件。

线程职责：
1. 按配置间隔截取游戏窗口客户区；
2. 调用 BuffRecognizer 识别 BUFF 状态；
3. 通过 buff_frame 信号把结果交给主线程刷新面板；
4. 通过日志输出每轮识别摘要；
5. 支持停止按钮，停止时立即退出循环。
"""
from __future__ import annotations

import time

from PySide6.QtCore import Signal

from Core.windows.capture import WindowsCapture
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.buffRecognition import (
    BuffDetection,
    BuffRecognizer,
)
from Utils.resourceConfig import get_resources


class BuffMonitorTask(BaseTaskThread):
    """屏幕截图的 BUFF 实时识别任务。"""

    # BuffDetection 列表、窗口标题
    buff_frame = Signal(list, str)

    def __init__(self):
        super().__init__()
        self._hwnd_list: list[int] = []
        self._capture = WindowsCapture()
        self._recognizer: BuffRecognizer | None = None
        self._scan_interval_ms = 1000
        self._last_summary = ""

    def init_task_param(self, hwnd_list: list[int]) -> None:
        """初始化需要监控的窗口句柄。"""
        self._hwnd_list = list(hwnd_list)
        self._last_summary = ""
        self.working = True

    def run(self) -> None:
        self.mutex.lock()
        frame_count = 0
        try:
            self.sin_run_status.emit(True)

            if not self._hwnd_list:
                self.sin_out.emit("请先勾选需要监控的游戏窗口")
                return None

            # 模板加载放在线程内，避免主界面在点击开始瞬间卡顿
            assets = get_resources().buff_assets
            try:
                self._recognizer = BuffRecognizer(assets.config_path)
            except (OSError, ValueError) as error:
                self.sin_out.emit(f"BUFF 识别初始化失败：{error}")
                return None

            if not self._recognizer.templates:
                self.sin_out.emit(
                    "没有加载到 BUFF 模板，请检查 "
                    "Resources/ImageTemplate/PicBuff/buff_config.json")
                return None

            self._scan_interval_ms = self._recognizer.scan_interval_ms
            self.sin_out.emit(
                f"BUFF 监控已启动，识别 {len(self._recognizer.templates)} 个模板，"
                f"间隔 {self._scan_interval_ms} 毫秒")

            while self.working:
                round_start = time.monotonic()
                for index, hwnd in enumerate(self._hwnd_list):
                    if not self.working:
                        break

                    capture = self._capture.capture(hwnd)
                    if capture is None:
                        self.sin_out.emit(
                            f"窗口 {index + 1} 截图失败，请确认窗口可见且未最小化")
                        continue

                    detections = self._recognizer.recognize(capture.pic_content)
                    title = f"窗口 {index + 1}"
                    self.buff_frame.emit(detections, title)

                    # 只在 BUFF 集合或层数变化时写日志，避免倒计时每帧刷屏
                    summary = self._format_summary(title, detections)
                    if summary != self._last_summary:
                        self.sin_out.emit(summary)
                        self._last_summary = summary

                    frame_count += 1
                    self.status_bar.emit(frame_count)

                self._wait_next_round(round_start)
        finally:
            self.sin_out.emit("BUFF 监控已停止")
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None

    def _wait_next_round(self, round_start: float) -> None:
        """按配置间隔补齐等待时间，并分段检查停止标志。"""
        deadline = round_start + self._scan_interval_ms / 1000.0
        while self.working:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            # 分段睡眠，保证点击停止后能快速退出
            time.sleep(min(0.1, remaining))

    @staticmethod
    def _format_summary(title: str,
                        detections: list[BuffDetection]) -> str:
        """把本帧识别结果整理为一行中文日志。"""
        if not detections:
            return f"[{title}] 未检测到激活 BUFF"

        parts: list[str] = []
        for detection in detections:
            text = detection.name
            if detection.stack is not None:
                text += f" 层数{detection.stack}"
            parts.append(text)
        return f"[{title}] " + "，".join(parts)
