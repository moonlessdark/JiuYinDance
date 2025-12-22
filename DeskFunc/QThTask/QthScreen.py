import os
import time

import cv2
from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from Utils.FindWindowsImage import WindowsCapture, PicCapture


class ScreenGameQth(QThread):
    """
    截图
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
        self.windows_handle_list = []

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def get_param(self, windows_handle_list: list, pic_save_path: str):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle_list = windows_handle_list
        self.pic_save_path = pic_save_path

    def run(self):
        self.mutex.lock()  # 先加锁

        # 先创建一个文件
        time_str_m = time.strftime("%H_%M", time.localtime(int(time.time())))
        pic_file_path = self.pic_save_path + "/JiuYinScreenPic/" + time_str_m + "/"
        if not os.path.exists(pic_file_path):  # 如果主目录+小时+分钟这个文件路径不存在的话
            os.makedirs(pic_file_path)

        self.sin_run_status.emit(True)  # 发送消息，人物开始

        _cap_pic_count: int = 0  # 截图数量

        while 1:
            if not self.working:
                break

            for hi in self.windows_handle_list:
                pic_content_obj: PicCapture = self.windows_cap.capture(hi)
                if pic_content_obj is None:
                    self.sin_out.emit("窗口截图失败")
                    self.working = False
                    break

                if min(pic_content_obj.pic_height, pic_content_obj.pic_width) > 0:
                    time_str_s = time.strftime("%H_%M_%S", time.localtime(int(time.time())))
                    cv2.imwrite(f"{pic_file_path}{time_str_s}.png", pic_content_obj.pic_content)
                    _cap_pic_count += 1
                    self.status_bar.emit(_cap_pic_count)
                time.sleep(1)
        self.sin_out.emit("窗口截图结束")
        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()
        return None
