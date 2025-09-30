# coding: utf-8
import datetime
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.XuanJi import FindMyFight
from Utils.FindWindowsImage import WindowsHandle
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse


class MyFightXJ(QThread):
    """
    我的战斗-玄机秘境报名
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

        self.find_my_f = FindMyFight()
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
        target_times: list = ["20:11:00"]

        # 转换为datetime对象并生成时间范围（前后3秒）
        time_ranges = []
        for t in target_times:
            target = datetime.datetime.strptime(t, "%H:%M:%S").replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            time_ranges.append((target - datetime.timedelta(seconds=3), target + datetime.timedelta(seconds=59)))  # 8点到8点59分59秒

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

        _is_clicked_hwnd: list = []  # 成功开卡了的窗口
        _open_count: int = 0  # 开了几次卡

        self.sin_run_status.emit(True)

        self.sin_out.emit("任务开始时间为 20:09:00")

        while 1:
            if not self.working:
                break

            # 计算到20点整还有多久
            if not self.check_local_time():
                # 如果还没有到20点
                time.sleep(1)
                continue
            self.sin_out.emit("任务已到开始时间，开始报名")

            # 先把背包打开,并检查是否有礼卡，如果包裹里没有礼卡的花那就没啥意义了啊
            for hwnd_i in self.windows_handle_list:

                if hwnd_i in _is_clicked_hwnd:
                    # 已经执行过了
                    continue

                if not self.working:
                    break

                self.windows_opt.activate_windows(hwnd_i)
                time.sleep(0.2)

                # 点击我的战斗
                if not self.find_my_f.find_my_fight(hwnd_i):
                    continue

                time.sleep(0.1)
                SetGhostMouse().click_mouse_left_button()
                time.sleep(0.5)

                if not self.find_my_f.find_xuan_ji_mi_jing(hwnd_i):
                    continue

                time.sleep(0.1)
                SetGhostMouse().click_mouse_left_button()
                time.sleep(0.5)

                if not self.find_my_f.find_bao_ming(hwnd_i):
                    continue

                self.sin_out.emit("开始报名")

                for xx in range(10):
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.3)
                    if self.find_my_f.find_open_loading(hwnd_i) is False:
                        continue
                    else:
                        self.sin_out.emit(f"窗口:{hwnd_i} 报名成功")
                        _open_count += 1
                        self.status_bar.emit(_open_count)
                        break
            self.working = False
        self.sin_out.emit("任务结束")
        self.mutex.unlock()
        self.sin_run_status.emit(False)
        return None
