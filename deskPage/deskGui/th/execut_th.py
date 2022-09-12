import random
import numpy
from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import time

from deskPage.bussinese.dance.findPicByHashCom.get_pic_icon.get_pic import getPic
from deskPage.bussinese.dance.findPicBySmallToBigger.findButton import FindButton
from deskPage.bussinese.signIn.get_page_element import business
from deskPage.common.dmSoft.get_dm_driver import getWindows, getKeyBoardMouse
from deskPage.common.windowsSoft.get_windows import windowsCap


class DanceThByFindPic(QThread):
    """
    大图找小图的方式
    """
    sin_out = pyqtSignal(str)
    status_bar = pyqtSignal(str)
    sin_work_status = pyqtSignal(str)

    def __init__(self, parent=None):
        # 设置工作状态和初始值
        super().__init__(parent)
        self.wait_time = 0.20
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.windows_handle_list = []
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
        self.windows_handle_list = []
        self.sin_out.emit("窗口停止检测")

    def start_execute_init(self, windows_handle_list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.dm_windows = getWindows()
        self.dm_keyboard = getKeyBoardMouse()

    @staticmethod
    def get_random_time(end_time):
        """
        随机一个保留2位小数
        :param end_time:
        :return:
        """
        return round(random.uniform(0.01, end_time), 2)

    def input_key(self, key_list):
        """
        :param key_list: 按钮列表数组
        :return:
        """
        for n in range(len(key_list)):
            key = key_list[n]
            # 具体按钮code看 https://github.com/Gaoyongxian666/pydmdll
            if key == 'J':
                self.dm_keyboard.key_down_char('j', hold_time=self.get_random_time(self.wait_time))
            elif key == 'K':
                self.dm_keyboard.key_down_char('k', hold_time=self.get_random_time(self.wait_time))
            elif key == 'UP':
                self.dm_keyboard.key_down(38, hold_time=self.get_random_time(self.wait_time))
            elif key == 'Down':
                self.dm_keyboard.key_down(40, hold_time=self.get_random_time(self.wait_time))
            elif key == 'Left':
                self.dm_keyboard.key_down(37, hold_time=self.get_random_time(self.wait_time))
            elif key == 'Right':
                self.dm_keyboard.key_down(39, hold_time=self.get_random_time(self.wait_time))
            time.sleep(self.get_random_time(self.wait_time))

    def run(self):
        self.mutex.lock()  # 先加锁
        while self.working:
            if self.working is False:
                self.sin_work_status.emit("结束")
                self.mutex.unlock()  # 解锁
                return None
            for i in range(len(self.windows_handle_list)):
                self.status_bar.emit(" %s => %d 号窗口开始检测" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))
                try:
                    pic_content, width, high = windowsCap().capture(self.windows_handle_list[i])
                    key_list = FindButton().find_pic_by_bigger(pic_content, pic_size=[high, width])
                    if len(key_list) > 0:
                        getWindows().set_window_state(self.windows_handle_list[i], 12)
                        self.input_key(key_list)  # 输入按钮
                        key_str_list = numpy.array(key_list)
                        key_str_list[numpy.where(key_str_list == "UP")] = "上"
                        key_str_list[numpy.where(key_str_list == "Down")] = "下"
                        key_str_list[numpy.where(key_str_list == "Left")] = "左"
                        key_str_list[numpy.where(key_str_list == "Right")] = "右"
                        self.sin_out.emit(
                            "%s => %d 号窗口按钮为 %s" % (time.strftime("%H:%M:%S", time.localtime()), i + 1, "".join(key_str_list)))
                    time.sleep(0.5)
                except Exception as e:
                    self.sin_out.emit("%s" % str(e))
                    self.sin_work_status.emit("结束")
                    self.mutex.unlock()
                    return None
        self.mutex.unlock()


