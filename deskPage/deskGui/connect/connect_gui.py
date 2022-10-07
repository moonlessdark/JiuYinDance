import os
import sys
from deskPage.toolSoft.enum_key import damo_tools
from deskPage.deskGui.guiPage.JiuYinTools import Ui_MainWindow
from deskPage.deskGui.th.execut_th import DanceThByFindPic, signInTh, DanceThByHash
from deskPage.common.dmSoft.get_dm_driver import getDM, getWindows, getKeyBoardMouse


class signIn(Ui_MainWindow):
    """
    公众号签到
    """
    def __init__(self):
        super(signIn, self).__init__()

        self.debug_mode = False
        self.account = None  # 账号
        self.password = None  # 密码
        self.area = None  # 游戏大区
        self.service = None  # 服务器
        self.project_path = None

        self.th_sign = signInTh()

        self.th_sign.sin_out_sign.connect(self.print_log_sign)
        self.th_sign.work_status_sign.connect(self.button_status)

        # self.execute_siginIn_button.clicked.connect(self.execute_sign_in)
        self.execute_siginIn_button.clicked.connect(self.execute)
        self.check_intelnet_button.clicked.connect(self.check_driver_by_edge)

    def print_log_sign(self, content: str, is_clear=False):
        if is_clear:
            self.log_textBrowser.clear()
        self.log_textBrowser.insertPlainText(content + "\n")

    def check_driver_by_edge(self):
        """
        检测浏览器驱动是否准备好
        :return:
        """
        self.print_log_sign("开始检测环境，请稍后", is_clear=True)
        self.th_sign.start_execute()
        self.th_sign.get_parm(account="11,22", password="33,44", area="武侠区",
                              service="侠骨丹心", error_pic_path=self.project_path, is_check=True)
        self.th_sign.start()

    # def execute_sign_in(self):
    #     """
    #     不读取配置文件时使用，打包给别人时记得删掉账号密码
    #     :return:
    #     """
    #     self.print_log_sign("初始化中，正在检查Edge浏览器版本信息", True)
    #     self.th_sign.start_execute()
    #     self.th_sign.get_parm(account="11,22", password="33,44", area="武侠区",
    #                           service="侠骨丹心", error_pic_path=self.project_path)
    #     self.th_sign.start()

    def execute(self):
        """
        读取本地配置文件时使用
        :return:
        """
        if self.check_ini() and self.th_sign.get_parm(account=self.account, password=self.password, area=self.area,
                                                      service=self.service, error_pic_path=self.project_path):
            self.th_sign.start_execute()
            self.print_log_sign("登录参数已经就绪，准备执行签到", True)
            self.th_sign.start()

    def button_status(self, status: bool):
        if status:
            self.execute_siginIn_button.setEnabled(False)
            self.check_intelnet_button.setEnabled(False)
        else:
            self.execute_siginIn_button.setEnabled(True)
            self.check_intelnet_button.setEnabled(True)

    @staticmethod
    def get_application_path():
        """
        获取打包后的app路径，因为配置文件一般放在这里
        :return:
        """
        application = ""
        if getattr(sys, "frozen", False):
            application = os.path.dirname(sys.executable)
        elif __file__:
            application = os.path.dirname(__file__)
        config_path = os.path.join(application, "JiuYinSign.ini")
        return config_path

    @staticmethod
    def get_project_path():
        application = ""
        if getattr(sys, "frozen", False):
            application = os.path.dirname(sys.executable)
        elif __file__:
            application = os.path.dirname(__file__)
        return application

    def get_config_ini(self, file_path: str = None) -> bool:
        # pyinstaller模式
        config_ini = self.get_application_path() if file_path is None else file_path
        result_list: list = []
        result_bool: bool = True
        if os.path.isfile(config_ini):
            with open(config_ini, "r", encoding="utf-8") as rf:
                result_list = rf.readlines()
            if len(result_list) == 4:
                for i in result_list:
                    i = i.replace("\n", "") if "\n" in i else i
                    if i != "":
                        content: str = i.replace("：", ":") if "：" in i else i
                        content = content + " "
                        r = content.split(":")
                        key: str = r[0]
                        value: str = r[1]
                        if key == "账号":
                            self.account = value.replace(" ", "")
                        elif key == "密码":
                            self.password = value.replace(" ", "")
                        elif key == "大区":
                            self.area = value.replace(" ", "")
                        elif key == "服务器":
                            self.service = value.replace(" ", "")
                if self.account is None or self.account == "":
                    result_bool = False
                    self.print_log_sign("账号信息未填写，请检查配置文件")
                if self.password is None or self.password == "":
                    result_bool = False
                    self.print_log_sign("密码信息未填写，请检查配置文件")
                if self.area is None or self.area == "":
                    result_bool = False
                    self.print_log_sign("游戏大区信息未填写，请检查配置文件")
                if self.area is None or self.area == "":
                    result_bool = False
                    self.print_log_sign("服务器信息未填写，请检查配置文件")
                return result_bool
            else:
                self.print_log_sign("配置文件内容错误，请删除旧文件后重新生成")
                return False

    def check_ini(self):
        """
        检查配置文件是否存在
        :return:
        """
        config_ini = None
        if self.debug_mode is False:
            # pyinstaller模式
            config_ini = self.get_application_path()
        else:
            # debug模式
            config_ini = "D:\SoftWare\DEV\project\JiuYinWechatSignByPyqt\dist\JiuYinSign.ini"

        self.project_path = self.get_project_path()
        self.print_log_sign("正在检查配置文件是否存在", True)
        if not os.path.isfile(config_ini):
            with open(config_ini, "w+", encoding='utf-8') as f:
                f.writelines("账号：" + "\n")
                f.writelines("密码：" + "\n")
                f.writelines("大区：武侠区" + "\n")
                f.writelines("服务器：侠骨丹心" + "\n")
                self.print_log_sign("配置文件不存在，已生成新的配置文件，在本程序相同路径下生成(JiuYinSignIn.ini)。请完善信息")
                return False
        else:
            self.print_log_sign("配置文件存在,开始检查完整性")
            return self.get_config_ini(config_ini)


