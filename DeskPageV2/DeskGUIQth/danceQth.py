import os
import random
import time

import cv2
import win32gui
from PySide6.QtCore import Signal, QThread, QWaitCondition, QMutex

from DeskPageV2.Utils.Log import Logger
from DeskPageV2.DeskFindPic.findButton import FindButton
from DeskPageV2.DeskTools.DmSoft.get_dm_driver import getKeyBoardMouse, getWindows
from DeskPageV2.DeskTools.WindowsSoft.get_windows import WindowsCapture, GetHandleList, PicCapture
from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards


def get_local_time():
    """
    获取当前时间
    :return:
    """
    time_string: str = time.strftime("%H:%M:%S", time.localtime(int(time.time())))
    return time_string


def save_pic(pic_content):
    time_str_m = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(int(time.time())))
    pic_file_path = f"./_internal/ErrorLog/"
    if not os.path.exists(pic_file_path):  # 如果主目录+小时+分钟这个文件路径不存在的话
        os.makedirs(pic_file_path)
    cv2.imwrite(pic_file_path + time_str_m + '.png', pic_content)


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
        elif key == '上':
            getKeyBoardMouse().key_down(38, hold_time=get_random_time(wait_time))
        elif key == '下':
            getKeyBoardMouse().key_down(40, hold_time=get_random_time(wait_time))
        elif key == '左':
            getKeyBoardMouse().key_down(37, hold_time=get_random_time(wait_time))
        elif key == '右':
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


def check_windows_size(w: int, h: int) -> int:
    """
    检测屏幕分辨率是否符合要求
    :param h: 高
    :param w: 宽
    :return: 1: 黑屏中，可能是在加载画面
             2: 按钮按下之后的游戏画面
             3: 正常的大于1366*768的游戏画面，可以用于正常识别画面
             0: 不符合要求，游戏画面低于1366*768，无法继续执行
    """
    result_type: int = 0
    if min(w, h) == 0 and max(w, h) > 0:
        """
        最小值是0，最大值有值，说明是在按下按钮后的画面
        """
        result_type = 2
    elif w == 0 and h == 0:
        """
        截图的宽高都是0，表示窗口都是黑色的，可能是在过图或者单纯的游戏画面黑屏了,需要继续等待画面
        """
        result_type = 1
    elif w >= 1340 or h >= 725:
        """
        窗口分辨率正常
        """
        result_type = 3
    return result_type


def input_key_by_ghost(key_list: list):
    """
    :param key_list:
    :return:
    """
    wait_time = 0.3
    for n in range(len(key_list)):
        key: str = key_list[n]
        if key == 'J':
            SetGhostBoards().click_press_and_release_by_key_name('J')
        elif key == 'K':
            SetGhostBoards().click_press_and_release_by_key_name("K")
        elif key == '上':
            SetGhostBoards().click_press_and_release_by_code(38)
        elif key == '下':
            SetGhostBoards().click_press_and_release_by_code(40)
        elif key == '左':
            SetGhostBoards().click_press_and_release_by_code(37)
        elif key == '右':
            SetGhostBoards().click_press_and_release_by_code(39)
        elif key == 'L':
            SetGhostBoards().click_press_and_release_by_key_name('L')
        time.sleep(get_random_time(wait_time))


