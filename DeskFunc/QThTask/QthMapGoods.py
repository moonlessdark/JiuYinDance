import time

from PySide6.QtCore import QMutex, QWaitCondition, Signal, QThread

from datetime import datetime, timedelta

from DeskFunc.TaskBussinese.findMapGoodsPoint import FindMapGoodsPointList
from Utils.FindWindowsImage import WindowsCapture, WindowsHandle, PicCapture
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse


class MapGoodsQth(QThread):
    """
    本线程负责接镖和检测是否结束
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)  # 底部状态栏日志

    def __init__(self):
        super().__init__()

        self.map_goods_point_list = None
        self.map_goods_point_working = False
        self.cond = QWaitCondition()

        self.windows_opt = WindowsHandle()

        self.is_close: bool = False

        self.mutex = QMutex()
        self.windows_handle = 0

        self.find_map_goods = FindMapGoodsPointList()

        self.time_out: bool = False

        self.start_time = None

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.map_goods_point_working = False

    def stop_execute_init(self):
        self.map_goods_point_working = False

    def get_param(self, windows_handle: int, map_goods_point_list: list):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.time_out: bool = False
        self.map_goods_point_working = True
        self.windows_handle = windows_handle
        self.map_goods_point_list = map_goods_point_list

    def check_time_out(self, time_out: int):
        """
        监测超时时间
        """
        if self.start_time is None:
            self.start_time = datetime.now()
            self.time_out = False
        else:
            end_time = datetime.now()

            difference = end_time - self.start_time
            if difference > timedelta(seconds=time_out):
                self.time_out = True
                self.start_time = None

    def check_and_get_goods(self):
        """
        点击右上角看看有没有出现进度条
        """
        # 点击一下小地图，看看能不能触发一下
        self.find_map_goods.click_mini_map(self.windows_handle)
        for xx in range(8):
            if self.find_map_goods.click_ok(self.windows_handle) is True:
                # 等待确定按钮出现
                self.sin_out.emit("采集成功.")
                return True
            time.sleep(0.5)
        self.sin_out.emit("没有出现进度条，继续检测")
        return False

    def run(self):
        self.mutex.lock()

        _set_time_out: int = 10  # 设置检查超时时间为 10秒，即每隔10秒去检查一次人物坐标
        _run_count: int = 0  # 采集了多少次了

        self.sin_run_status.emit(True)
        self.sin_out.emit(f"3秒后路线开始执行...")
        time.sleep(3)

        self.sin_out.emit("地图初始化...")
        # 先把地图缩放拉大
        self.find_map_goods.plus_map(self.windows_handle)

        while self.map_goods_point_working:
            for point in self.map_goods_point_list:
                if self.map_goods_point_working is False:
                    # 如果已经停止
                    break

                pi: list = point.split(",")  # 获取一下要执行的 x，y坐标
                p_x, p_y = pi[0], pi[1]

                self.sin_out.emit(f"开始执行坐标:({p_x},{p_y})的物资采集")

                self.find_map_goods.search_goods_point(p_x, p_y, self.windows_handle)

                while 1:

                    if self.map_goods_point_working is False:
                        break

                    self.status_bar.emit(_run_count)

                    self.check_time_out(_set_time_out)

                    if self.time_out is False:
                        # 如果还没有等够10秒，就继续
                        time.sleep(1)
                        continue

                    self.sin_out.emit("10秒后确认人物移动状态")

                    if self.find_map_goods.check_person_move_status(self.windows_handle) is False:
                        # 任务依旧处于移动中
                        continue

                    self.sin_out.emit(f"检测到人物已停止移动")

                    """
                    首次判断，看看有没有出现进度条或者获取所有的按钮
                    """
                    # 首次判断，一般无效
                    time.sleep(0.5)
                    for xx in range(8):

                        if self.map_goods_point_working is False:
                            # 如果已经停止
                            break

                        # 开卡自动寻路能不能直接挖到/砍树
                        if self.find_map_goods.find_open_loading(self.windows_handle) is False:
                            continue
                        if self.find_map_goods.click_ok(self.windows_handle) is False:
                            # 等待确定按钮出现
                            continue
                        else:
                            _run_count += 1
                            self.status_bar.emit(_run_count)
                            self.sin_out.emit(f"采集成功...")
                        time.sleep(0.5)

                    """
                    二次判断
                    """
                    while 1:

                        if self.map_goods_point_working is False:
                            # 如果已经停止
                            break

                        if self.check_and_get_goods() is True:
                            _run_count += 1
                            self.status_bar.emit(_run_count)
                            continue
                        else:
                            if self.find_map_goods.check_person_move_status(self.windows_handle) is False:
                                # 任务依旧处于移动中,说明这个点有问题，应该放弃
                                SetGhostBoards().click_press_and_release_by_key_name("S")  # 按一下键盘,停止移动
                                self.sin_out.emit(f"坐标({p_x},{p_y})地形不适合自动寻路,请优化坐标")
                            else:
                                self.sin_out.emit(f"坐标({p_x},{p_y})采集结束,继续执行")
                            break
                    break

                #
                #
                # if self.time_out:
                #
                #     # 60秒了，检测一次坐标看看是不是停止运行了
                #     # print("已经超时，检测是否有资源")
                #     if self.find_map_goods.check_person_move_status(self.windows_handle) is True:
                #         self.sin_out.emit(f"检测到人物已停止移动")
                #         # 人物停止移动了，但是没有出现进度条
                #         if self.find_map_goods.find_open_loading(self.windows_handle) is False:
                #             # 点击一下小地图，尝试一下看看能不能出
                #             self.sin_out.emit(f"点击小地图,自动采集...")
                #             if self.check_and_get_goods() is False:
                #                 self.sin_out.emit(f"未检测到采集进度条,可能没有物资了或者旁边有NPC干扰")
                #                 # 如果没有监测到进度条，那就继续下一个坐标，结束本次循环
                #                 break
                #             else:
                #                 # 出现了进度条，交给下一个方法执行
                #                 self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下
                #         else:
                #             # 出现了进度条，交给下面的方法执行吧，这里不做任何处理，只能说运气十分不好卡在最后一秒出现了进度条
                #             self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下
                #     self.sin_out.emit("人物移动中...")
                # if self.find_map_goods.find_open_loading(self.windows_handle):
                #     # 如果出现了进度条，说明自动采集中，一般砍树会触发此判断
                #     while 1:
                #
                #         if self.map_goods_point_working is False:
                #             break
                #
                #         if self.find_map_goods.click_ok(self.windows_handle) is False:
                #             continue
                #         else:
                #             if self.check_and_get_goods() is False:
                #                 self.sin_out.emit(f"未检测到采集进度条,可能没有物资了或者旁边有NPC干扰")
                #                 break
                #             else:
                #                 self.sin_out.emit(f"坐标:({p_x},{p_y})物资已采集")
                #     _run_count += 1
                #
                #     self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下
                #     break

        self.wait()  # 等待线程结束
        self.mutex.unlock()  # 解锁
        self.sin_run_status.emit(False)
        self.sin_out.emit("地图采集已停止...")
        return None
