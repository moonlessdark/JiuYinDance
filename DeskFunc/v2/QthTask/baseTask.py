# coding: utf-8
"""
v2 任务线程基类。

统一所有后台任务的对外契约：
- sin_out(str)：日志输出
- status_bar(int)：底部状态栏计数
- sin_run_status(bool)：任务开始/结束状态
- working：任务线程的退出标志
- stop_execute_init() / stop_stak()：停止任务

各任务线程只关注自己的 run() 业务逻辑，重复的信号定义、停止方法、
线程锁和等待条件由本类提供。
"""
from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal


class BaseTaskThread(QThread):
    """所有任务线程的公共基类。"""

    sin_out = Signal(str)  # 日志打印
    status_bar = Signal(int)  # 底部状态栏计数
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()

    def __del__(self):
        try:
            self.working = False
        except (AttributeError, RuntimeError):
            pass

    def stop_execute_init(self):
        """停止任务，供 GUI 的“停止执行”按钮调用。"""
        self.working = False

    def stop_stak(self):
        """兼容旧方法的停止入口。"""
        self.stop_execute_init()

    def is_working(self) -> bool:
        return bool(self.working)
