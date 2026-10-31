# coding: utf-8
"""
9 点开卡任务线程。

逻辑与 v1 一致：
1. 只在 20:59:55 / 21:03:55 / "21:07:55" 前后执行；
2. 逐个窗口打开背包、找到礼卡、右键开卡；
3. 开完后点击“全部拾取”，并记录开卡次数。
"""
import datetime
import time

from Core.input.ghost import SetGhostMouse
from Core.windows.capture import WindowsCapture
from Core.windows.window import WindowsHandle
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.moneyCard import FindGiftCard


class OpenGiftCardTask(BaseTaskThread):
    """9 点开卡任务。"""

    def __init__(self):
        super().__init__()
        self._windows_opt = WindowsHandle()
        self._windows_cap = WindowsCapture()
        self._windows_handle_list: list[int] = []
        self._find_gift_card = FindGiftCard()

    @staticmethod
    def check_local_time() -> bool:
        """判断当前时间是否落在开卡时间窗口内。"""
        current_time = datetime.datetime.now().replace(microsecond=0)
        target_times = ["20:59:55", "21:03:55", "21:07:55"]

        for text in target_times:
            target = datetime.datetime.strptime(text, "%H:%M:%S").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day,
            )
            start = target - datetime.timedelta(seconds=1)
            end = target + datetime.timedelta(seconds=3)
            if start <= current_time <= end:
                return True
        return False

    def get_param(self, windows_handle_list: list[int]):
        """初始化执行参数。"""
        self.working = True
        self._windows_handle_list = list(windows_handle_list)

    def run(self):
        self.mutex.lock()
        opened_hwnd_list: list[int] = []
        no_card_hwnd_list: list[int] = []
        open_card_count = 0

        try:
            self.sin_run_status.emit(True)

            while self.working:
                if not self.check_local_time():
                    time.sleep(1)
                    continue

                if len(no_card_hwnd_list + opened_hwnd_list) == len(self._windows_handle_list):
                    self.sin_out.emit("所有窗口已全部处理完毕")
                    time.sleep(1)
                    continue

                for hwnd in self._windows_handle_list:
                    if not self.working:
                        break
                    if hwnd in no_card_hwnd_list or hwnd in opened_hwnd_list:
                        time.sleep(0.5)
                        continue

                    self.sin_out.emit(f"窗口id:{hwnd} 正在开卡")
                    if not self._find_gift_card.find_backpack(hwnd):
                        self.sin_out.emit(f"窗口id:{hwnd} 未成功打开背包")
                        if hwnd not in no_card_hwnd_list:
                            no_card_hwnd_list.append(hwnd)
                        continue

                    self.status_bar.emit(open_card_count)

                    if not self.working:
                        break

                    if not self._find_gift_card.find_gift_card(hwnd):
                        self.sin_out.emit(f"窗口id:{hwnd} 未找到礼卡")
                        if hwnd not in no_card_hwnd_list:
                            no_card_hwnd_list.append(hwnd)
                        continue

                    self._windows_opt.activate_windows(hwnd)
                    time.sleep(0.6)

                    for run_index in range(50):
                        if not self.working:
                            self.sin_out.emit(
                                f"窗口id:{hwnd} 因停止状态退出，当前循环: {run_index}")
                            break

                        if not self._windows_opt.activate_windows(hwnd):
                            self.sin_out.emit(f"窗口id:{hwnd} 未成功激活")
                            continue

                        SetGhostMouse().click_mouse_right_button()
                        time.sleep(0.4)

                        if self._find_gift_card.find_open_loading(hwnd):
                            self.sin_out.emit(f"窗口id:{hwnd} 已开卡...")
                            open_card_count += 1
                            self.status_bar.emit(open_card_count)
                            if hwnd not in opened_hwnd_list:
                                opened_hwnd_list.append(hwnd)
                            break
                        time.sleep(0.1)

                if opened_hwnd_list:
                    time.sleep(2)
                    for hwnd in opened_hwnd_list:
                        self._windows_opt.activate_windows(hwnd)
                        time.sleep(0.6)
                        # get_mouse_x_y 返回的是屏幕坐标，直接移动即可
                        mouse_x, mouse_y = SetGhostMouse().get_mouse_x_y()
                        SetGhostMouse().move_mouse_to(mouse_x - 10, mouse_y - 10)
                        if self._find_gift_card.click_get_all(hwnd):
                            self.sin_out.emit(f"窗口id:{hwnd} 没有钱,领取一些丹药")
                        else:
                            self.sin_out.emit(f"窗口id:{hwnd} 开到钱了")

                no_card_hwnd_list.clear()
                opened_hwnd_list.clear()
        finally:
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
