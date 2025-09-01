import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.danceButton import FindButton
from Utils.FindWindowsImage import WindowsCapture, WindowsHandle, PicCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, get_random_time


def input_key_by_ghost(key_list: list):
    """
    :param key_list:
    :return:
    """
    wait_time = 0.3
    time.sleep(0.1)
    for n in range(len(key_list)):
        key: str = key_list[n]
        if key == 'J':
            SetGhostBoards().click_press_and_release_by_key_name('J')
        elif key == 'K':
            SetGhostBoards().click_press_and_release_by_key_name("K")
        elif key == 'UP':
            SetGhostBoards().click_press_and_release_by_code(38)
        elif key == 'Down':
            SetGhostBoards().click_press_and_release_by_code(40)
        elif key == 'Left':
            SetGhostBoards().click_press_and_release_by_code(37)
        elif key == 'Right':
            SetGhostBoards().click_press_and_release_by_code(39)
        elif key == 'L':
            SetGhostBoards().click_press_and_release_by_key_name('L')
        time.sleep(get_random_time(wait_time))


# 定义映射关系
mapping = {
    "UP": "上",
    "Down": "下",
    "Left": "左",
    "Right": "右",
    "J": "J",
    "K": "K",
    "L": "L",
}


class DanceThByFindPic(QThread):

    sin_out = Signal(str)  # 日志打印
    status_bar = Signal(int)  # 底部状态栏打印
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()

        self._hwnd_list: list = []

        self.windows_cap = WindowsCapture()  # 截图
        self.windows_opt = WindowsHandle()  # 激活窗口
        self.find_button = FindButton()
        self.dance_type = None

        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

    def __del__(self):
        self.working = False

    def stop_stak(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def init_task_param(self, hwnd_list: list, dance_type: str):
        """
        初始化执行参数
        :param dance_type: grey 或者 green
        :param hwnd_list: 需要检测的窗口句柄
        :return:
        """
        self._hwnd_list = hwnd_list
        self.dance_type = dance_type
        self.working = True

    def run(self):
        self.mutex.lock()  # 先加锁

        find_button_count: int = 0  # 当前是第几轮执行
        self.sin_run_status.emit(True)  # 发送消息，任务开始执行了
        while self.working:

            self.status_bar.emit(find_button_count)  # 打印一下执行了几次按钮
            if self.working is False:
                break
            for hwnd in self._hwnd_list:
                # 2种模式都执行一次。先找团练授业，如果没有找到就去找绿色的上下左右

                if self.working is False:
                    break
                # start_time = time.time()

                _w_cap: PicCapture = self.windows_cap.capture(hwnd)
                if _w_cap is None:
                    continue

                if self.dance_type == "grey":
                    _button_list: list = self.find_button.find_button(_w_cap.pic_content)
                else:
                    _button_list: list = self.find_button.find_button_green(_w_cap.pic_content)

                if len(_button_list) == 0:
                    # 如果没有找到按钮，那么就可以下一个了
                    continue

                # end_time = time.time()
                # time_diff = end_time - start_time

                # 将时间差转换为字符串并打印
                # print("执行时间:" + str(time_diff) + str(_button_list))

                if self.windows_opt.activate_windows(hwnd) is False:
                    self.sin_out.emit(f"窗口: {hwnd} 激活失败,任务停止执行")
                    self.working = False
                    break

                input_key_by_ghost(_button_list)  # 输入按钮
                find_button_count += 1
                self.sin_out.emit(f"按钮: {''.join(list(map(lambda x: mapping[x], _button_list)))}")
                if len(self._hwnd_list) == 1:
                    # 如果当前只有一个窗口，那么在连续识别时就停止一下，避免识别太快的问题。连续识别多个窗口就没用问题了
                    time.sleep(0.5)
        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()  # 解锁
        return None
