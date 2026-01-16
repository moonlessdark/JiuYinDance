import time

from PySide6.QtCore import QMutex, QWaitCondition, Signal, QThread

from datetime import datetime, timedelta

from DeskFunc.TaskBussinese.findMapGoodsPoint import FindMapGoodsPointList
from Utils.FindWindowsImage import WindowsHandle
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards


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
                if not self.map_goods_point_working:
                    # 如果已经停止
                    break

                pi: list = point.split(",")  # 获取一下要执行的 x，y坐标
                p_x, p_y = pi[0], pi[1]

                self.sin_out.emit(f"开始执行坐标:({p_x},{p_y})的物资采集")

                self.find_map_goods.search_goods_point(p_x, p_y, self.windows_handle)

                while 1:

                    if not self.map_goods_point_working:
                        break

                    self.status_bar.emit(_run_count)

                    self.check_time_out(_set_time_out)

                    if not self.time_out:
                        # 如果还没有等够10秒，就继续
                        time.sleep(1)
                        continue

                    self.sin_out.emit("10秒后确认人物移动状态")

                    if not self.find_map_goods.check_person_move_status(self.windows_handle):
                        # 任务依旧处于移动中
                        continue

                    self.sin_out.emit(f"检测到人物已停止移动")

                    """
                    首次判断，看看有没有出现进度条或者获取所有的按钮
                    """
                    # 首次判断，一般无效
                    time.sleep(0.5)
                    for xx in range(8):

                        if not self.map_goods_point_working:
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

                        if not self.map_goods_point_working:
                            # 如果已经停止
                            break

                        if self.check_and_get_goods():
                            _run_count += 1
                            self.status_bar.emit(_run_count)
                            continue
                        else:
                            if not self.find_map_goods.check_person_move_status(self.windows_handle):
                                # 任务依旧处于移动中,说明这个点有问题，应该放弃
                                SetGhostBoards().click_press_and_release_by_key_name("S")  # 按一下键盘,停止移动
                                self.sin_out.emit(f"坐标({p_x},{p_y})地形不适合自动寻路,请优化坐标")
                            else:
                                self.sin_out.emit(f"坐标({p_x},{p_y})采集结束,继续执行")
                            break
                    break

        self.wait()  # 等待线程结束
        self.mutex.unlock()  # 解锁
        self.sin_run_status.emit(False)
        self.sin_out.emit("地图采集已停止...")
        return None
