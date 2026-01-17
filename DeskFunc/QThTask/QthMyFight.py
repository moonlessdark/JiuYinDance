# coding: utf-8
import datetime
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.XuanJi import FindMyFight
from DeskFunc.TaskBussinese.findCars import TeamFunc
from Utils.FindWindowsImage import WindowsHandle, WindowsCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse


def add_10_seconds():
    """
    调试方法，在当前时间上增加10秒
    """
    current_time = datetime.datetime.now()
    new_time = current_time + datetime.timedelta(seconds=10)
    formatted_time = new_time.strftime("%H:%M:%S")
    return formatted_time



class MyFightXJ(QThread):
    """
    我的战斗-玄机秘境报名
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()
        self.cap = WindowsCapture()
        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = WindowsHandle()

        self.mutex = QMutex()
        self.windows_handle_list = []

        self.find_my_f = FindMyFight()
        self.mouse = SetGhostMouse()

        self.team = TeamFunc()  # 创建队伍

        self.time_ranges = []  # 点击的时间段

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

    def check_local_time(self) -> bool:
        # 获取当前时间并去除微秒
        current_time = datetime.datetime.now().replace(microsecond=0)
        # 定义目标时间字符串列表
        target_times: list = ["19:59:53"]

        # 转换为datetime对象并生成时间范围（前后3秒）
        if len(self.time_ranges) == 0:
            for t in target_times:
                target = datetime.datetime.strptime(t, "%H:%M:%S").replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day
                )
                self.time_ranges.append((target - datetime.timedelta(seconds=3), target + datetime.timedelta(seconds=59)))  # 8点到8点59分59秒

        # 判断当前时间是否落入任一区间
        match_flag: bool = False
        for start, end in self.time_ranges:
            if start < current_time < end:
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

        _open_count: int = 0  # 报名次数
        _is_close_hwnd: list = []  # 已经失效的窗口句柄

        self.sin_run_status.emit(True)

        self.sin_out.emit("任务开始时间为 20:00:00")

        while 1:
            if not self.working:
                break


            # 计算到20点整还有多久
            if not self.check_local_time():
                # 如果还没有到20点
                time.sleep(1)
                continue
            self.sin_out.emit("任务已到开始时间，开始报名")

            for hwnd_i in self.windows_handle_list:

                if not self.working:
                    break

                if not self.cap.windows_handle_visible(hwnd_i):
                    self.sin_out.emit(f"窗口id:{hwnd_i} 失效,请自行检查")
                    if hwnd_i not in _is_close_hwnd:
                        _is_close_hwnd.append(hwnd_i)

                if len(_is_close_hwnd) == len(self.windows_handle_list):
                    # 如果当前所有窗口就失效了，就可以结束了
                    self.working = False
                    self.sin_out.emit("所有窗口均无法识别,已经自动退出任务")
                    break

                # 检测一下当前是否是组队状态
                if self.team.close_team(hwnd_i):
                    self.sin_out.emit(f"窗口id:{hwnd_i} 检测组队状态")

                if not self.windows_opt.activate_windows(hwnd_i):
                    self.sin_out.emit(f"窗口:{hwnd_i} 激活窗口失败")
                    break
                time.sleep(0.2)

                # 点击我的战斗
                if not self.find_my_f.find_my_fight(hwnd_i):
                    self.sin_out.emit(f"窗口id:{hwnd_i} 未找到我的战斗入口")
                    continue
                self.sin_out.emit(f"窗口id:{hwnd_i} 点击我的战斗")

                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                time.sleep(0.5)

                if not self.find_my_f.find_xuan_ji_mi_jing(hwnd_i):
                    self.sin_out.emit(f"窗口id:{hwnd_i} 未找到玄机秘境入口")
                    continue
                self.sin_out.emit(f"窗口id:{hwnd_i} 点击玄机秘境")

                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                time.sleep(1)

                if not self.find_my_f.find_bao_ming(hwnd_i):
                    self.sin_out.emit(f"窗口id:{hwnd_i} 未找到报名按钮")
                    continue
                self.sin_out.emit(f"窗口id:{hwnd_i} 开始报名")
                _is_clicked: bool = False  # 是否报名成功
                for xx in range(50):
                    if not self.working:
                        break

                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.3)
                    if self.find_my_f.find_open_loading(hwnd_i):
                        self.sin_out.emit(f"窗口id:{hwnd_i} 识别到加载中进度条")
                        _is_clicked = True
                        break
                if _is_clicked:
                    self.sin_out.emit(f"窗口id:{hwnd_i} 报名成功")
                    _open_count += 1
                    self.status_bar.emit(_open_count)
                else:
                    self.sin_out.emit(f"窗口id:{hwnd_i} 报名失败")
            self.working = False
        self.sin_out.emit("任务结束")
        self.mutex.unlock()
        self.sin_run_status.emit(False)
        return None
