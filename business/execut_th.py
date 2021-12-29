import random
import time

import win32com
import win32con
import win32gui
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import time
from ctypes import windll

from bd_time import Time
from pydamo_0 import DM, Key, Mouse

from business.action_keyboad.button_click import buttonClick
from business.windows_screen.get_screen_windows import windowsCap
from business.get_pic_icon.get_pic import getPic
from business.action_keyboad.button_click import buttonClick


class signalThreading(QThread):
    sin_out = pyqtSignal(str)
    sin_work_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 设置工作状态和初始值
        self.working = True
        self.open_handle_num = 1
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.click = buttonClick()

        self.windows_handle_list = []

        dm = DM()
        self.ms = Mouse(dm)
        self.kk = Key(dm)
        self.tt = Time()

    def __del__(self):
        # 线程状态改为和线程终止
        self.working = False
        # self.wait()

    def pause(self):
        """
        线程暂停
        :return:
        """
        self.working = False

    def start_execute_init(self, windows_handle_list):
        """
        线程开始
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list

    def run(self):
        """
        主方法，对比图片使用
        :return:
        """
        self.mutex.lock()
        while self.working:
            if self.working is False:
                self.sin_out.emit("窗口停止检测")
                self.sin_work_status.emit("结束")
                self.mutex.unlock()
                return None

            for i in range(len(self.windows_handle_list)):

                self.sin_out.emit("%s=> %d 号窗口开始检测" % (time.strftime("%H:%M:%S", time.localtime()), i+1))
                key_list = getPic().get_screen_pic(windowsCap().capture(self.windows_handle_list[i]))
                if key_list is not None and len(key_list) > 0:
                    win32gui.SetForegroundWindow(self.windows_handle_list[i])
                    # 设置为活动的，方便输入按键
                    win32gui.ShowWindow(self.windows_handle_list[i], win32con.SW_SHOW)
                    time.sleep(0.1)
                    for n in range(len(key_list)):
                        key = key_list[n]
                        if key == 'j':
                            self.kk.dp('j', round(random.uniform(0, 0.2), 2))
                        elif key == 'k':
                            self.kk.dp('k', round(random.uniform(0, 0.2), 2))
                        elif key == 'up':
                            self.kk.dp(38, round(random.uniform(0, 0.2), 2))
                        elif key == 'down':
                            self.kk.dp(40, round(random.uniform(0, 0.2), 2))
                        elif key == 'left':
                            self.kk.dp(37, round(random.uniform(0, 0.2), 2))
                        elif key == 'right':
                            self.kk.dp(39, round(random.uniform(0, 0.2), 2))
                    self.sin_out.emit("%s 本轮团练结束,按钮为 %s" % (time.strftime("%H:%M:%S", time.localtime()), key_list))
                else:
                    self.sin_out.emit("%s=> 还没有检测到团练信号" % time.strftime("%H:%M:%S", time.localtime()))
                time.sleep(1)
        self.sin_out.emit("窗口停止检测")
        self.mutex.unlock()
