import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from Utils.FindWindowsImage import WindowsCapture, WindowsHandle
from DeskFunc.TaskBussinese.findDaySkillDance import FindDaySkillDance
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse


class SkillDanceQth(QThread):
    """
    截图
    """
    sin_out = Signal(str)  # 日志打印
    status_bar = Signal(int)  # 底部状态栏，出招了几次
    sin_run_status = Signal(bool)  # 执行状态

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
        self.windows_opt = WindowsHandle()
        self.windows_handle_list = []

        self.find = FindDaySkillDance()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

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
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list

    def run(self):
        self.mutex.lock()  # 先加锁
        self.sin_run_status.emit(True)  # 发送消息，任务开始
        _run_count: int = 0  # 执行了几次技能

        all_skill_num: int = self.find.find_skill_num()  # 技能数量,数量相等就说明全部出招完毕，每个技能出招一次
        _is_dance_ok_hwnd_list: list = []  # 已经演练完成的窗口
        _runed_skill_list: list = []
        _skill_dict: dict = self.find.get_skill_group_list()
        if _skill_dict is None:
            self.sin_out.emit(f"每日演练套路未设置")
            self.working = False

        while 1:

            if not self.working:
                break

            if len(_is_dance_ok_hwnd_list) == len(self.windows_handle_list):
                self.sin_out.emit(f"今天的演练已完成")
                break

            for hwnd in self.windows_handle_list:
                key_str_tuple: tuple = self.find.find_day_skill_dance(hwnd)
                if key_str_tuple is not None:
                    if not self.windows_opt.activate_windows(hwnd):
                        self.sin_out.emit(f"窗口id:{hwnd} 激活失败")
                        continue
                    key_str, key_name, need_ground = key_str_tuple

                    if key_str in _runed_skill_list:
                        continue
                    _runed_skill_list.append(key_str)
                    self.sin_out.emit(f"窗口id:{hwnd} 找到技能:{key_name}")

                    if need_ground:
                        pic = self.windows_cap.capture(hwnd)
                        pos_content: tuple = (int(pic.pic_width / 2), int(pic.pic_height / 2))
                        center_pos_in_screen: tuple = coordinate_change_from_windows(hwnd, pos_content)
                        SetGhostMouse().move_mouse_to(center_pos_in_screen[0], center_pos_in_screen[1])

                    time.sleep(1)
                    SetGhostBoards().click_press_and_release_by_key_name(key_str)
                    _run_count += 1
                    self.status_bar.emit(_run_count)
                    time.sleep(1)

                if _run_count >= all_skill_num:
                    self.sin_out.emit(f"窗口id:{hwnd} 所有技能已演练")
                    if hwnd not in _is_dance_ok_hwnd_list:
                        _is_dance_ok_hwnd_list.append(hwnd)

        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()
