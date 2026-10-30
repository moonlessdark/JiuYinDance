# coding: utf-8
"""
团练授业 / 上下左右（绿/红）任务线程。

识别由 v2 FindDanceButton 完成，本线程只负责：
1. 截图；
2. 识别按键顺序；
3. 激活窗口并通过幽灵键鼠发送按键；
4. 多窗口轮询与停止控制。
"""
import time

from Core.input.ghost import SetGhostBoards, get_random_time
from Core.windows.capture import PicCapture, WindowsCapture
from Core.windows.window import WindowsHandle
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.danceButton import (
    DANCE_TYPE_GREEN,
    DANCE_TYPE_GREY,
    FindDanceButton,
)

# 按键名 -> 幽灵键鼠键码（上下左右用键码，字母用键名）
_KEY_NAME_MAP = {
    "UP": 38,
    "Down": 40,
    "Left": 37,
    "Right": 39,
    "J": "J",
    "K": "K",
}

_LOG_NAME_MAP = {
    "UP": "上",
    "Down": "下",
    "Left": "左",
    "Right": "右",
    "J": "J",
    "K": "K",
}


def input_key_by_ghost(key_list: list[str]) -> None:
    """按识别出的顺序依次发送按键，按键之间加入随机间隔。"""
    time.sleep(0.1)
    for key in key_list:
        target = _KEY_NAME_MAP.get(key)
        if isinstance(target, int):
            SetGhostBoards().click_press_and_release_by_code(target)
        elif isinstance(target, str):
            SetGhostBoards().click_press_and_release_by_key_name(target)
        time.sleep(get_random_time(0.3))


class DanceTask(BaseTaskThread):
    """团练授业、势力修炼按键任务。"""

    def __init__(self):
        super().__init__()
        self._hwnd_list: list[int] = []
        self._dance_type = DANCE_TYPE_GREY
        self._capture = WindowsCapture()
        self._windows_opt = WindowsHandle()
        self._find_button = FindDanceButton()

    def init_task_param(self, hwnd_list: list[int], dance_type: str = DANCE_TYPE_GREY):
        """
        初始化执行参数。

        :param hwnd_list: 需要检测的窗口句柄
        :param dance_type: grey / green
        """
        self._hwnd_list = list(hwnd_list)
        self._dance_type = dance_type
        self.working = True

    def run(self):
        self.mutex.lock()
        find_button_count = 0
        try:
            self.sin_run_status.emit(True)

            while self.working:

                self.status_bar.emit(find_button_count)
                for hwnd in self._hwnd_list:
                    if not self.working:
                        break

                    capture: PicCapture = self._capture.capture(hwnd)
                    if capture is None:
                        continue

                    if self._dance_type == DANCE_TYPE_GREEN:
                        button_list = self._find_button.find_button_green(capture.pic_content)
                    else:
                        button_list = self._find_button.find_button(capture.pic_content)

                    if not button_list:
                        continue

                    if not self._windows_opt.activate_windows(hwnd):
                        self.sin_out.emit(f"窗口: {hwnd} 激活失败,任务停止执行")
                        self.working = False
                        break

                    input_key_by_ghost(button_list)
                    find_button_count += 1
                    self.sin_out.emit(
                        f"按钮: {''.join(_LOG_NAME_MAP.get(key, key) for key in button_list)}")

                    if len(self._hwnd_list) == 1:
                        # 单窗口连续识别太快容易重复按同一轮，稍微停顿
                        time.sleep(0.5)
        finally:
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