class dance(Ui_MainWindow):
    """
    团练授业
    """

    def __init__(self):
        super().__init__()
        # 初始化一些对象
        # self.th = DanceThByHash()
        self.th = DanceThByFindPic()
        getDM(dm_reg_path=damo_tools.dm_reg.value, dm_path=damo_tools.dm.value)

        # 定义3个窗口的handle
        self.windows_1_handle = None
        self.windows_2_handle = None
        self.windows_3_handle = None
        self.gui_windows_handle_list = []

        # 初始化一些控件的内容
        self.statusbar.showMessage(" 当前状态 : 等待执行")

        # 信号槽连接
        self.th.status_bar.connect(self.print_status_bar)
        self.th.sin_out.connect(self.print_logs)
        self.th.sin_work_status.connect(self.execute_status)

        # click事件的信号槽
        self.execute_dance_button.clicked.connect(self.execute_button_status)
        self.get_windows_list_button.clicked.connect(self.get_game_windows)
        self.test_windows_button.clicked.connect(self.test_windows_handle)

    def print_logs(self, text, is_clear=False):
        """
        打印日志的方法
        :param is_clear: 是否清楚日志
        :param text: 日志内容
        :return:
        """
        if is_clear:
            self.log_textBrowser.clear()
        self.log_textBrowser.insertPlainText(text + '\n')

    def print_status_bar(self, text):
        """
        打印底部状态栏的日志
        :param text:
        :return:
        """
        self.statusbar.showMessage(text)

    def check_handle_is_selected(self):
        """
        看看哪些窗口已经勾选了
        :return:
        """
        windows_list = []
        if self.checkBox_1_windows.isChecked():
            windows_list.append(self.windows_1_handle)
        if self.checkBox_2_windows.isChecked():
            windows_list.append(self.windows_2_handle)
        if self.checkBox_3_windows.isChecked():
            windows_list.append(self.windows_3_handle)
        return windows_list

    def execute_start(self):
        """
        点击开始执行按钮
        :return:
        """
        windows_list = self.check_handle_is_selected()
        if len(windows_list) == 0:
            self.print_logs("请选择您需要执行的游戏窗口")
        else:
            self.print_logs("开始执行", is_clear=True)
            self.th.start_execute_init(windows_list)
            self.th.start()
            self.execute_dance_button.setText("结束执行")

    def execute_button_status(self):
        if self.th.working is True and self.execute_dance_button.text() == '开始执行':
            self.execute_start()
        elif self.th.working is True and self.execute_dance_button.text() == '结束执行':
            self.stop_execute()
        elif self.th.working is False and self.execute_dance_button.text() == '开始执行':
            self.execute_start()

    def execute_stop(self):
        """
        结束执行
        :return:
        """
        self.th.stop_execute_init()
        self.print_logs("等待程序结束运行")
        self.statusbar.showMessage(" 当前状态 : 等待执行")

    def __get_windows_handle(self):
        """
        获取游戏窗口有多少个
        :return:
        """
        # 先把3个变量初始化一下，避免窗口关闭后重新获取有旧数据残存
        self.windows_1_handle = None
        self.windows_2_handle = None
        self.windows_3_handle = None
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
        """
        检测游戏打开了几个窗口
        :return:
        """
        # 先把3个按钮状态初始化一下
        self.checkBox_1_windows.setEnabled(False)
        self.checkBox_2_windows.setEnabled(False)
        self.checkBox_3_windows.setEnabled(False)

        windows_handle_list = self.__get_windows_handle()

        if 0 < len(windows_handle_list) < 4:
            self.print_logs("已检测到 %d 个游戏窗口" % len(windows_handle_list), is_clear=True)
            windows_list = [self.checkBox_1_windows, self.checkBox_2_windows, self.checkBox_3_windows]
            for i in range(len(windows_handle_list)):
                windows_list[i].setEnabled(True)
                # getWindows().set_window_state(windows_handle_list[i], 1)
            self.test_windows_button.setEnabled(True)
            self.execute_dance_button.setEnabled(True)
        elif len(windows_handle_list) > 3:
            self.print_logs("窗口数量超时3个的限制，请关闭其余的窗口")
        else:
            self.print_logs("未检测到游戏窗口...")

    def test_windows_handle(self):
        """
        检测游戏窗口.对当前活跃的游戏窗口进行检测
        :return:
        """
        windows_handle = getWindows().set_window_state(getWindows().find_window("", "FxMain"), 12)
        # getWindows().set_window_state(windows_handle, 8)  # 置顶窗口
        getWindows().set_window_state(windows_handle, 1)  # 激活窗口
        getKeyBoardMouse().key_down_char("k", hold_time=0.1)
        self.print_logs("窗口已激活，并按下了'K'按钮")
        # getWindows().set_window_state(windows_handle, 9)

    def stop_execute(self):
        """
        停止执行
        :return:
        """
        self.print_logs("已发出停止指令，请等待")
        self.th.stop_execute_init()
        self.execute_dance_button.setText("开始执行")
        self.statusbar.showMessage(" 当前状态 : 等待执行")

    def execute_status(self, sin_work_status):
        self.execute_dance_button.setEnabled(True)
        self.stop_execute()


class mainUI(signIn, dance):
    def __init__(self):
        super(mainUI, self).__init__()