class DanceThByFindPic(QThread):
    """
    大图找小图的方式
    """
    sin_out = Signal(str)  # 日志打印
    status_bar = Signal(str, int)  # 底部状态栏打印
    sin_work_status = Signal(bool)  # 运行状态是否正常
    log = Logger()

    def __init__(self, parent=None):
        # 设置工作状态和初始值
        super().__init__(parent)
        self.dance_type = "团练"
        self.key_board_mouse_driver_type = None
        self.dm_windows = getWindows()
        self.windows_cap = WindowsCapture()
        self.find_button = FindButton()
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.debug: bool = False

        self.windows_handle_list = []

        self.windows_opt = GetHandleList()

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

    def start_execute_init(self, windows_handle_list: list, dance_type: str, key_board_mouse_driver_type: str,
                           debug: bool):
        """
        线程用到的参数初始化一下
        :param key_board_mouse_driver_type: dm or ghost
        :param windows_handle_list: 窗口handle列表
        :param dance_type: 团练 or 望辉洲
        :param debug:
        :return:
        """
        self.windows_handle_list = []
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.key_board_mouse_driver_type: str = key_board_mouse_driver_type
        self.dance_type = dance_type
        self.debug = debug

    def run(self):
        self.mutex.lock()  # 先加锁
        wait_num_print: int = 0
        wait_game_pic: bool = False  # 是否在等待游戏界面正常
        find_button_count: int = 0  # 本轮发现几个按钮了
        while self.working:
            if self.working is False:
                self.sin_out.emit("窗口停止检测")
                break
            for windows_this_handle in self.windows_handle_list:
                wait_num_print: int = wait_num_print + 1 if wait_num_print < 6 else 0
                self.status_bar.emit("", find_button_count)
                start_time = time.time()
                try:
                    # 开始截图
                    pic_contents: PicCapture = self.windows_cap.capture_and_clear_black_area(windows_this_handle)
                except Exception as e:
                    if windows_is_mini_size(windows_this_handle) is True:
                        """
                        如果窗口时最小化
                        """
                        if wait_game_pic is False:
                            self.sin_out.emit(f"游戏窗口({windows_this_handle}) 未显示画面，请不要最小化窗口。")
                            self.sin_out.emit("等待窗口刷新...")
                            wait_game_pic = True
                        else:
                            self.sin_out.emit(f"游戏窗口分辨率已经符合要求。\n"
                                              f"继续检测游戏窗口...")
                            wait_game_pic = False
                        time.sleep(1)
                        continue
                    self.sin_out.emit(str(e))
                    self.sin_work_status.emit(False)
                    self.working = False
                    break

                __pic_contents: PicCapture = self.windows_cap.capture(windows_this_handle)
                # 开始检查分辨率是否正常
                windows_check_result: int = check_windows_size(w=__pic_contents.pic_width, h=__pic_contents.pic_height)
                if windows_check_result == 0:
                    """
                    如果分辨率太低了
                    """
                    if wait_game_pic is False:
                        self.sin_out.emit(f"游戏窗口分辨率过低，请重新设置游戏窗口m分辨率大于1366*768。\n"
                                          f"当前分辨率为 {__pic_contents.pic_width}*{__pic_contents.pic_height} 。")
                        self.sin_out.emit("等待窗口刷新...")
                    else:
                        self.sin_out.emit("等待窗口刷新...")
                    wait_game_pic = True
                    time.sleep(1)
                    continue
                elif windows_check_result in [1, 2]:
                    """
                    1：表示在加载过程动画的黑屏或者其他的黑屏
                    2：表示按钮之后的动画效果
                    """
                    time.sleep(1)
                    continue
                else:
                    if wait_game_pic:
                        wait_game_pic = False
                        self.sin_out.emit(f"游戏窗口分辨率已经符合要求。\n"
                                          f"当前分辨率为 {__pic_contents.pic_width}*{__pic_contents.pic_height} 。\n"
                                          f"继续检测游戏窗口...")

                # 开始检查是否有按钮出现
                key_list: list = self.find_button.find_pic_by_bigger(bigger_pic_cap=pic_contents,
                                                                     find_type=self.dance_type,
                                                                     debug=self.debug,
                                                                     single=self.sin_out)
                if len(key_list) > 0:
                    if self.debug:
                        end_time = time.time()
                        execution_time = end_time - start_time
                        self.log.write_log(f"识别时间为: {round(execution_time, 2)}秒")
                    if self.windows_opt.activate_windows(windows_this_handle):
                        input_key_by_ghost(key_list)  # 输入按钮
                        find_button_count += 1
                        key_arr: str = "".join(key_list)
                        self.sin_out.emit(f"窗口按钮: {key_arr}")
                        if self.debug:
                            end_time = time.time()
                            execution_time = end_time - start_time
                            self.log.write_log(f"执行时间为: {round(execution_time, 2)}秒 \n")

                    else:
                        self.sin_out.emit(f"出错了,窗口{windows_this_handle}激活失败,尝试再次激活")
                        continue
                if len(self.windows_handle_list) > 1:
                    """
                    如果此时有个以上窗口在扫描，那么就加快一点进度
                    """
                    time.sleep(0.1)
                else:
                    """
                    如果现在是只有一个窗口在扫描，那么就慢一点，1秒一次
                    """
                    time.sleep(1)
        self.mutex.unlock()
        self.status_bar.emit("等待执行", 0)
        return None


class ScreenGameQth(QThread):
    """
    截图
    """
    sin_out = Signal(str)
    status_bar = Signal(str)

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
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

        # 先创建一个文件
        time_str_m = time.strftime("%H_%M", time.localtime(int(time.time())))
        pic_file_path = self.pic_save_path + "/JiuYinScreenPic/" + time_str_m + "/"
        if not os.path.exists(pic_file_path):  # 如果主目录+小时+分钟这个文件路径不存在的话
            os.makedirs(pic_file_path)

        while self.working:
            if self.working is False:
                self.mutex.unlock()  # 解锁
                self.sin_out.emit("窗口停止截图")
                return None
            for handle in range(len(self.windows_handle_list)):
                self.status_bar.emit("窗口截图中...")
                try:
                    pic_content_obj: PicCapture = self.windows_cap.capture(
                        self.windows_handle_list[handle])
                    if min(pic_content_obj.pic_height, pic_content_obj.pic_width) > 0:
                        time_str_s = time.strftime("%H_%M_%S", time.localtime(int(time.time())))
                        cv2.imwrite(f"{pic_file_path}{time_str_s}.png", pic_content_obj.pic_content)
                    else:
                        print(f"{pic_content_obj.pic_height}__{pic_content_obj.pic_width}")
                except Exception as e:
                    self.sin_out.emit("%s" % str(e))
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
