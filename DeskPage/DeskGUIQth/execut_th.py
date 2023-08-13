import os
import random
import time

import cv2
import numpy
import win32gui
from PySide6.QtCore import Signal, QThread, QWaitCondition, QMutex

from DeskPage.DeskDance.findPicBySmallToBigger.findButton import FindButton
from DeskPage.DeskTools.DmSoft.get_dm_driver import getKeyBoardMouse, getWindows
from DeskPage.DeskTools.WindowsSoft.get_windows import windowsCap, GetHandleList
from DeskPage.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards


def get_random_time(end_time):
    """
    随机一个保留2位小数
    :param end_time:
    :return:
    """
    return round(random.uniform(0.05, end_time), 2)


def input_key_by_dm(key_list: list):
    """
    :param key_list: 按钮列表数组
    :return:
    """
    wait_time = 0.4
    for n in range(len(key_list)):
        key: str = key_list[n]
        # 具体按钮code看 https://github.com/Gaoyongxian666/pydmdll
        if key == 'J':
            getKeyBoardMouse().key_down_char('j', hold_time=get_random_time(wait_time))
        elif key == 'K':
            getKeyBoardMouse().key_down_char('k', hold_time=get_random_time(wait_time))
        elif key == 'UP':
            getKeyBoardMouse().key_down(38, hold_time=get_random_time(wait_time))
        elif key == 'Down':
            getKeyBoardMouse().key_down(40, hold_time=get_random_time(wait_time))
        elif key == 'Left':
            getKeyBoardMouse().key_down(37, hold_time=get_random_time(wait_time))
        elif key == 'Right':
            getKeyBoardMouse().key_down(39, hold_time=get_random_time(wait_time))
        elif key == 'L':
            getKeyBoardMouse().key_down_char('l', hold_time=get_random_time(wait_time))
        time.sleep(get_random_time(wait_time))


def windows_is_mini_size(check_windows_handle: int) -> bool:
    """
    检测传入的窗口id是否激活状态
    :param check_windows_handle:
    :return:
    """
    if win32gui.IsIconic(check_windows_handle):
        return True
    return False


def activate_windows(windows_handle: int):
    """
    激活窗口
    :param windows_handle: 窗口id
    :return:
    """
    GetHandleList().activate_windows(windows_handle)
    time.sleep(0.2)


def input_key_by_ghost(key_list: list):
    """
    :param key_list:
    :return:
    """
    wait_time = 0.3
    for n in range(len(key_list)):
        key: str = key_list[n]
        # 具体按钮code看 https://github.com/Gaoyongxian666/pydmdll
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


class DanceThByFindPic(QThread):
    """
    大图找小图的方式
    """
    sin_out = Signal(str)
    status_bar = Signal(str)
    sin_work_status = Signal(str)

    def __init__(self, parent=None):
        # 设置工作状态和初始值
        super().__init__(parent)
        self.key_board_mouse_driver_list: list = []
        self.dance_type = "团练"
        self.key_board_mouse_driver_type = "dm"
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.windows_handle_list = []

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
        self.sin_out.emit("窗口停止检测")

    def start_execute_init(self, windows_handle_list: list, dance_type: str, key_board_mouse_driver_type: str):
        """
        线程用到的参数初始化一下
        :param key_board_mouse_driver_type: dm or ghost
        :param windows_handle_list: 窗口handle列表
        :param dance_type: 团练 or 望辉洲
        :return:
        """
        self.windows_handle_list = []
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.key_board_mouse_driver_type: str = key_board_mouse_driver_type
        self.dance_type = dance_type

    def run(self):
        self.mutex.lock()  # 先加锁
        wait_num_print: int = 0
        while self.working:
            if self.working is False:
                self.sin_work_status.emit("结束")
                self.mutex.unlock()  # 解锁
                return None
            for windows_this_handle in self.windows_handle_list:
                wait_num_print = wait_num_print + 1 if wait_num_print < 6 else 0
                try:
                    if windows_is_mini_size(windows_this_handle) is False:
                        self.status_bar.emit(
                            "窗口检测中 => %s %s" % (time.strftime("%H:%M:%S", time.localtime()), "." * wait_num_print))

                        pic_content, width, high = windowsCap().capture(windows_this_handle)
                        key_list = FindButton().find_pic_by_bigger(pic_content, pic_size=[high, width],
                                                                   find_type=self.dance_type)
                        if len(key_list) > 0:
                            key_str_list = numpy.array(key_list)
                            key_str_list[numpy.where(key_str_list == "UP")] = "上"
                            key_str_list[numpy.where(key_str_list == "Down")] = "下"
                            key_str_list[numpy.where(key_str_list == "Left")] = "左"
                            key_str_list[numpy.where(key_str_list == "Right")] = "右"
                            self.sin_out.emit("%s=>窗口(%s)按钮:%s" % (
                            time.strftime("%H:%M:%S", time.localtime()), windows_this_handle, "".join(key_str_list)))

                            if self.key_board_mouse_driver_type == "ghost":
                                GetHandleList().activate_windows(windows_this_handle)   # 激活窗口
                                input_key_by_ghost(key_list)  # 输入按钮
                            else:
                                getWindows().set_window_state(hwnd=windows_this_handle, flag=12)  # 激活窗口
                                input_key_by_dm(key_list)  # 输入按钮

                            time.sleep(0.3)

                    else:
                        self.status_bar.emit("窗口(%s)未显示，请不要最小化窗口" % str(windows_this_handle))
                        time.sleep(1)
                except Exception as e:
                    self.sin_out.emit("出错了:%s" % str(e))
                    self.sin_work_status.emit("结束")
                    self.mutex.unlock()
                    return None
        self.mutex.unlock()


class ScreenGameQth(QThread):
    sin_out = Signal(str)
    status_bar = Signal(str)
    sin_work_status = Signal(str)

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.windows_handle_list = []

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
        self.windows_handle_list = []
        self.sin_out.emit("窗口停止截图")

    def get_param(self, windows_handle_list: list, pic_save_path: str):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.pic_save_path = pic_save_path

    def run(self):
        self.mutex.lock()  # 先加锁
        while self.working:
            if self.working is False:
                self.sin_work_status.emit("结束")
                self.mutex.unlock()  # 解锁
                return None
            for i in range(len(self.windows_handle_list)):
                self.status_bar.emit("%s => 窗口截图中..." % time.strftime("%H:%M:%S", time.localtime()))
                try:
                    pic_content, width, high = windowsCap().capture(self.windows_handle_list[i])
                    time_str_m = time.strftime("%H_%M", time.localtime(int(time.time())))
                    pic_file_path = self.pic_save_path + "/JiuYinScreenPic/" + time_str_m + "/"
                    if not os.path.exists(pic_file_path):  # 如果主目录+小时+分钟这个文件路径不存在的话
                        os.makedirs(pic_file_path)
                    time_str_s = time.strftime("%S", time.localtime(int(time.time())))
                    cv2.imencode('.png', pic_content)[1].tofile(pic_file_path + time_str_s + '.png')
                except Exception as e:
                    self.sin_out.emit("%s" % str(e))
                    self.sin_work_status.emit("结束")
                    self.mutex.unlock()
                    return None
            time.sleep(1)
        self.mutex.unlock()


if __name__ == '__main__':
    time_str = time.strftime("%H_%M", time.localtime(int(time.time())))
    for i in range(10):
        time_strs = time.strftime("%S", time.localtime(int(time.time())))
        print(time_strs)
        time.sleep(1)
