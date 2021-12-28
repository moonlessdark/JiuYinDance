from gui.page.tuanlian import Ui_main_page_gui
from business.execut_th import signalThreading
from business.windows_screen.get_screen_windows import windowsCap



class mainUI(Ui_main_page_gui):

    def __init__(self):
        super().__init__()
        self.log_count = 0
        self.th = signalThreading()
        self.windows_cap = windowsCap()

        self.th.sin_out.connect(self.print_logs)
        self.execute_button.clicked.connect(self.start_execute)
        self.select_windows_button.clicked.connect(self.get_game_windows)

    def print_logs(self, text):
        """
        打印日志的方法
        :param text:
        :return:
        """
        if self.log_count < 13:
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = self.log_count + 1
        else:
            self.log_textBrowser.clear()
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = 0

    def start_execute(self):

        self.print_logs("开始执行")
        windows_list = []
        if self.windows_1_check.isChecked():
            windows_list.append(1)
        if self.windows_2_check.isChecked():
            windows_list.append(2)
        if self.windows_3_check.isChecked():
            windows_list.append(3)
        if len(windows_list) == 0:
            self.print_logs("请选择您需要团练的窗口")
            return None
        self.th.start_execute_init(self.windows_cap.get_windows_handle(), windows_list)
        self.th.start()

    def stop(self):
        self.th.pause()
        self.print_logs("等待程序结束运行")

    def get_game_windows(self):
        windows_list = self.windows_cap.get_windows_handle()
        if len(windows_list) > 0:
            self.print_logs("已检测到 %d 个游戏窗口" % len(windows_list))
            self.windows_3_check.setEnabled(False)
            self.windows_2_check.setEnabled(False)
            self.windows_1_check.setEnabled(True)
            if len(windows_list) > 1:
                self.windows_2_check.setEnabled(True)
                self.windows_3_check.setEnabled(False)
                if len(windows_list) > 2:
                    self.windows_3_check.setEnabled(True)
            self.execute_button.setEnabled(True)

        else:
            self.windows_3_check.setEnabled(False)
            self.windows_2_check.setEnabled(False)
            self.windows_1_check.setEnabled(False)
            self.print_logs("未检测到游戏窗口...")


