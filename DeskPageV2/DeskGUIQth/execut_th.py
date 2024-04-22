import os
import random
import win32gui
from PySide6.QtCore import Signal, QThread, QWaitCondition, QMutex

from DeskPageV2.Utils.Log import Logger
from DeskPageV2.DeskFindPic.findButton import FindButton
from DeskPageV2.DeskFindPic.findCars import *
from DeskPageV2.DeskTools.DmSoft.get_dm_driver import getKeyBoardMouse, getWindows
from DeskPageV2.DeskTools.WindowsSoft.get_windows import WindowsCapture, GetHandleList, PicCapture
from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards
from DeskPageV2.Utils.keyEvenQTAndGhost import qt_key_get_ghost_key_code


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
    if w >= 1366 or h >= 768:
        """
        窗口分辨率正常
        """
        result_type = 3
    elif min(w, h) == 0 and max(w, h) > 768:
        """
        最小值是0，最大值有值，说明是在按下按钮后的画面
        """
        result_type = 2
    elif w == 0 and h == 0:
        """
        截图的宽高都是0，表示窗口都是黑色的，可能是在过图或者单纯的游戏画面黑屏了,需要继续等待画面
        """
        result_type = 1
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
        self.sin_out.emit("窗口停止检测")

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

                # 开始检查分辨率是否正常
                windows_check_result: int = check_windows_size(w=pic_contents.pic_width, h=pic_contents.pic_height)
                if windows_check_result == 0:
                    """
                    如果分辨率太低了
                    """
                    if wait_game_pic is False:
                        self.sin_out.emit(f"游戏窗口分辨率过低，请重新设置游戏窗口m分辨率大于1366*768。\n"
                                          f"当前分辨率为 {pic_contents.pic_width}*{pic_contents.pic_height} 。")
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
                                          f"当前分辨率为 {pic_contents.pic_width}*{pic_contents.pic_height} 。\n"
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

        # 先创建一个文件
        time_str_m = time.strftime("%H_%M", time.localtime(int(time.time())))
        pic_file_path = self.pic_save_path + "/JiuYinScreenPic/" + time_str_m + "/"
        if not os.path.exists(pic_file_path):  # 如果主目录+小时+分钟这个文件路径不存在的话
            os.makedirs(pic_file_path)

        while self.working:
            if self.working is False:
                self.mutex.unlock()  # 解锁
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


class QProgressBarQth(QThread):
    """
    底部的跑马灯进度条
    """
    thread_step = Signal(int)

    def __init__(self):

        super(QProgressBarQth, self).__init__()
        self.working = True
        self.step = 0  # 进度条跑马灯效果初始值设置为0
        self.mutex = QMutex()

    def __del__(self):
        self.working = False

    def start_init(self):
        self.working = True
        self.step = 0

    def stop_init(self):
        self.working = False
        self.step = 0

    def run(self):

        self.mutex.lock()  # 先加锁
        while self.working:
            if self.step < 101:
                self.step += 1
                self.thread_step.emit(self.step)
            else:
                self.step = 0
            time.sleep(0.001)
        self.thread_step.emit(0)
        self.mutex.unlock()
        return None


class AutoPressKeyQth(QThread):
    """
    键盘连点器
    """
    sin_out = Signal(str)
    status_bar = Signal(str)
    sin_work_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle = 0
        self.key_press_list: str = ""
        self.press_count: int = 0
        self.press_wait_time: int = 0

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
        self.windows_handle = 0

    def get_param(self, windows_handle: int, key_press_list: str, press_count: int, press_wait_time: float):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle
        self.key_press_list = key_press_list
        self.press_count = press_count
        self.press_wait_time = press_wait_time

    def run(self):
        self.mutex.lock()  # 先加锁
        key_code_list = qt_key_get_ghost_key_code(self.key_press_list)
        print(key_code_list)
        for count_i in range(self.press_count):
            if self.working is False:
                break
            wait_time: float = random.uniform(self.press_wait_time, self.press_wait_time + 2)
            time.sleep(round(wait_time, 2))
            if self.windows_opt.activate_windows(self.windows_handle):
                SetGhostBoards().click_all_press_and_release_by_key_code(key_code_list)
            self.sin_out.emit(f"已经执行了 {count_i + 1} 次按钮")
        self.mutex.unlock()
        self.sin_work_status.emit(False)
        return None


