# coding: utf-8
import threading
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.findCars import TeamFunc, FindTaskNPCFunc, ReceiveTruckTask, TransportTaskFunc, UserGoods, \
    FightMonster
from Utils.FindWindowsImage import WindowsHandle
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse, SetGhostBoards

is_not_in_car_sum: int = 0  # 打怪后，是否连续多次状态还没有更新到上车
is_fight_npc_end: bool = False  # 是否已经和NPC战斗，如有没有战斗，就直接上车。 如果已经战斗，那么就需要查询点击镖车再上车
is_fight_npc_visible: bool = False  # 是否出现NPC
is_can_go_car: bool = False  # 打怪是否可以直接上车


# 给全局变量加把锁
mutex = threading.Lock()


class TruckCarTaskQth(QThread):
    """
    本线程负责接镖和检测是否结束
    """
    sin_out = Signal(str)  # 日志打印
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车
    status_bar = Signal(int)  # 执行了几次
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()

        self.truck_count = None
        self.TruckCarTaskQth_working = False
        self.cond = QWaitCondition()

        self.windows_opt = WindowsHandle()

        self.is_close: bool = False

        self.mutex = QMutex()
        self.windows_handle = 0

        self.__team = TeamFunc()  # 创建队伍
        self.__find_npc = FindTaskNPCFunc()  # 查找当地的NPC
        self.__get_task = ReceiveTruckTask()  # 接任务
        self.__transport_task = TransportTaskFunc()  # 开始运镖
        self.__use_goods = UserGoods()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.TruckCarTaskQth_working = False

    def set_close(self):
        self.TruckCarTaskQth_working = False

    def get_param(self, windows_handle: int, truck_count: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.windows_handle = windows_handle
        self.truck_count = truck_count
        self.TruckCarTaskQth_working = True

    def run(self):
        # 声明一下全局变量
        global is_fight_npc_end, is_fight_npc_visible, is_not_in_car_sum, is_can_go_car

        # 修改全局变量，已经发现怪了，停止寻找车辆
        is_fight_npc_end = False
        is_fight_npc_visible = False

        self.sin_run_status.emit(True)

        self.mutex.lock()  # 先加锁
        self.sin_out.emit(f"线程:3秒后开始启动押镖...")
        self.status_bar.emit(0)  # 执行了0次

        time.sleep(3)

        SetGhostMouse().press_mouse_right_button()
        time.sleep(0.5)
        SetGhostMouse().release_mouse_right_button()

        self.__get_task.reply_person_perspective_up(self.windows_handle)  # 初始化视角
        self.sin_out.emit("初始化视角...")

        self.__transport_task.plus_map(self.windows_handle)
        time.sleep(0.5)

        for count_i in range(self.truck_count):

            self.sin_out.emit(f"开始执行第 {count_i + 1} 次押镖")
            # 0: 初始化  1: 完成组队  2: 已经找到接镖NPC,正在前往  3: 已经接取押镖任务  4: 已经驾驶镖车行驶  5: 已经打完怪 6: 已经再次上车
            __task_status: int = 0

            mutex.acquire()
            is_not_in_car_sum = 0
            mutex.release()

            map_name: str = ""

            while 1:

                if not self.TruckCarTaskQth_working:
                    self.next_step.emit(0)
                    self.quit()
                    self.wait()  # 等待线程结束
                    self.mutex.unlock()  # 解锁
                    self.sin_run_status.emit(False)
                    self.sin_out.emit("线程:已停止押镖...")
                    return None

                if map_name == "":
                    map_name: str = self.__team.get_map_and_person(self.windows_handle)

                if __task_status == 0:
                    # 创建队伍
                    if not self.__team.create_team(self.windows_handle):
                        continue

                    SetGhostBoards().click_press_and_release_by_code(27)  # 关闭队伍界面

                    self.sin_out.emit(f"当前地图:{map_name}...")

                    self.sin_out.emit("步骤一:已创建队伍...")

                    # 检测是否使用了御风
                    self.__use_goods.use_yu_feng_shen_shui(self.windows_handle)
                    __task_status = 1
                    self.sin_out.emit("步骤一:检测是否使用御风神水...")

                elif __task_status == 1:

                    # 队伍已经创建，开始寻找接镖NPC
                    if not self.__find_npc.find_truck_task_npc(self.windows_handle, map_name):
                        continue
                    __task_status = 10
                    self.sin_out.emit("步骤二:寻找押镖NPC,寻路中...")

                elif __task_status == 2:

                    # 正在跑路中，等待进入接取任务界面
                    if not self.__get_task.receive_task(self.windows_handle, map_name):
                        continue
                    __task_status = 3
                    self.sin_out.emit("步骤三:已接镖,开始上车驾驶...")
                    time.sleep(1)

                elif __task_status == 3:

                    # 已经接取了任务，寻找一下镖车,驾车上路
                    if is_fight_npc_visible:
                        # 出怪了，这里等一下啊,等打完怪再说
                        time.sleep(1)
                        continue

                    if is_not_in_car_sum == 10:
                        # 如果连续10次没有成功上车，调整一下视角，由于目前是平视，所以先仰视
                        self.__get_task.reply_person_perspective_up(self.windows_handle)
                    elif is_not_in_car_sum == 20:
                        # 20次没有上车成功，再调整一下视角
                        self.__get_task.reply_person_perspective(self.windows_handle)
                    elif is_not_in_car_sum == 30:
                        # 没救了，放弃了，退组重新接镖吧
                        if not self.__team.close_team(self.windows_handle):
                            continue
                        self.next_step.emit(0)  # 全部结束
                        self.sin_out.emit(f"尝试 {is_not_in_car_sum + 1} 次没有成功上车，队伍解散重组")
                        __task_status = 0
                        continue

                    # 已经接取了任务，寻找一下镖车,驾车上路
                    if not self.__transport_task.driver_truck_car(self.windows_handle, map_name=map_name):
                        # 失败次数+1
                        mutex.acquire()
                        is_not_in_car_sum += 1
                        mutex.release()
                        continue

                    self.sin_out.emit("步骤四:驾驶镖车,运输中...")

                    self.__get_task.reply_person_perspective_up(self.windows_handle)  # 初始化视角

                    __task_status = 4

                    # self.__get_task.reply_person_perspective_up(self.windows_handle)

                    self.next_step.emit(1)  # 等待劫镖NPC出现

                    mutex.acquire()
                    is_not_in_car_sum = 0
                    mutex.release()

                elif __task_status == 4:
                    # 首次上车成功，开始等怪出现
                    if is_fight_npc_end:
                        __task_status = 5
                        self.sin_out.emit("步骤五:打怪结束...")

                elif __task_status == 5:

                    # 打怪结束，先检查一下是不是输出太低，镖车已经木有了
                    if not self.__transport_task.check_task_status(self.windows_handle):
                        __task_status = 0
                        continue

                    # 打完怪,再次上车
                    if is_not_in_car_sum == 5:
                        # 如果连续10次没有成功上车，调整一下视角
                        self.__get_task.reply_person_perspective(self.windows_handle)
                    elif is_not_in_car_sum == 10:
                        # 20次没有上车成功，再调整一下视角
                        self.__get_task.reply_person_perspective_up(self.windows_handle)
                    elif is_not_in_car_sum == 15:
                        # 没救了，放弃了，退组重新接镖吧
                        if not self.__team.close_team(self.windows_handle):
                            continue
                        self.next_step.emit(0)  # 全部结束
                        self.sin_out.emit(f"尝试 {is_not_in_car_sum + 1} 次没有成功上车，队伍解散重组,5秒后重新接镖")
                        __task_status = 0
                        time.sleep(5)
                        continue

                    if is_can_go_car:

                        if not self.__transport_task.transport_truck(self.windows_handle):
                            # 失败次数+1
                            mutex.acquire()
                            is_not_in_car_sum += 1
                            mutex.release()
                            continue

                    # 打完怪了，开始继续找镖车
                    else:
                        if not self.__transport_task.driver_truck_car_v2(self.windows_handle, car_area_type=1):

                            self.sin_out.emit(f"上车失败(次数:{is_not_in_car_sum + 1}),往前走1步")
                            SetGhostBoards().click_press_and_release_by_key_name_hold_time("w", 0.1)  # 往前走一步

                            # 失败次数+1
                            mutex.acquire()
                            is_not_in_car_sum += 1
                            mutex.release()
                            time.sleep(0.5)
                            continue
                    __task_status = 6
                    self.sin_out.emit("步骤六:重新驾车,等待结束...")

                elif __task_status == 6:
                    # 打怪结束，上车成功，等待任务结束
                    if self.__transport_task.check_task_status(self.windows_handle):
                        time.sleep(0.5)
                        continue
                    else:
                        if self.__transport_task.check_task_end(self.windows_handle):
                            self.sin_out.emit(f"本次押镖(第{count_i + 1}轮已经完成)")
                            self.status_bar.emit(count_i + 1)
                        else:
                            self.sin_out.emit("押镖未完成，超时或者镖车被毁")
                    mutex.acquire()
                    # 参数初始化我
                    is_not_in_car_sum = 0  # 已经连续多少次没有找到镖车
                    is_fight_npc_end = False  # 是否已经和NPC战斗，如有没有战斗，就直接上车。 如果已经战斗，那么就需要查询点击镖车再上车
                    is_fight_npc_visible = False  # 是否出现NPC
                    is_can_go_car = False
                    mutex.release()
                    break

                elif __task_status == 10:
                    # 尝试接取每日任务
                    find_task_code: int = self.__get_task.day_task(self.windows_handle)
                    if find_task_code == 0:
                        __task_status = 2  # 不需要接每日任务
                    elif find_task_code == 1:
                        self.sin_out.emit("接取每日押镖任务,开始押镖")
                        __task_status = 1  # 接完每日任务了，继续押镖


        self.mutex.unlock()  # 解锁
        self.sin_run_status.emit(False)
        self.next_step.emit(0)  # 全部结束
        return None


class TruckTaskFightMonsterQth(QThread):
    """
    检测并打怪。
    打怪之前先尝试点击一下镖车(屏幕中心点)，打完怪后就可以直接上车
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车, 3: 打怪中，暂时查找车辆， 4：打怪结束，重新查找车辆

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.mutex = QMutex()
        self.windows_handle = 0
        self.__transport_task = TransportTaskFunc()  # 开始运镖

        self.__fight_monster = FightMonster()

    def __del__(self):
        # 线程状态改为和线程终止
        self.working = False

    def get_param(self, windows_handle: int, working_status: bool = True):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = working_status
        self.windows_handle = windows_handle

    def run(self):
        self.sin_out.emit("线程:开始查找/检测劫匪NPC")
        self.mutex.lock()  # 先加锁
        while 1:
            if self.working is False:
                # 结束了
                self.quit()
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                self.sin_out.emit("线程:已经停止查找/检测劫匪NPC")
                return None
            if self.__fight_monster.check_fight_status(self.windows_handle):
                # 声明一下全局变量
                global is_fight_npc_end, is_fight_npc_visible, is_can_go_car
                # 修改全局变量，已经发现怪了，停止寻找车辆
                mutex.acquire()
                is_fight_npc_end = False
                is_fight_npc_visible = True
                mutex.release()
                self.sin_out.emit("劫镖NPC出现...")

                # 开始战斗
                if self.__fight_monster.fight_monster(self.windows_handle) is True:
                    self.working = False

                    self.sin_out.emit("劫镖NPC已消失(击杀)...")
                    # 修改一下全局变量，已经和NPC战斗过了
                    mutex.acquire()
                    is_fight_npc_end = True
                    is_fight_npc_visible = False
                    mutex.release()
                    # 修改全局变量，战斗结束，继续寻找车辆
                    if self.__transport_task.click_truck_car_in_display_center(self.windows_handle) is True:
                        mutex.acquire()
                        is_can_go_car = True
                        mutex.release()
                        self.sin_out.emit("可直接上车")
                        time.sleep(1)
