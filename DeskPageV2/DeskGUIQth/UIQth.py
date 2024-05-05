# coding: utf-8

import time
from PySide6.QtCore import QThread, Signal, QMutex


class QProgressBarQth(QThread):
    """
    底部的跑马灯进度条
    """
    thread_step = Signal(int)

    def __init__(self):

        super(QProgressBarQth, self).__init__()
        self.working = True
        self.step = 0  # 进度条跑马灯效果初始值设置为0
        self.mutex = QMutex()

    def __del__(self):
        self.working = False

    def start_init(self):
        self.working = True
        self.step = 0

    def stop_init(self):
        self.working = False
        self.step = 0

    def run(self):

        self.mutex.lock()  # 先加锁
        while self.working:
            if self.step < 101:
                self.step += 1
                self.thread_step.emit(self.step)
            else:
                self.step = 0
            time.sleep(0.001)
        self.thread_step.emit(0)
        self.mutex.unlock()
        return None
