from deskPage.gui.page.mz import Ui_Form
from deskPage.gui.page.tuanlian import Ui_main_page_gui
from deskPage.gui.th.execut_th import tuanLianTh
from deskPage.common.DMSoft.get_dm_driver import getDM, getWindows, getKeyBoardMouse
from deskPage.common.tools.resources_tools.enum_key import damo_tools


class mz(Ui_Form):
    def __init__(self):
        super().__init__()


class mainUI(Ui_main_page_gui):

    def __init__(self):
        super().__init__()
        self.log_count = 0
        self.th = tuanLianTh()
        getDM(dm_reg_path=damo_tools.dm_reg.value, dm_path=damo_tools.dm.value)
        self.mz_windows = mz()
        self.down_status_line.showMessage(" 当前状态 : 等待执行")

        # 定义3个窗口的handlie
        self.windows_1_handle = None
        self.windows_2_handle = None
        self.windows_3_handle = None

        self.th.status_bar.connect(self.print_status_bar)
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
        if self.log_count < 100:
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = self.log_count + 1
        else:
            self.log_textBrowser.clear()
            self.log_textBrowser.insertPlainText(text + '\n')
            self.log_count = 0

    def print_status_bar(self, text):
        """
        打印日志的方法
        :param text:
        :return:
        """
        self.down_status_line.showMessage(text)

    def start_execute(self):
        """
        点击开始执行按钮
        :return:
        """
        windows_list = []
        if self.checkBox_1_windows.isChecked():
            windows_list.append(self.windows_1_handle)
        if self.checkBox_2_windows.isChecked():
            windows_list.append(self.windows_2_handle)
        if self.checkBox_3_windows.isChecked():
            windows_list.append(self.windows_3_handle)
        if len(windows_list) == 0:
            self.print_logs("请选择您需要执行的游戏窗口")
            return None
        else:
            self.th.start_execute_init(windows_list, self.type_select_button.currentText())
            self.print_logs("开始执行")
            self.th.start()
            self.execute_button.setText("结束执行")

    def stop(self):
        """
        结束执行
        :return:
        """
        self.th.stop_execute_init()
        self.print_logs("等待程序结束运行")
        self.down_status_line.showMessage(" 当前状态 : 等待执行")

    def get_windows_handle(self):
        """
        获取游戏窗口有多少个
        :return:
        """
        windows_handle_list = getWindows().enum_window(0, "", "FxMain", 2)
        gui_windows_handle_list = []
        if len(windows_handle_list) == 1:
            self.windows_1_handle = int(windows_handle_list[0])
            gui_windows_handle_list = [self.windows_1_handle]
        elif len(windows_handle_list) == 2:
            self.windows_1_handle = int(windows_handle_list[0])
            self.windows_2_handle = int(windows_handle_list[1])
            gui_windows_handle_list = [self.windows_1_handle, self.windows_2_handle]
        elif len(windows_handle_list) == 3:
            self.windows_1_handle = int(windows_handle_list[0])
            self.windows_2_handle = int(windows_handle_list[1])
            self.windows_3_handle = int(windows_handle_list[2])
            gui_windows_handle_list = [self.windows_1_handle, self.windows_2_handle, self.windows_3_handle]
        return gui_windows_handle_list

    def get_game_windows(self):
        # 先把按钮状态初始化一下
        self.line_1_windows.clear()
        self.line_2_windows.clear()
        self.line_3_windows.clear()
        self.checkBox_3_windows.setChecked(False)
        self.checkBox_2_windows.setChecked(False)
        self.checkBox_1_windows.setChecked(False)
        self.test_windows_3_button.setEnabled(False)
        self.test_windows_2_button.setEnabled(False)
        self.test_windows_1_button.setEnabled(False)
        windows_handle_list = self.get_windows_handle()
        if 0 < len(windows_handle_list) < 4:
            self.print_logs("已检测到 %d 个游戏窗口" % len(windows_handle_list))
            windows_list = [self.checkBox_1_windows, self.checkBox_2_windows, self.checkBox_3_windows]
            windows_button_list = [self.test_windows_1_button, self.test_windows_2_button, self.test_windows_3_button]
            for i in range(len(windows_handle_list)):
                windows_list[i].setEnabled(True)
                windows_button_list[i].setEnabled(True)
                getWindows().set_window_state(windows_handle_list[i], 4)
            self.execute_button.setEnabled(True)
        elif len(windows_handle_list) > 3:
            self.print_logs("窗口数量超时3个的限制，请关闭其余的窗口")
        else:
            self.print_logs("未检测到游戏窗口...")

    def test_windows_handle_by_1(self):
        getWindows().set_window_state(self.windows_1_handle, 12)
        getKeyBoardMouse().key_down_char("k", hold_time=0.1)
        self.print_logs("1号窗口已激活，并按下了'K'按钮")

    def test_windows_handle_by_2(self):
        getWindows().set_window_state(self.windows_2_handle, 8)
        getKeyBoardMouse().key_down_char("k", hold_time=0.1)
        self.print_logs("2号窗口已激活，并按下了'K'按钮")
        getWindows().set_window_state(self.windows_2_handle, 9)

    def test_windows_handle_by_3(self):
        getWindows().set_window_state(self.windows_3_handle, 8)
        getKeyBoardMouse().key_down_char("k", hold_time=0.1)
        self.print_logs("3号窗口已激活，并按下了'K'按钮")
        getWindows().set_window_state(self.windows_3_handle, 9)

    def stop_execute(self):
        """
        停止执行
        :return:
        """
        self.print_logs("已发出停止指令，请等待")
        self.th.stop_execute_init()
        self.execute_button.setText("开始执行")
        self.down_status_line.showMessage(" 当前状态 : 等待执行")

    def execute_button_status(self):
        if self.th.working is True and self.execute_button.text() == '开始执行':
            self.start_execute()
        elif self.th.working is True and self.execute_button.text() == '结束执行':
            self.stop_execute()
        elif self.th.working is False and self.execute_button.text() == '开始执行':
            self.start_execute()

    def execute_status(self, sin_work_status):
        self.execute_button.setEnabled(True)
        self.stop_execute()
