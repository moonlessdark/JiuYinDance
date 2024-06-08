# coding: utf-8

import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskPageV2.DeskFindPic.findCars import TeamFunc, FindTaskNPCFunc, ReceiveTruckTask, TransportTaskFunc, FightMonster
from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList

is_stop_find_car: bool = False  # 是否停止寻找镖车
is_need_walk: bool = True  # 是否需要走2步前往镖车
is_fight_npc_end: bool = False  # 是否已经和NPC战斗，如有没有战斗，就直接上车。 如果已经战斗，那么就需要查询点击镖车再上车
is_fight_npc_visible: bool = False  # 是否出现NPC
person_viewpoint: int = 0  # 0，默认，无， 1：平视， 2：俯视


class TruckCarTaskQth(QThread):
    """
    本线程负责接镖和检测是否结束
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车
    sin_work_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.truck_count = None
        self.TruckCarTaskQth_working = False
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

        self.is_close: bool = False

        self.mutex = QMutex()
        self.windows_handle = 0

        self.__team = TeamFunc()  # 创建队伍
        self.__find_npc = FindTaskNPCFunc()  # 查找当地的NPC
        self.__get_task = ReceiveTruckTask()  # 接任务
        self.__transport_task = TransportTaskFunc()  # 开始运镖

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

    def run(self):

        self.TruckCarTaskQth_working = True
        self.mutex.lock()  # 先加锁
        self.sin_out.emit(f"5秒后开始启动")
        time.sleep(5)
        for count_i in range(self.truck_count):
            self.sin_out.emit(f"开始执行第：{count_i+1} 次押镖")
            if self.TruckCarTaskQth_working is False:
                # 结束了
                self.quit()
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                return None

            __city_name: str = self.__team.get_map_and_person(self.windows_handle)
            self.__get_task.reply_person_perspective(self.windows_handle)
            # 创建队伍
            self.__team.create_team(self.windows_handle)
            # 查询地图和NPC
            self.__find_npc.find_truck_task_npc(self.windows_handle)
            # 接取任务
            self.__get_task.receive_task(self.windows_handle)

            global person_viewpoint
            person_viewpoint = 1

            # 声明一下全局变量
            global is_stop_find_car, is_fight_npc_end, is_need_walk, is_fight_npc_visible
            # 修改全局变量，已经发现怪了，停止寻找车辆
            is_stop_find_car = False
            is_fight_npc_end = False
            is_need_walk = True  # 需要根据实际情况修改
            is_fight_npc_visible = False
            if __city_name in ["苏州", "成都"]:
                # 如果是成都和苏州，就不需要走了，直接上车就行了
                is_need_walk = False

            pos = coordinate_change_from_windows(self.windows_handle, (100, 100))
            SetGhostMouse().move_mouse_to(pos[0], pos[1])

            self.sin_out.emit(f"开始执行发送信号了")

            # 发送信号，等待劫匪出现
            self.next_step.emit(1)
            # 发送信号，等待劫匪出现
            self.next_step.emit(2)
            self.next_step.emit(4)

            while 1:

                if self.TruckCarTaskQth_working is False:
                    self.quit()
                    self.wait()  # 等待线程结束
                    self.mutex.unlock()  # 解锁
                    self.sin_work_status.emit(False)
                    return None

                if self.__transport_task.check_task_status(self.windows_handle) is False:
                    if self.__transport_task.check_task_end(self.windows_handle):
                        self.sin_out.emit(f"本次押镖(第{count_i + 1}轮已经完成)")
                    else:
                        self.sin_out.emit("押镖未完成，超时或者镖车被毁")
                    self.next_step.emit(0)  # 全部结束
                    break
        self.mutex.unlock()  # 解锁
        self.sin_work_status.emit(False)
        self.next_step.emit(0)  # 全部结束
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
        self.working = True
        self.mutex = QMutex()
        self.windows_handle = 0

        self.__transport_task = TransportTaskFunc()  # 开始运镖

    def __del__(self):
        # 线程状态改为和线程终止
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle = 0

    def get_param(self, windows_handle: int, working: bool):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = working
        self.windows_handle = windows_handle

    def run(self):
        global person_viewpoint
        self.mutex.lock()  # 先加锁
        while 1:
            if self.working is False:
                # 结束了
                self.quit()
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                return None

            if is_stop_find_car or is_fight_npc_visible:
                # 如果停止查找
                time.sleep(2)
                continue

            if is_need_walk is False:
                # 如果不需要走2步，那么就是苏州和成都了，其他的都要走2步，直接上车就行
                if self.__transport_task.transport_truck(self.windows_handle):
                    # 如果出现了“驾车”的按钮，尝试点击 “驾车”
                    self.sin_out.emit("开始押镖")
                    # 鼠标离镖车远一点
                    pos = coordinate_change_from_windows(self.windows_handle, (100, 100))
                    SetGhostMouse().move_mouse_to(pos[0], pos[1])
                    self.__transport_task.reply_person_perspective_up(self.windows_handle)  # 成功上车，拉远一下视角
                    person_viewpoint = 2
                    # 成功开车
                    self.working = False

            if is_fight_npc_end is False:

                """
                如果此时是接任务后的第一次寻找镖车,还没有打怪
                当前为调试代码，
                燕京场景，接镖后人物距离镖车会较远，需要走2步。成都，苏州较近，可以直接上车，is_need_walk 请设置为False
                """
                __car = self.__transport_task.find_truck_car_center_pos(hwnd=self.windows_handle, find_count=1,
                                                                        is_break=is_stop_find_car)
                if __car is None:
                    time.sleep(1)
                    continue
                if is_need_walk:
                    # 如果发现镖车在 画面中间的位置附近，就往前走2秒，靠近镖车
                    SetGhostMouse().release_all_mouse_button()
                    SetGhostBoards().click_press_and_release_by_key_name_hold_time("w", 2)
                if self.__transport_task.transport_truck(self.windows_handle):
                    # 如果出现了“驾车”的按钮，尝试点击 “驾车”
                    self.sin_out.emit("开始押镖")
                    # 鼠标离镖车远一点
                    pos = coordinate_change_from_windows(self.windows_handle, (100, 100))
                    SetGhostMouse().move_mouse_to(pos[0], pos[1])
                    self.__transport_task.reply_person_perspective_up(self.windows_handle)  # 成功上车，拉远一下视角

                    person_viewpoint = 2
                    # 成功开车
                    self.working = False
            else:
                """
                如果已经和NPC战斗过，那么就需要慢慢的找镖车了
                """
                if self.__transport_task.transport_truck(self.windows_handle):
                    self.sin_out.emit("已经找到镖车，开始押镖...")
                    self.working = False
                    break

                __car_pos = self.__transport_task.find_car_center_pos_in_display(self.windows_handle)
                if __car_pos is not None:
                    # self.sin_out.emit(f"TransportTaskFunc: 找到了 镖车 的坐标({__car_pos[0]},{__car_pos[1]})")
                    SetGhostMouse().move_mouse_to(__car_pos[0], __car_pos[1])  # 鼠标移动到初始化位置
                    time.sleep(0.5)
                    while 1:

                        if is_stop_find_car or is_fight_npc_visible:
                            time.sleep(1)
                            continue

                        pos = SetGhostMouse().get_mouse_x_y()

                        #  先下移50个像素点击一次
                        SetGhostMouse().move_mouse_to(pos[0], pos[1] + 50)
                        time.sleep(0.2)
                        SetGhostMouse().click_mouse_left_button()
                        time.sleep(1)

                        __transport_pos = self.__transport_task.find_driver_truck_type(self.windows_handle)
                        if __transport_pos is not None:

                            if is_stop_find_car or is_fight_npc_visible:
                                time.sleep(1)
                                continue

                            SetGhostBoards().click_press_and_release_by_code(27)
                            time.sleep(1)
                            SetGhostMouse().click_mouse_right_button()  # 右键主动靠近
                            time.sleep(2)  # 等待2秒，让人物主动靠近
                            if self.__transport_task.transport_truck(self.windows_handle):
                                # 如果 运镖 方式 界面出现，并且还成功运行了.
                                # 那么本次任务就可以结束了
                                self.__transport_task.reply_person_perspective_up(self.windows_handle)  # 成功上车，拉远一下视角
                                person_viewpoint = 2
                                self.working = False

                                pos = coordinate_change_from_windows(self.windows_handle, (100, 100))
                                SetGhostMouse().move_mouse_to(pos[0], pos[1])

                                break
                            else:
                                SetGhostMouse().release_all_mouse_button()
                                # 如果点了 运镖 但是 没有开车，那么就表示距离太远了，需要靠近
                                SetGhostBoards().click_press_and_release_by_key_name_hold_time("w", 1)  # 往前走一步
                                # 退出循环，从头再来一次
                                break


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

        self.mutex.lock()  # 先加锁

        while 1:
            if self.working is False:
                # 结束了
                self.quit()
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                return None
            if self.__fight_monster.check_fight_status(self.windows_handle):
                # 声明一下全局变量
                global is_stop_find_car, is_fight_npc_end, is_fight_npc_visible
                # 修改全局变量，已经发现怪了，停止寻找车辆
                is_stop_find_car = True
                is_fight_npc_end = False
                is_fight_npc_visible = True

                self.next_step.emit(3)  # 打怪中，暂时查找车辆

                # 开始战斗
                self.__fight_monster.fight_monster(self.windows_handle)
                self.working = False

                # 修改一下全局变量，已经和NPC战斗过了
                is_stop_find_car = False
                is_fight_npc_end = True
                is_fight_npc_visible = False
                # 修改全局变量，战斗结束，继续寻找车辆
                self.next_step.emit(2)  # 打怪结束，继续上车跑路
                self.next_step.emit(4)  # 打怪结束，继续保持车辆在屏幕上


class FollowTheTrailOfTruckQth(QThread):
    """
    保持镖车在屏幕中间的附近
    """

    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车, 3: 打怪中，暂时查找车辆， 4：打怪结束，重新查找车辆

    def __init__(self):
        super().__init__()

        self.is_wait = False
        self.working = True
        self.cond = QWaitCondition()

        self.mutex = QMutex()
        self.windows_handle = 0

        self.__transport_task = TransportTaskFunc()  # 查找镖车

    def __del__(self):
        # 线程状态改为和线程终止
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False
        self.windows_handle = 0

    def set_wait_status(self, is_wait: bool):
        self.is_wait = is_wait

    def get_param(self, windows_handle: int, working_status: bool):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = working_status
        self.windows_handle = windows_handle

    def run(self):
        self.mutex.lock()  # 先加锁
        follow_car_quadrant: int = 0  # 追踪车辆在第几象限，用于车辆离开了屏幕后可以尝试去找回来
        while 1:
            if self.working is False:
                # 结束了
                self.quit()
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                return None

            if is_stop_find_car or is_fight_npc_visible:
                time.sleep(1)
                continue

            __car_pos = self.__transport_task.find_truck_car_center_pos(self.windows_handle, 1,
                                                                        is_break=is_stop_find_car)
            if __car_pos is not None:
                self.sin_out.emit("正在持续追踪镖车...")
                # 存储一下镖车在屏幕哪个位置
                follow_cap = WindowsCapture().capture(self.windows_handle)
                follow_car_quadrant = self.__transport_task.check_target_pos_direction(follow_cap, __car_pos)
                time.sleep(5)
            else:
                """
                这里主要是处理被怪击飞后，镖车的视角丢失的问题
                此时视角如果是俯视的，
                """
                if person_viewpoint == 1:
                    # 如果当前角色视角是平视的话，那么就说明是在查找镖车的时候。
                    continue

                if follow_car_quadrant == 0:
                    # 如果镖车本身就就没有出现在屏幕上，那么就继续就好了
                    continue
                elif follow_car_quadrant == 1:
                    print(f"当前镖车在第一象限，按a转向")
                    # 如果镖车在画面中消失前，是在第1象限，那么就往这个方向走一下
                    SetGhostBoards().click_press_by_key_name("w")
                    SetGhostBoards().click_press_by_key_name("a")
                    time.sleep(0.5)
                    SetGhostBoards().release_all_key()
                elif follow_car_quadrant == 2:
                    print(f"当前镖车在第二象限，按d转向")

                    # 第二象限，右上角
                    SetGhostBoards().click_press_by_key_name("w")
                    SetGhostBoards().click_press_by_key_name("d")
                    time.sleep(0.5)
                    SetGhostBoards().release_all_key()
                elif follow_car_quadrant == 3:
                    print(f"当前镖车在第3象限，按a转向")

                    # 第三象限，左下角
                    SetGhostBoards().click_press_by_key_name("s")
                    SetGhostBoards().click_press_by_key_name("a")
                    time.sleep(0.5)
                    SetGhostBoards().release_all_key()
                elif follow_car_quadrant == 4:
                    print(f"当前镖车在第一象限，按d转向")

                    # 第四象限，右下角
                    SetGhostBoards().click_press_by_key_name("s")
                    SetGhostBoards().click_press_by_key_name("d")
                    time.sleep(0.5)
                    SetGhostBoards().release_all_key()
