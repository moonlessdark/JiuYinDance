import time

import win32con
import win32gui

from gui.page.tuanlian import Ui_main_page_gui
from business.execut_th import signalThreading
from business.windows_screen.get_screen_windows import windowsCap



class mainUI(Ui_main_page_gui):

    def __init__(self):
        super().__init__()
        self.log_count = 0
        self.th = signalThreading()
        self.windows_cap = windowsCap()

        # 定义3个窗口的handlie
        self.windows_1_handle = None
        self.windows_2_handle = None
        self.windows_3_handle = None

        self.th.sin_out.connect(self.print_logs)
        self.th.sin_work_status.connect(self.execute_status)
        self.execute_button.clicked.connect(self.execute_button_status)
        self.get_windows_list_button.clicked.connect(self.get_game_windows)

        self.test_windows_1_button.clicked.connect(self.test_windows_handle_by_1)
        self.test_windows_2_button.clicked.connect(self.test_windows_handle_by_2)
        self.test_windows_3_button.clicked.connect(self.test_windows_handle_by_3)

    def print_logs(self, text):
        """
        打印日志的方法
        :param text:
        :return:
        """
        if self.log_count < 16:
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = self.log_count + 1
        else:
            self.log_textBrowser.clear()
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = 0

    def start_execute(self):
        if self.type_select_button.currentText() == "团练模式":
            windows_list = []
            if self.checkBox_1_windows.isChecked():
                windows_list.append(self.windows_1_handle)
            if self.checkBox_2_windows.isChecked():
                windows_list.append(self.windows_2_handle)
            if self.checkBox_3_windows.isChecked():
                windows_list.append(self.windows_3_handle)
            if len(windows_list) == 0:
                self.print_logs("请选择您需要团练的窗口")
                return None
            self.print_logs("开始执行自定义模式")
            self.th.start_execute_init(windows_list)
            self.th.start()
            self.execute_button.setText("结束执行")
        else:
            windows_list = []
            if self.checkBox_1_windows.isChecked():
                windows_list.append(self.windows_1_handle)
            if self.checkBox_2_windows.isChecked():
                windows_list.append(self.windows_2_handle)
            if self.checkBox_3_windows.isChecked():
                windows_list.append(self.windows_3_handle)
            if len(windows_list) == 0:
                self.print_logs("请选择您需要团练的窗口")
                return None
            elif len(windows_list) == 3:
                self.print_logs("授业模式最多只支持2个窗口")
                return None
            self.print_logs("开始执行授业模式")
            self.th.start_execute_init(windows_list)
            self.th.start()
            self.execute_button.setText("结束执行")

    def stop(self):
        self.th.pause()
        self.print_logs("等待程序结束运行")

    def get_game_windows(self):
        self.line_1_windows.clear()
        self.line_2_windows.clear()
        self.line_3_windows.clear()
        self.checkBox_3_windows.setChecked(False)
        self.checkBox_2_windows.setChecked(False)
        self.checkBox_3_windows.setChecked(False)
        windows_list = self.windows_cap.get_windows_handle()
        if len(windows_list) > 0:
            self.print_logs("已检测到 %d 个游戏窗口" % len(windows_list))
            self.checkBox_3_windows.setEnabled(False)
            self.checkBox_2_windows.setEnabled(False)
            self.checkBox_1_windows.setEnabled(True)
            self.test_windows_1_button.setEnabled(True)
            self.windows_1_handle = windows_list[0]
            # self.print_logs("%d" % windows_list[0])
            if len(windows_list) > 1:
                self.checkBox_2_windows.setEnabled(True)
                self.checkBox_3_windows.setEnabled(False)
                self.test_windows_2_button.setEnabled(True)
                self.windows_2_handle = windows_list[1]
                # self.print_logs("%d" % windows_list[1])
                if len(windows_list) > 2:
                    self.checkBox_3_windows.setEnabled(True)
                    self.windows_3_handle = windows_list[2]
                    self.test_windows_3_button.setEnabled(True)
            self.execute_button.setEnabled(True)

        else:
            self.checkBox_3_windows.setEnabled(False)
            self.checkBox_2_windows.setEnabled(False)
            self.checkBox_1_windows.setEnabled(False)
            self.print_logs("未检测到游戏窗口...")

    def test_windows_handle_by_1(self):
        win32gui.SetForegroundWindow(self.windows_1_handle)
        win32gui.ShowWindow(self.windows_1_handle, win32con.SW_SHOW)
        self.print_logs("1号窗口已激活，请填写1号窗的备注信息")

    def test_windows_handle_by_2(self):
        win32gui.SetForegroundWindow(self.windows_2_handle)
        win32gui.ShowWindow(self.windows_2_handle, win32con.SW_SHOW)
        self.print_logs("2号窗口已激活，请填写2号窗的备注信息")

    def test_windows_handle_by_3(self):
        win32gui.SetForegroundWindow(self.windows_3_handle)
        win32gui.ShowWindow(self.windows_3_handle, win32con.SW_SHOW)
        self.print_logs("3号窗口已激活，请填写3号窗的备注信息")

    def stop_execute(self):
        """
        停止执行
        :return:
        """
        self.th.pause()
        self.print_logs("已发出停止指令，请等待")
        self.execute_button.setText("开始执行")

    def execute_button_status(self):
        if self.th.working is True and self.execute_button.text() == '开始执行':
            self.start_execute()
        elif self.th.working is True and self.execute_button.text() == '结束执行':
            self.stop_execute()
        elif self.th.working is False and self.execute_button.text() == '开始执行':
            self.start_execute()
        else:
            self.execute_button.setText("开始执行")

    def execute_status(self, sin_work_status):
        if sin_work_status == "结束":
            self.execute_button.setText("开始执行")
            self.execute_button.setEnabled(True)
