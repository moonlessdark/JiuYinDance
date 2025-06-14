import time

from PySide6 import QtCore
from PySide6.QtCore import QMutex, QWaitCondition, Signal, QThread

from DeskPageV2.DeskTools.WindowsSoft.get_windows import GetHandleList
from DeskPageV2.DeskFindPic.findMapGoodsPoint import FindMapGoodsPointList
from datetime import datetime, timedelta


class MapGoodsQth(QThread):
    """
    本线程负责接镖和检测是否结束
    """
    sin_out = Signal(str)
    next_step = Signal(int)  # 下一步: 1 是扫描打怪。 2 是重新查找 镖车并开车
    sin_work_status = Signal(bool)
    sin_status_bar_out = Signal(str, int)  # 底部状态栏日志

    def __init__(self):
        super().__init__()

        self.map_goods_point_list = None
        self.map_goods_point_working = False
        self.cond = QWaitCondition()

        self.windows_opt = GetHandleList()

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
        for xx in range(5):
            if self.find_map_goods.find_open_loading(self.windows_handle):
                # 如果出现了loading界面，说明这个地方有物资，正在挖掘
                return True
            # 有可能还得跑2步路，3秒内吧，没有出现就拉到，说明被地形卡住了或者没有物资了
            time.sleep(1)
        return False

    def run(self):
        self.mutex.lock()

        # 先把地图缩放拉大
        self.find_map_goods.plus_map(self.windows_handle)

        for point in self.map_goods_point_list:
            if self.map_goods_point_working is False:
                self.wait()  # 等待线程结束
                self.mutex.unlock()  # 解锁
                self.sin_work_status.emit(False)
                self.sin_out.emit("地图采集已停止...")
                return None

            pi: list = point.split(",")
            p_x, p_y = pi[0], pi[1]

            print(f"开始执行坐标: {p_x} + {p_y}")

            self.find_map_goods.search_goods_point(p_x, p_y, self.windows_handle)

            while 1:
                self.check_time_out(20)
                if self.time_out:
                    # 60秒了，检测一次坐标看看是不是停止运行了
                    print("已经超时，检测是否有资源")
                    if self.find_map_goods.check_person_move_status(self.windows_handle) is True:
                        # 人物停止移动了，但是没有出现进度条
                        if self.find_map_goods.find_open_loading(self.windows_handle) is False:
                            # 点击一下小地图，尝试一下看看能不能出
                            if self.check_and_get_goods() is False:
                                # 如果没有监测到进度条，那就继续下一个坐标，结束本次循环
                                break
                            else:
                                # 出现了进度条，交给下一个方法执行
                                self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下
                        else:
                            # 出现了进度条，交给下面的方法执行吧，这里不做任何处理，只能说运气十分不好卡在最后一秒出现了进度条
                            self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下

                if self.find_map_goods.find_open_loading(self.windows_handle):
                    # 如果出现了进度条，说明自动采集中，一般砍树会触发此判断
                    while 1:
                        if self.find_map_goods.click_ok(self.windows_handle) is False:
                            continue
                        else:
                            if self.check_and_get_goods() is False:
                                break
                    self.start_time = None  # 这个坐标扫描结束了，超时时间重置一下
                    break

        self.wait()  # 等待线程结束
        self.mutex.unlock()  # 解锁
        self.sin_work_status.emit(False)
        self.sin_out.emit("地图采集已停止...")
        return None
