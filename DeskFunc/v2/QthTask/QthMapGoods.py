# coding: utf-8
"""
地图物资采集任务线程。

流程与 v1 一致：
1. 放大小地图；
2. 逐个坐标打开地图、输入 X/Y、点击搜索结果；
3. 每 10 秒检查一次人物坐标，确认是否已经停止移动；
4. 点击采集/全部拾取，并区分“采集成功 / 地形不适合寻路 / 采集结束”。
"""
import time
from datetime import datetime, timedelta

from Core.input.ghost import SetGhostBoards
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.mapGoodsPoint import FindMapGoodsPoint

# 每隔多少秒检查一次人物坐标
_CHECK_INTERVAL = 10


class MapGoodsTask(BaseTaskThread):
    """地图物资采集任务。"""

    def __init__(self):
        super().__init__()
        self._windows_handle = 0
        self._map_goods_point_list: list[str] = []
        self._find_map_goods = FindMapGoodsPoint()
        self._start_time: datetime | None = None
        self._time_out = False

    def get_param(self, windows_handle: int, map_goods_point_list: list[str]):
        """初始化执行参数。"""
        self.working = True
        self._windows_handle = windows_handle
        self._map_goods_point_list = list(map_goods_point_list)
        self._start_time = None
        self._time_out = False

    def check_time_out(self, time_out: int):
        """累计检查时间，达到 time_out 秒后把 _time_out 置为 True。"""
        if self._start_time is None:
            self._start_time = datetime.now()
            self._time_out = False
            return
        if datetime.now() - self._start_time > timedelta(seconds=time_out):
            self._time_out = True
            self._start_time = None

    def check_and_get_goods(self) -> bool:
        """点击小地图后等待采集按钮出现，出现则点击。"""
        self._find_map_goods.click_mini_map(self._windows_handle)
        for _ in range(8):
            if not self.working:
                return False
            if self._find_map_goods.click_ok(self._windows_handle):
                self.sin_out.emit("采集成功.")
                return True
            time.sleep(0.5)
        self.sin_out.emit("没有出现进度条，继续检测")
        return False

    def run(self):
        self.mutex.lock()
        run_count = 0
        try:
            self.sin_run_status.emit(True)
            self.sin_out.emit("3秒后路线开始执行...")
            time.sleep(3)

            self.sin_out.emit("地图初始化...")
            self._find_map_goods.plus_map(self._windows_handle)

            while not self.working:
                return None

            for point in self._map_goods_point_list:
                if not self.working:
                    break

                coordinates = str(point).split(",")
                if len(coordinates) < 2:
                    self.sin_out.emit(f"坐标格式错误: {point}")
                    continue
                point_x, point_y = coordinates[0], coordinates[1]

                self.sin_out.emit(f"开始执行坐标:({point_x},{point_y})的物资采集")
                self._find_map_goods.search_goods_point(
                    point_x, point_y, self._windows_handle,
                    is_running=lambda: self.working,
                )

                while self.working:
                    self.status_bar.emit(run_count)
                    self.check_time_out(_CHECK_INTERVAL)

                    if not self._time_out:
                        time.sleep(1)
                        continue

                    self.sin_out.emit("10秒后确认人物移动状态")
                    if not self._find_map_goods.check_person_move_status(self._windows_handle):
                        # 仍在移动，继续等待
                        continue

                    self.sin_out.emit("检测到人物已停止移动")

                    # 第一次判断：自动寻路是否直接触发了采集
                    time.sleep(0.5)
                    for _ in range(8):
                        if not self.working:
                            break
                        if not self._find_map_goods.find_open_loading(self._windows_handle):
                            continue
                        if not self._find_map_goods.click_ok(self._windows_handle):
                            continue
                        run_count += 1
                        self.status_bar.emit(run_count)
                        self.sin_out.emit("采集成功...")
                        time.sleep(0.5)

                    # 第二次判断：点击小地图再次尝试采集
                    while self.working:
                        if self.check_and_get_goods():
                            run_count += 1
                            self.status_bar.emit(run_count)
                            continue

                        if not self._find_map_goods.check_person_move_status(self._windows_handle):
                            # 仍然在移动，说明这个坐标无法正常寻路
                            SetGhostBoards().click_press_and_release_by_key_name("S")
                            self.sin_out.emit(
                                f"坐标({point_x},{point_y})地形不适合自动寻路,请优化坐标")
                        else:
                            self.sin_out.emit(f"坐标({point_x},{point_y})采集结束,继续执行")
                        break
                    break
        finally:
            self.sin_run_status.emit(False)
            self.sin_out.emit("地图采集已停止...")
            self.mutex.unlock()
        return None
