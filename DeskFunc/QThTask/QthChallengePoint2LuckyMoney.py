import random
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.findChallengePoint2LuckyMoney import ChangePoint2LuckyMoney
from Utils.FindWindowsImage import WindowsCapture, WindowsHandle

class ChallengePoint2LuckyMoney(QThread):

    sin_out = Signal(str)  # 日志打印
    status_bar = Signal(int)  # 底部状态栏打印,执行了多少次
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()

        self._hwnd: int = 0

        self.windows_cap = WindowsCapture()  # 截图
        self.windows_opt = WindowsHandle()  # 激活窗口
        self.dance_type = None

        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.func = ChangePoint2LuckyMoney()

    def __del__(self):
        self.working = False

    def stop_stak(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def init_task_param(self, hwnd):
        """
        初始化执行参数
        :param hwnd: 需要检测的窗口句柄
        :return:
        """
        self._hwnd = hwnd
        self.working = True

    def run(self):
        self.mutex.lock()  # 先加锁

        exchange_count: int = 0  # 已经兑换了多少次
        self.sin_run_status.emit(True)  # 发送消息，任务开始执行了

        self.sin_out.emit("3秒后执行开始执行...")
        time.sleep(3)

        while 1:

            if not self.working:
                break

            self.status_bar.emit(exchange_count)

            # 第一步，检查我需要的某些元素在不在
            check_code: int = self.func.check_pic_template_exist(self._hwnd)
            if check_code != 0:

                if check_code == -1:

                    if not self.func.find_change_point_shop_book(self._hwnd):
                        self.sin_out.emit(f"窗口:{self._hwnd} 未发现'夺魄的书页'，请先打开'夺魄'的技能书页页面")
                        self.working = False
                elif check_code == -2:
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换窗口,请先点击NPC打开兑换窗口")
                    self.working = False
                else:
                    self.sin_out.emit(f"窗口:{self._hwnd} 其他错误:{check_code}，程序停止")
                    self.working = False
                continue

            # 第二步 获取技能书页
            if not self.func.find_change_point_book_page(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到技能书页")
                self.working = False
                break

            if not self.working:
                break

            self.sin_out.emit(f"窗口:{self._hwnd} 已获取技能书页")
            time.sleep(round(random.uniform(0.9, 1.5), 2))

            # 第三步 获取技能书页的兑换按钮
            if not self.func.find_change_point_exchange_button(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到技能书页的兑换按钮")
                self.working = False
                break

            if not self.working:
                break

            time.sleep(round(random.uniform(0.9, 1.5), 2))

            # 第四步 获取背包中的夺魄书页
            if not self.func.find_backpack_item_pic(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到背包中的夺魄书页")
                self.working = False
                break

            if not self.working:
                break

            time.sleep(round(random.uniform(0.9, 1.5), 2))

            # 第五步 找到兑换窗口
            if not self.func.find_recycle_box(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换窗口")
                self.working = False
                break

            if not self.working:
                break
            time.sleep(round(random.uniform(0.9, 1.5), 2))

            # 第六步 找到兑换结果
            if not self.func.find_recycle_box_result(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换结果")
                self.working = False
                break

            if not self.working:
                break

            # 第七步 确认兑换
            if not self.func.find_exchange_ok(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到确认兑换")
                self.working = False
                break

            if not self.working:
                break
            time.sleep(round(random.uniform(0.8, 1.5), 2))

            # 第八步 二次确认兑换
            if not self.func.find_exchange_re_ok(self._hwnd):
                self.sin_out.emit(f"窗口:{self._hwnd} 未找到二次确认兑换")
                self.working = False
                break
            self.sin_out.emit(f"窗口:{self._hwnd} 幸运币兑换成功")
            time.sleep(1.5)
            exchange_count += 1

        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()  # 解锁
        return None