class DanceThByHash(QThread):
    """
    以哈希的形式查找图片
    """
    sin_out = pyqtSignal(str)
    status_bar = pyqtSignal(str)
    sin_work_status = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DanceThByHash, self).__init__(parent)
        # 设置工作状态和初始值
        self.wait_time = 0.3
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

    def start_execute_init(self, windows_handle_list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.dm_windows = getWindows()
        self.dm_keyboard = getKeyBoardMouse()

    @staticmethod
    def get_random_time(end_time):
        """
        随机一个保留2位小数
        :param end_time:
        :return:
        """
        return round(random.uniform(0.01, end_time), 2)

    def input_key(self, key_list):
        """
        :param key_list: 按钮列表数组
        :return:
        """
        for n in range(len(key_list)):
            key = key_list[n]
            # 具体按钮code看 https://github.com/Gaoyongxian666/pydmdll
            if key == 'j':
                self.dm_keyboard.key_down_char('j', hold_time=self.get_random_time(self.wait_time))
            elif key == 'k':
                self.dm_keyboard.key_down_char('k', hold_time=self.get_random_time(self.wait_time))
            elif key == 'up':
                self.dm_keyboard.key_down(38, hold_time=self.get_random_time(self.wait_time))
            elif key == 'down':
                self.dm_keyboard.key_down(40, hold_time=self.get_random_time(self.wait_time))
            elif key == 'left':
                self.dm_keyboard.key_down(37, hold_time=self.get_random_time(self.wait_time))
            elif key == 'right':
                self.dm_keyboard.key_down(39, hold_time=self.get_random_time(self.wait_time))
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
                    try:
                        pic_content, width, high = windowsCap().capture(self.windows_handle_list[i])
                        key_list = getPic().get_screen_pic(pic_content, execute_type=self.execute_type, resolution_ratio=width)
                        if type(key_list) == list and len(key_list) > 0:
                            getWindows().set_window_state(self.windows_handle_list[i], 12)
                            self.input_key(key_list)  # 输入按钮
                            self.sin_out.emit("%s => %d 窗口按钮为 %s" % (time.strftime("%H:%M:%S", time.localtime()), i + 1, key_list))
                            self.handle_is_execute_list.append(self.windows_handle_list[i])
                    except Exception as e:
                        self.sin_out.emit("%s" % str(e))
                        return None
                    # elif type(key_list) == dict:
                    #     """
                    #     以下为结束判断
                    #     """
                    #     if key_list.get("团练") is True and self.execute_type == "团练模式":
                    #         """
                    #         判断团练结束
                    #         """
                    #         self.windows_handle_list_log.append(self.windows_handle_list[i][0])
                    #         self.sin_out.emit(
                    #             "%s => %d 号窗口已停止扫描" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))
                    #     elif key_list.get("授业") is False and self.execute_type == "授业模式":
                    #         """
                    #         判断授业结束
                    #         """
                    #         if self.windows_handle_list[i][0] in self.handle_is_execute_list:
                    #             self.windows_handle_list_log.append(self.windows_handle_list[i])
                    #             self.sin_out.emit(
                    #                 "%s => %d 号窗口已停止扫描" % (time.strftime("%H:%M:%S", time.localtime()), i + 1))
                elif len(self.windows_handle_list) == len(self.windows_handle_list_log):
                    self.sin_out.emit("%s => 所有团练或授业已经结束" % (time.strftime("%H:%M:%S", time.localtime())))
                    self.sin_work_status.emit("结束")
                    self.mutex.unlock()
                    return None
                time.sleep(1)
        self.mutex.unlock()


class signInTh(QThread):
    """
    微信签到
    """
    sin_out_sign = pyqtSignal(str)
    work_status_sign = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        # 设置工作状态和初始值
        self.working = True
        self.is_First_time = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.account = None
        self.password = None
        self.area = None
        self.service = None
        self.error_pic_path = None
        self.is_check = False

    def __del__(self):
        # 线程状态改为和线程终止
        self.working = False
        self.wait()

    def pause(self):
        """
        线程暂停
        :return:
        """
        self.working = False

    def start_execute(self):
        """
        线程开始
        :return:
        """
        self.working = True
        self.is_First_time = False

    # def resource_path(self, relative_path):
    #     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    #     return os.path.join(base_path, relative_path)

    def get_parm(self, account: str, password: str, area: str, service: str, is_check: bool = False, error_pic_path: str or None = None) -> bool:
        """
        :param is_check: 是否时检测模式
        :param account: 登录账号，如果有多个，请用英文的 , 隔开
        :param password: 登录密码，如果有多个，请用英文的 , 隔开
        :param area: 武侠区
        :param service: 侠骨丹心
        :param error_pic_path: 出现异常时的截图保持地址
        :return:
        """
        account = account.replace("，", ",")
        account = account.replace(" ", "")
        password = password.replace("，", ",")
        password = password.replace(" ", "")
        self.account = account.split(",") if "," in account else [account]
        self.password = password.split(",") if "," in password else [password]
        self.area = area
        self.service = service
        self.error_pic_path = error_pic_path
        self.is_check = is_check
        if len(self.account) != len(self.password):
            self.sin_out_sign.emit("账号和密码数量不一致，请完善")
            return False
        return True

    def run(self):
        """
        主方法，对比图片使用
        :return:
        """
        self.mutex.lock()
        while True:
            self.work_status_sign.emit(True)
            if self.working is False:
                self.mutex.unlock()
                self.sin_out_sign.emit("已结束")
                self.work_status_sign.emit(False)
                return None
            go = business(self.sin_out_sign, self.work_status_sign, self.error_pic_path)
            if go.get_driver():
                if self.is_check:
                    """
                    如果时检测模式，那检查完就可以出去了
                    """
                    self.mutex.unlock()
                    self.sin_out_sign.emit("已结束")
                    self.work_status_sign.emit(False)
                    return None

                self.sin_out_sign.emit("环境已就绪，即将开始签到，请稍等")
                if go.get_url():
                    # 如果正常访问url
                    for li in range(len(self.account)):
                        if go.login(account=self.account[li], password=self.password[li]):
                            if go.select_area(area=self.area, service=self.service):
                                # 如果正常登录进来了
                                go.sign_wechat()
                                if li == len(self.account) - 1:
                                    # 说明已经来到最后一个账号，那就没必要推出了，之间关闭浏览器吧
                                    go.quit()
                                else:
                                    go.login_out()
                        else:
                            self.sin_out_sign.emit("账号（%s）登录失败，请重试或检查账号密码" % str(self.account[li]))
                self.pause()