class TruckCarTaskQth(QThread):
    """
    押镖
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车
    sin_work_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.truck_count = None
        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle = 0

        self.__team = TeamFunc()  # 创建队伍
        self.__find_npc = FindTaskNPCFunc()  # 查找当地的NPC
        self.__get_task = ReceiveTruckTask()  # 接任务
        self.__transport_task = TransportTaskFunc()  # 开始运镖

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
        self.windows_handle = 0

    def get_param(self, windows_handle: int, truck_count: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.windows_handle = windows_handle
        self.truck_count = truck_count

    def run(self):
        self.mutex.lock()  # 先加锁

        for count_i in range(self.truck_count):
            if self.working is False:
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None

            self.__get_task.reply_person_perspective(self.windows_handle)

            # 创建队伍
            self.__team.create_team(self.windows_handle)
            # 查询地图和NPC
            self.__find_npc.find_truck_task_npc(self.windows_handle)
            # 接取任务
            self.__get_task.receive_task(self.windows_handle)

            if self.__transport_task.transport_truck(self.windows_handle):
                self.sin_out.emit("开始押镖,请注意劫匪NPC刷新")
                self.next_step.emit(1)  # 开始等待劫匪出现
                print("直接押镖成功，发送信号至 等待劫匪出现")
            else:
                self.next_step.emit(1)  # 开始等待劫匪出现
                print("直接押镖失败，发送信号至 等待劫匪出现")
                self.next_step.emit(2)  # 开始查找镖车并开车
                print("直接押镖失败，发送信号至 寻找车辆")

            # 开始尝试押镖
            while 1:
                if self.working is False:
                    # 结束了
                    self.mutex.unlock()  # 解锁
                    self.sin_work_status.emit(False)
                    return None
                if self.__transport_task.check_task_status(self.windows_handle) is False or self.__transport_task.check_task_end(self.windows_handle):
                    self.sin_out.emit("未检测到接镖成功标志，大概已经结束了")
                    self.sin_out.emit(f"本次押镖(第{count_i + 1}轮已经完成)")
                    break
        self.mutex.unlock()  # 解锁
        self.sin_work_status.emit(False)
        return None


class TruckTaskFindCarQth(QThread):
    """
    以下原因出现时 查找镖车并上车
    1、接取任务后 开车 失败
    2、打了怪后，重新上车
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车
    sin_work_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.truck_count = None
        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.mutex = QMutex()
        self.windows_handle = 0
        self.wait = False

        self.__transport_task = TransportTaskFunc()  # 开始运镖

    def __del__(self):
        # 线程状态改为和线程终止
        self.wait = False
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle = 0
        self.wait = False

    def wait_status(self, status: bool):
        """
        是否等待
        """
        self.wait = status

    def get_param(self, windows_handle: int, working: bool):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = working
        self.windows_handle = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁

        # 旋转一周的次数
        round_count: int = 0
        while 1:

            if self.working is False:
                # 结束了
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None

            if round_count == 20:
                # 转了一周之后，还是没找到，就调整一下视角
                self.__transport_task.reply_person_perspective_up(self.windows_handle)
                round_count = 0
            print("TransportTaskFunc 开始进行查询镖车的操作")

            if self.__transport_task.transport_truck(self.windows_handle):
                self.sin_out.emit("开始押镖,请注意劫匪NPC刷新")

            __car_quadrant: int = self.__transport_task.find_car_quadrant(self.windows_handle)
            if __car_quadrant in [0, 3, 4]:
                """
                如果在第三、四象限，那么这不是我想要的
                """
                print(f"镖车在屏幕的第 {__car_quadrant} 象限")
                continue

            __car_pos = self.__transport_task.find_car_pos(self.windows_handle)
            if __car_pos is not None:
                self.sin_out.emit(f"TransportTaskFunc: 找到了 镖车 的坐标({__car_pos[0]},{__car_pos[1]})")
                SetGhostMouse().move_mouse_to(__car_pos[0], __car_pos[1])  # 鼠标移动到初始化位置
                time.sleep(1)

                while 1:
                    if self.working is False:
                        # 结束了
                        self.mutex.unlock()  # 解锁
                        self.sin_work_status.emit(False)
                        return None

                    pos_x, pos_y = SetGhostMouse().get_mouse_x_y()

                    #  先下移50个像素点击一次
                    SetGhostMouse().move_mouse_to(pos_x, pos_y + 50)
                    print("下移50个像素，继续找车")
                    time.sleep(0.2)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(1)

                    __transport_pos = self.__transport_task.find_driver_truck_type(self.windows_handle)
                    if __transport_pos is not None:
                        SetGhostBoards().click_press_and_release_by_code(27)
                        time.sleep(1)
                        SetGhostMouse().click_mouse_right_button()  # 右键主动靠近
                        time.sleep(2)  # 等待2秒，让人物主动靠近
                        if self.__transport_task.transport_truck(self.windows_handle):
                            # 如果 运镖 方式 界面出现，并且还成功运行了.
                            # 那么本次任务就可以结束了
                            print("开始 '驾车'...")
                            self.working = False
                        else:
                            # 如果点了 运镖 但是 没有开车，那么就表示距离太远了，需要靠近
                            SetGhostBoards().click_press_and_release_by_key_name_hold_time("w", 1)  # 往前走一步
                            # 退出循环，从头再来一次
                            break
            else:
                print(f"镖车在屏幕的第 {__car_quadrant} 象限，但是距离中间太近了")
                if __car_quadrant == 1:
                    """
                    如果在第一象限，但是不符合规则；那么就向 左侧 转一下
                    """
                    SetGhostBoards().click_press_and_release_by_code(37)
                else:
                    """
                    如果在第二象限，但是不符合规则；那么就向 右侧 转一下
                    """
                    SetGhostBoards().click_press_and_release_by_code(39)
                print("TransportTaskFunc: 没有找到镖车，旋转一下继续找")
                round_count += 1


class TruckTaskFightMonsterQth(QThread):
    """
    检测并打怪
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车, 3: 打怪中，暂时查找车辆， 4：打怪结束，重新查找车辆
    sin_work_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.mutex = QMutex()
        self.windows_handle = 0
        self.wait = False

        self.__fight_monster = FightMonster()  # 开始运镖

    def __del__(self):
        # 线程状态改为和线程终止
        self.wait = False
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle = 0
        self.wait = False

    def get_param(self, windows_handle: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.windows_handle = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁

        while 1:
            if self.working is False:
                # 结束了
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None
            if self.__fight_monster.check_fight_status(self.windows_handle):
                self.sin_out.emit("出现了劫匪NPC，即将进入战斗")
                self.next_step.emit(3)  # 打怪中，暂时查找车辆
                self.__fight_monster.fight_monster(self.windows_handle)
                self.working = False
                self.next_step.emit(4)  # 打怪结束，继续上车跑路


if __name__ == '__main__':
    time_str = time.strftime("%H_%M", time.localtime(int(time.time())))
    for i in range(10):
        time_strs = time.strftime("%S", time.localtime(int(time.time())))
        print(time_strs)
        time.sleep(1)
