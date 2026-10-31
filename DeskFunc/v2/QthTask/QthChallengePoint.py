# coding: utf-8
"""
挑战点兑换书页任务线程。

纯模板匹配，不含 OCR。流程与 v1 保持一致，每一步失败时输出明确原因并停止。
"""
import random
import time

from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.challengePoint import ChallengePointExchange


class ChallengePointTask(BaseTaskThread):
    """挑战点兑换书页任务。"""

    def __init__(self):
        super().__init__()
        self._hwnd = 0
        self._exchange = ChallengePointExchange()

    def init_task_param(self, hwnd: int):
        """初始化执行参数。"""
        self._hwnd = hwnd
        self.working = True

    @staticmethod
    def _random_sleep():
        time.sleep(round(random.uniform(0.9, 1.5), 2))

    def run(self):
        self.mutex.lock()
        exchange_count = 0
        try:
            self.sin_run_status.emit(True)
            self.sin_out.emit("3秒后执行开始执行...")
            time.sleep(3)

            while self.working:
                self.status_bar.emit(exchange_count)

                check_code = self._exchange.check_pic_template_exist(self._hwnd)
                if check_code != 0:
                    if check_code == -1:
                        if not self._exchange.find_change_point_shop_book(self._hwnd):
                            self.sin_out.emit(
                                f"窗口:{self._hwnd} 未发现'夺魄的书页'，"
                                "请先打开'夺魄'的技能书页页面")
                            self.working = False
                    elif check_code == -2:
                        self.sin_out.emit(
                            f"窗口:{self._hwnd} 未找到兑换窗口,请先点击NPC打开兑换窗口")
                        self.working = False
                    else:
                        self.sin_out.emit(f"窗口:{self._hwnd} 其他错误:{check_code}，程序停止")
                        self.working = False
                    continue

                if not self._exchange.find_change_point_book_page(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到技能书页")
                    self.working = False
                    break

                if not self.working:
                    break
                self.sin_out.emit(f"窗口:{self._hwnd} 已获取技能书页")
                self._random_sleep()

                if not self._exchange.find_change_point_exchange_button(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到技能书页的兑换按钮")
                    self.working = False
                    break
                if not self.working:
                    break
                self._random_sleep()

                if not self._exchange.find_backpack_item_pic(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到背包中的夺魄书页")
                    self.working = False
                    break
                if not self.working:
                    break
                self._random_sleep()

                if not self._exchange.find_recycle_box(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换窗口")
                    self.working = False
                    break
                if not self.working:
                    break
                self._random_sleep()

                if not self._exchange.find_recycle_box_result(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换结果")
                    self.working = False
                    break
                if not self.working:
                    break

                if not self._exchange.find_exchange_ok(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到确认兑换")
                    self.working = False
                    break
                if not self.working:
                    break
                time.sleep(round(random.uniform(0.8, 1.5), 2))

                if not self._exchange.find_exchange_re_ok(self._hwnd):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到二次确认兑换")
                    self.working = False
                    break

                self.sin_out.emit(f"窗口:{self._hwnd} 幸运币兑换成功")
                time.sleep(0.5)
                exchange_count += 1
        finally:
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
