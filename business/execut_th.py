import random
import win32con
import win32gui
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import time
from business.get_dm_tools.pydamo_0.damo import Key, DM
from business.windows_screen.get_screen_windows import windowsCap
from business.get_pic_icon.get_pic import getPic


class tuanLianTh(QThread):
    sin_out = pyqtSignal(str)
    status_bar = pyqtSignal(str)
    sin_work_status = pyqtSignal(str)

    def __init__(self, continuous=False, parent=None):
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
        self.dm = DM()
        self.kk = Key(self.dm)

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
            self.wait_time = 0.4
        else:
            if len(windows_handle_list) == 1:
                self.wait_time = 0.2
        print("变量")

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
                self.kk.dp('j', self.get_random_time(self.wait_time))
            elif key == 'k':
                self.kk.dp('k', self.get_random_time(self.wait_time))
            elif key == 'up':
                self.kk.dp(38, self.get_random_time(self.wait_time))
            elif key == 'down':
                self.kk.dp(40, self.get_random_time(self.wait_time))
            elif key == 'left':
                self.kk.dp(37, self.get_random_time(self.wait_time))
            elif key == 'right':
                self.kk.dp(39, self.get_random_time(self.wait_time))

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
                    key_list = getPic().get_screen_pic(windowsCap().capture(self.windows_handle_list[i]),
                                                       execute_type=self.execute_type)
                    if type(key_list) == list and len(key_list) > 0:
                        # 如果返回的是数组那就说明里面有按钮
                        # 切换并激活这个窗口
                        win32gui.ShowWindow(self.windows_handle_list[i], win32con.SW_SHOWMAXIMIZED)
                        win32gui.SetForegroundWindow(self.windows_handle_list[i])
                        time.sleep(0.5)  # 这里加一下等待，避免窗口切换后响应较慢

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