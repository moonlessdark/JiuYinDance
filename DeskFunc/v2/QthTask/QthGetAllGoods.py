# coding: utf-8
"""
清理禁地包裹任务线程。

多窗口轮询：
1. 优先点击“全部拾取”；
2. 打开禁地物品包打开后产生的材料包；
3. 右键打开禁地物品包本身。
"""
import time

from Core.input.ghost import SetGhostMouse
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.commonOperations import CommonOperations
from DeskFunc.v2.TaskBussinese.hiddenRealmItem import HiddenRealmItems


class GetAllGoodsTask(BaseTaskThread):
    """清理禁地包裹任务。"""

    def __init__(self):
        super().__init__()
        self._windows_handle_list: list[int] = []
        self._common = CommonOperations()
        self._hidden_realm = HiddenRealmItems()

    def get_param(self, windows_handle_list: list[int]):
        """初始化执行参数。"""
        self.working = True
        self._windows_handle_list = list(windows_handle_list)

    @staticmethod
    def move_mouse(hwnd: int):
        """移动一下鼠标，避免挡住背包中的包裹图标。"""
        mouse_x, mouse_y = SetGhostMouse().get_mouse_x_y()
        SetGhostMouse().move_mouse_to(mouse_x - 10, mouse_y - 10)
        time.sleep(0.5)

    def run(self):
        self.mutex.lock()
        count = 0
        try:
            self.sin_run_status.emit(True)

            while self.working:
                for hwnd in self._windows_handle_list:
                    if not self.working:
                        break

                    time.sleep(1)
                    if self._common.find_get_all_button(hwnd):
                        count += 1
                        self.move_mouse(hwnd)
                        time.sleep(1)

                    self.status_bar.emit(count)

                    if self._hidden_realm.find_cailiao_item_backpack(hwnd):
                        time.sleep(2)
                        self.move_mouse(hwnd)
                        continue

                    time.sleep(1)

                    if self._hidden_realm.find_red_item_backpack(hwnd):
                        self.move_mouse(hwnd)
                        time.sleep(2)
                        continue
        finally:
            self.sin_out.emit("自动获取结束")
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
