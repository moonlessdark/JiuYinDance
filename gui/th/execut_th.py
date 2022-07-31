import random
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import time
from numpy import ndarray
from business.windows_screen.get_screen_windows import windowsCap
from common.DMSoft.get_dm_driver import getWindows, getKeyBoardMouse
from business.get_pic_icon.get_pic import getPic


class tuanLianTh(QThread):
    sin_out = pyqtSignal(str)
    status_bar = pyqtSignal(str)
    sin_work_status = pyqtSignal(str)

    def __init__(self, parent=None):
        super(tuanLianTh, self).__init__(parent)
        # 设置工作状态和初始值
        self.wait_time = 0.2
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.windows_handle_list = []
        self.windows_handle_list_log = []
        self.handle_is_execute_list = []
        self.execute_type = None
        self.dm_windows = None
        self.dm_keyboard = None

    def __del__(self):
        # 线程状态改为和线程终止
        self.wait()
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle_list_log = []
        self.handle_is_execute_list = []
        self.windows_handle_list = []
        self.sin_out.emit("窗口停止检测")

    def start_execute_init(self, windows_handle_list, execute_type):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.execute_type = execute_type
        if execute_type == "团练模式":
            self.wait_time = 0.3
        else:
            if len(windows_handle_list) == 1:
                self.wait_time = 0.2
        self.dm_windows = getWindows()
        self.dm_keyboard = getKeyBoardMouse()

    def get_random_time(self, end_time):
        return round(random.uniform(0, end_time), 2)

    def input_key(self, key_list):
        """
        :param handle: 窗口handle_id
        :param key_list: 按钮列表数组
        :return:
        """
        for n in range(len(key_list)):
            key = key_list[n]
            # 具体按钮code看 https://github.com/Gaoyongxian666/pydmdll
            if key == 'j':
                self.dm_keyboard.key_down_char('j')
            elif key == 'k':
                self.dm_keyboard.key_down_char('k')
            elif key == 'up':
                self.dm_keyboard.key_down(38)
            elif key == 'down':
                self.dm_keyboard.key_down(40)
            elif key == 'left':
                self.dm_keyboard.key_down(37)
            elif key == 'right':
                self.dm_keyboard.key_down(39)
            time.sleep(self.get_random_time(self.wait_time))

    def run(self):
        self.mutex.lock()  # 先加锁
        while self.working:
            if self.working is False:
                self.sin_work_status.emit("结束")
                self.mutex.unlock()  # 解锁
                return None
            for i in range(len(self.windows_handle_list)):
                if self.windows_handle_list[i] not in self.windows_handle_list_log:
                    self.status_bar.emit(" %s => %d 号窗口开始检测" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))

                    pic_content: ndarray = windowsCap().capture(self.windows_handle_list[i])
                    key_list = getPic().get_screen_pic(pic_content, execute_type=self.execute_type)
                    if type(key_list) == list and len(key_list) > 0:
                        getWindows().set_window_state(self.windows_handle_list[i], 12)
                        self.input_key(key_list)  # 输入按钮
                        self.sin_out.emit(
                            "%s => %d 窗口按钮为 %s" % (time.strftime("%H:%M:%S", time.localtime()), i + 1, key_list))
                        self.handle_is_execute_list.append(self.windows_handle_list[i])
                    elif type(key_list) == dict:
                        """
                        以下为结束判断
                        """
                        if key_list.get("团练") is True and self.execute_type == "团练模式":
                            """
                            判断团练结束
                            """
                            self.windows_handle_list_log.append(self.windows_handle_list[i])
                            self.sin_out.emit(
                                "%s => %d 号窗口已停止扫描" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))
                        elif key_list.get("授业") is False and self.execute_type == "授业模式":
                            """
                            判断授业结束
                            """
                            if self.windows_handle_list[i] in self.handle_is_execute_list:
                                self.windows_handle_list_log.append(self.windows_handle_list[i])
                                self.sin_out.emit(
                                    "%s => %d 号窗口已停止扫描" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))
                elif len(self.windows_handle_list) == len(self.windows_handle_list_log):
                    self.sin_out.emit("%s => 所有团练或授业已经结束" % (time.strftime("%H:%M:%S", time.localtime())))
                    self.sin_work_status.emit("结束")
                    self.mutex.unlock()
                    return None
                time.sleep(1)
        self.mutex.unlock()
