# coding: utf-8
import datetime
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.MoneyCard import FindGiftCard
from Utils.FindWindowsImage import WindowsHandle
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse


class OpenGiftCard(QThread):
    """
    9点开卡
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = WindowsHandle()

        self.mutex = QMutex()
        self.windows_handle_list = []

        self.find_gift_card = FindGiftCard()
        self.mouse = SetGhostMouse()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

    @staticmethod
    def check_local_time() -> bool:
        # 获取当前时间并去除微秒
        current_time = datetime.datetime.now().replace(microsecond=0)
        # 定义目标时间字符串列表
        target_times: list = ["20:59:55", "21:03:55"]

        # 转换为datetime对象并生成时间范围（前后3秒）
        time_ranges = []
        for t in target_times:
            target = datetime.datetime.strptime(t, "%H:%M:%S").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            time_ranges.append((target - datetime.timedelta(seconds=3), target + datetime.timedelta(seconds=3)))

        # 判断当前时间是否落入任一区间
        match_flag: bool = False
        for start, end in time_ranges:
            if start <= current_time <= end:
                match_flag = True
                break
        return match_flag

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def get_param(self, windows_handle_list: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.windows_handle_list = windows_handle_list

    def run(self):
        self.mutex.lock()  # 先加锁

        _is_open_card_hwnd: list = []  # 成功开卡了的窗口
        _open_card_count: int = 0  # 开了几次卡

        self.sin_run_status.emit(True)

        while 1:
            if not self.working:
                break

            # 计算到21点整还有多久
            if not self.check_local_time():
                # 如果还没有到21点
                time.sleep(1)
                continue

            # 先把背包打开,并检查是否有礼卡，如果包裹里没有礼卡的花那就没啥意义了啊
            for hwnd_i in self.windows_handle_list:

                if len(_is_open_card_hwnd) == len(self.windows_handle_list):
                    break

                if hwnd_i in _is_open_card_hwnd:
                    continue

                if not self.find_gift_card.find_backpack(hwnd_i):
                    # 如果包裹里没有礼卡

                    if hwnd_i not in _is_open_card_hwnd:
                        _is_open_card_hwnd.append(hwnd_i)

                    continue

                self.status_bar.emit(_open_card_count)

                if not self.working:
                    break

                # 查询一下有没有礼卡
                if not self.find_gift_card.find_gift_card(hwnd_i):
                    continue

                self.windows_opt.activate_windows(hwnd_i)
                time.sleep(0.6)

                _index_x, _index_y = 0, 0
                for run_i in range(50):

                    if not self.working:
                        break

                    # # 检测一些鼠标的位置，如果人为移动的鼠标，那说明有突发情况，需要停止
                    # x, y = SetGhostMouse().get_mouse_x_y()
                    # if _index_x == 0 and _index_y == 0:
                    #     _index_x, _index_y = x, y
                    # elif x != _index_x or y != _index_y:
                    #     self.sin_out.emit(f"发现鼠标移动,或许有突发情况，停止开卡")
                    #     self.working = False
                    #     break

                    SetGhostMouse().click_mouse_right_button()
                    time.sleep(0.1)
                    if self.find_gift_card.find_open_loading(hwnd_i):
                        self.sin_out.emit(f"窗口id:{hwnd_i}已开卡,请结束后自行查看开卡记录")

                        _open_card_count += 1
                        self.status_bar.emit(_open_card_count)

                        # 鼠标移动一下，避免挡住了包裹的图标
                        m_x, m_y = SetGhostMouse().get_mouse_x_y()
                        w_point = coordinate_change_from_windows(hwnd_i, (m_x-10, 10))
                        SetGhostMouse().move_mouse_to(w_point[0], w_point[1])

                        if hwnd_i not in _is_open_card_hwnd:
                            _is_open_card_hwnd.append(hwnd_i)
                        break

            if len(_is_open_card_hwnd) > 0:
                # 如果，所有的窗口都没有检测到礼卡，那么就可以跳出去了，没有意义
                # 如果所有的窗口已经检测完成了，那么就可以跳出去了，没有意义
                for is_ok_h in _is_open_card_hwnd:
                    self.windows_opt.activate_windows(is_ok_h)
                    time.sleep(0.5)
                    # 如果有“获取全部”的按钮的话，那么就全部关掉吧
                    self.find_gift_card.click_ok(is_ok_h)
                _is_open_card_hwnd.clear()  # 清理掉

        self.mutex.unlock()
        self.sin_run_status.emit(False)
        return None
