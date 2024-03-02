import random
import time

from DeskPageV2.DeskTools.DmSoft.regsvr import reg_dm_soft


class GetKeyBordAndMouse:
    """
    键盘鼠标操作
    """

    """
    以下是按下按钮需要的输入的 key_str 和 vk_code
    key_str     虚拟键码
    "1",          49
    "2",          50
    "3",          51
    "4",          52
    "5",          53
    "6",          54
    "7",          55
    "8",          56
    "9",          57
    "0",          48
    "-",          189
    "=",          187
    "back",       8

    "a",          65
    "b",          66
    "c",          67
    "d",          68
    "e",          69
    "f",          70
    "g",          71
    "h",          72
    "i",          73
    "j",          74
    "k",          75
    "l",          76
    "m",          77
    "n",          78
    "o",          79
    "p",          80
    "q",          81
    "r",          82
    "s",          83
    "t",          84
    "u",          85
    "v",          86
    "w",          87
    "x",          88
    "y",          89
    "z",          90

    "ctrl",       17
    "alt",        18
    "shift",      16
    "win",        91
    "space",      32
    "cap",        20
    "tab",        9
    "~",          192

    "esc",        27
    "enter",      13

    "up",         38
    "down",       40
    "left",       37
    "right",      39

    "option",     93
    "print",      44
    "delete",     46
    "home",       36
    "end",        35
    "pgup",       33
    "pgdn",       34

    "f1",         112
    "f2",         113
    "f3",         114
    "f4",         115
    "f5",         116
    "f6",         117
    "f7",         118
    "f8",         119
    "f9",         120
    "f10",        121
    "f11",        122
    "f12",        123

    "[",          219
    "]",          221
    "\\",         220
    ";",          186
    "'",          222
    ",",          188
    ".",          190
    "/",          191
    """

    def __init__(self):
        self.dm = None

    def get_dm_driver(self, dm=None, dm_reg_path: str = None, dm_path: str = None):
        """
        :param dm: 已经加载成功的大漠插件驱动对象
        :param dm_reg_path: DmReg.dll的路径
        :param dm_path: dm.dll的路径
        """
        if dm is None:
            self.dm = reg_dm_soft(dm_reg_path, dm_path)
        else:
            self.dm = dm

    def wait_key(self, vk_code: int, time_out=0) -> int:
        """
        等待键盘输入某个字符，(前台,不是后台)
        :param vk_code: 虚拟按键码
        :param time_out: 等待多久,单位毫秒. 如果是0，表示一直等待
        :return: 0:超时 1:指定的按键按下
        """
        return self.dm.WaitKey(vk_code, time_out)

    def sleep_time(self, end_time: float):
        """
        等待时间
        :param end_time: 结束时间
        """
        end_time = 0.2 if end_time == 0 else end_time
        time.sleep(round(random.uniform(0.01, end_time), 2))

    def get_key_status(self, vk_code: int) -> int:
        """
        获取指定的按键状态.(前台信息,不是后台)
        :param vk_code: 虚拟按键码
        :return: 0:弹起 1:按下
        """
        return self.dm.GetKeyState(vk_code)

    def key_down(self, vk_code: int, hold_time: float = 0.1) -> bool:
        """
        按住指定的虚拟键码
        :param hold_time: 按住按钮的时长
        :param vk_code: 字符编码
        """
        self.dm.KeyDown(vk_code)
        self.sleep_time(hold_time)
        self.key_up(vk_code)
        return True

    def key_down_char(self, key_str: str, hold_time: float = 0.1):
        """
        按住指定的虚拟键码，支持以字符形式传入
        :param hold_time: 按住按钮的时长
        :param key_str: 按钮字符,不区分大小写
        """
        self.dm.KeyDownChar(key_str)
        self.sleep_time(hold_time)
        self.key_up_char(key_str)

    def key_press(self, vk_code: int, sleep_time: float = 0.1) -> bool:
        """
        按下指定的虚拟键码
        :param sleep_time: 按了按钮之后等待的时间
        :param vk_code: 字符编码
        """
        if self.dm.KeyPress(vk_code) == 1:
            self.sleep_time(sleep_time)
            return True
        else:
            return False

    def key_press_char(self, key_str: str, sleep_time: float = 0.1) -> bool:
        """
        按下指定的虚拟键码
        :param sleep_time: 按了按钮之后等待的时间
        :param key_str: 按钮字符,不区分大小写
        """
        if self.dm.KeyPressChar(key_str) == 1:
            self.sleep_time(sleep_time)
            return True
        else:
            return False

    def key_press_str(self, key_str: str, delay: int) -> bool:
        """
        根据指定的字符串序列，依次按顺序按下其中的字符.
        注: 在某些情况下，SendString和SendString2都无法输入文字时，可以考虑用这个来输入.
            但这个接口只支持"a-z 0-9 ~-=[];',./"和空格,其它字符一律不支持.
        :param key_str: 需要按下的字符串序列. 比如"1234","abcd","7389,1462"等.
        :param delay: 每按下一个按键，需要延时多久. 单位毫秒.这个值越大，按的速度越慢。
        """
        return True if self.dm.KeyPressStr(key_str, delay) == 1 else False

    def key_up(self, vk_code: int) -> bool:
        """
        弹起来虚拟键
        :param vk_code: 字符编码
        """
        return True if self.dm.KeyUp(vk_code) == 1 else False

    def key_up_char(self, key_str: str) -> bool:
        """
        弹起来虚拟键
        :param key_str: 字符串描述的键码. 大小写无所谓
        """
        return True if self.dm.KeyUpChar(key_str) == 1 else False

    def left_click(self) -> bool:
        """
        单击鼠标左键
        """
        return True if self.dm.LeftClick() == 1 else False

    def left_double_click(self) -> bool:
        """
        双击鼠标左键
        """
        return True if self.dm.LeftDoubleClick() == 1 else False

    def left_down(self) -> bool:
        """
        按住鼠标左键
        """
        return True if self.dm.LeftDown() == 1 else False

    def left_up(self) -> bool:
        """
        弹起鼠标左键
        """
        return True if self.dm.LeftUp() == 1 else False

    def middle_click(self) -> bool:
        """
        按下鼠标中键
        """
        return True if self.dm.MiddleClick() == 1 else False

    def move_r(self, rx: int, ry: int) -> bool:
        """
        鼠标相对于上次的位置移动rx,ry
        :param rx: 相对于上次的X偏移
        :param ry: 相对于上次的Y偏移
        """
        return True if self.dm.MoveR(rx, ry) == 1 else False

    def move_to(self, x: int, y: int) -> bool:
        """
        把鼠标移动到目的点(x,y)
        :param x: X坐标
        :param y: Y坐标
        """
        return True if self.dm.MoveTo(int(x), int(y)) == 1 else False

    def move_to_ex(self, x: int, y: int, w: int, h: int) -> bool:
        """
        把鼠标移动到目的范围内的任意一点
        :param x: X坐标
        :param y: Y坐标
        :param w: 宽度(从x计算起)
        :param h: 高度(从y计算起)
        """
        return True if self.dm.MoveToEx(x, y, w, h) == 1 else False

    def right_click(self) -> bool:
        """
        单机鼠标右键
        """
        return True if self.dm.RightClick() == 1 else False

    def right_down(self) -> bool:
        """
        按住鼠标右键
        """
        return True if self.dm.RightDown() == 1 else False

    def right_up(self) -> bool:
        """
        弹起鼠标右键
        """
        return True if self.dm.RightUp() == 1 else False

    def set_keypad_delay(self, type_str: str, delay: int) -> bool:
        """
        注 : 此函数影响的接口有KeyPress
        设置按键时,键盘按下和弹起的时间间隔。
        高级用户使用。
        某些窗口可能需要调整这个参数才可以正常按键。

        :param type_str: 键盘类型,取值有以下
                        "normal" : 对应normal键盘  默认内部延时为30ms
                        "windows": 对应windows 键盘 默认内部延时为10ms
                        "dx"     : 对应dx 键盘 默认内部延时为50ms
        :param delay: 延时,单位是毫秒
        """
        return True if self.dm.SetKeypadDelay(type_str, delay) == 1 else False

    def set_mouse_delay(self, type_str: str, delay: int) -> bool:
        """
        注 : 此函数影响的接口有LeftClick RightClick MiddleClick LeftDoubleClick
        设置鼠标单击或者双击时,鼠标按下和弹起的时间间隔。高级用户使用。某些窗口可能需要调整这个参数才可以正常点击。

        :param type_str:鼠标类型,取值有以下
                         "normal" : 对应normal鼠标 默认内部延时为 30ms
                         "windows": 对应windows 鼠标 默认内部延时为 10ms
                         "dx" :     对应dx鼠标 默认内部延时为40ms
        :param delay: 延时,单位是毫秒
        """
        return True if self.dm.SetMouseDelay(type_str, delay) == 1 else False

    def wheel_down(self) -> bool:
        """
        滚轮向下滚
        """
        return True if self.dm.WheelDown() == 1 else False

    def wheel_up(self) -> bool:
        """
        滚轮向上滚
        """
        return True if self.dm.WheelUp() == 1 else False

    def move_and_left_click(self, x, y, sleep_time=3):
        """
        移动到指定的位置并按下鼠标左键
        :param sleep_time: 休眠时间
        :param x: x坐标
        :param y: y坐标
        :return:
        """
        self.move_to(x, y)
        self.sleep_time(sleep_time)
        self.left_click()


class GetWindows:
    """
    窗口操作
    """

    def __init__(self):
        self.dm = None

    def get_dm_driver(self, dm=None, dm_reg_path: str = None, dm_path: str = None):
        """
        :param dm: 已经加载成功的大漠插件驱动对象
        :param dm_reg_path: DmReg.dll的路径
        :param dm_path: dm.dll的路径
        """
        if dm is None:
            self.dm = reg_dm_soft(dm_reg_path, dm_path)
        else:
            self.dm = dm

    def find_window(self, title: str = "", class_str: str = "") -> int:
        """
        找符合类名或者标题名的顶层可见窗口
        :param class_str: 窗口类名，如果为空，则匹配所有. 这里的匹配是模糊匹配.
        :param title: 窗口标题,如果为空，则匹配所有.这里的匹配是模糊匹配.
        :return: 窗口句柄, 没找到返回0
        """
        return self.dm.FindWindow(class_str, title)

    def find_window_ex(self, parent: int or str = "", class_str: str = "", title: str = "") -> int:
        """
        查找符合类名或者标题名的顶层可见窗口,如果指定了parent,则在parent的第一层子窗口中查找.
        :param parent: 父窗口句柄，如果为空，则匹配所有顶层窗口
        :param class_str: 窗口类名，如果为空，则匹配所有. 这里的匹配是模糊匹配
        :param title: 窗口标题,如果为空，则匹配所有. 这里的匹配是模糊匹配
        :return:
        """
        return self.dm.FindWindowEx(parent, class_str, title)

    def enum_window(self, parent: int = 0, title: str = "", class_name: str = "", filter_num: int = 16) -> list:
        """
        根据指定条件,枚举系统中符合条件的窗口,可以枚举到按键自带的无法枚举到的窗口
        :param parent: 获得的窗口句柄是该窗口的子窗口的窗口句柄,取0时为获得桌面句柄
        :param title: 窗口标题. 此参数是模糊匹配
        :param class_name: 窗口类名. 此参数是模糊匹配
        :param filter_num: 取值定义如下
                            1 : 匹配窗口标题,参数title有效
                            2 : 匹配窗口类名,参数class_name有效.
                            4 : 只匹配指定父窗口的第一层孩子窗口
                            8 : 匹配所有者窗口为0的窗口,即顶级窗口
                            16 : 匹配可见的窗口
                            这些值可以相加,比如4+8+16就是类似于任务管理器中的窗口列表
        :return: 返回所有匹配的窗口句柄字符串 例如：["123","234"]
                这里注意,返回的数组里的是字符串,要用于使用,比如BindWindow时,还得强制类型转换,比如int(hwnds(0))
        """
        hwnds = self.dm.EnumWindow(parent, title, class_name, filter_num)
        if hwnds != "":
            return hwnds.split(",")
        else:
            return []

    def enum_window_by_process(self, process_name: str = "", title: str = "", class_name: str = "",
                               filter_num: str = "16"):
        """
        根据指定条件,枚举系统中符合条件的窗口,可以枚举到按键自带的无法枚举到的窗口
        :param process_name: 进程映像名.比如(svchost.exe). 此参数是精确匹配,但不区分大小写
        :param title: 窗口标题. 此参数是模糊匹配
        :param class_name: 窗口类名. 此参数是模糊匹配
        :param filter_num: 取值定义如下
                            1 : 匹配窗口标题,参数title有效
                            2 : 匹配窗口类名,参数class_name有效.
                            4 : 只匹配指定父窗口的第一层孩子窗口
                            8 : 匹配所有者窗口为0的窗口,即顶级窗口
                            16 : 匹配可见的窗口
                            这些值可以相加,比如4+8+16就是类似于任务管理器中的窗口列表
        :return: 返回所有匹配的窗口句柄字符串 例如：["123","234"]
                这里注意,返回的数组里的是字符串,要用于使用,比如BindWindow时,还得强制类型转换,比如int(hwnds(0))
        """
        hwnds = self.dm.EnumWindowByProcess(process_name, title, class_name, filter_num)
        if hwnds != "":
            return hwnds.split(",")
        else:
            return []

    def get_client_size(self, hwnd, width, height):
        """
        获取窗口客户区域在屏幕上的位置
        :param hwnd: 返回窗口客户区左上角X坐标
        :param width: 变参指针: 宽度
        :param height: 变参指针: 高度
        :return height, width
        """
        return self.dm.GetClientSize(hwnd, width, height)

    def get_foreground_focus(self) -> int:
        """
        获取顶层活动窗口中具有输入焦点的窗口句柄
        """
        return self.dm.GetForegroundFocus()

    def get_foreground_window(self) -> int:
        """
        获取顶层活动窗口,可以获取到按键自带插件无法获取到的句柄
        """
        return self.dm.GetForegroundWindow()

    def get_mouse_point_window(self) -> int:
        """
        获取鼠标指向的窗口句柄,可以获取到按键自带的插件无法获取到的句柄
        """
        return self.dm.GetMousePointWindow()

    def get_point_window(self, x: int, y: int) -> int:
        """
        获取给定坐标的窗口句柄,可以获取到按键自带的插件无法获取到的句柄
        :param x: 屏幕X坐标
        :param y: 屏幕Y坐标
        """
        return self.dm.GetPointWindow(x, y)

    def get_windows(self, hwnd: int, flag: int) -> int:
        """
        获取给定窗口相关的窗口句柄
        :param hwnd: 指定的窗口句柄
        :param flag: 取值定义如下
                    0 : 获取父窗口
                    1 : 获取第一个儿子窗口
                    2 : 获取First 窗口
                    3 : 获取Last窗口
                    4 : 获取下一个窗口
                    5 : 获取上一个窗口
                    6 : 获取拥有者窗口
                    7 : 获取顶层窗口
        """
        return self.dm.GetWindow(hwnd, flag)

    def get_window_class(self, hwnd: int) -> str:
        """
        取窗口的类名
        :param hwnd: 指定的窗口句柄
        """
        return self.dm.GetWindowClass(hwnd)

    def get_window_process_id(self, hwnd: int) -> int:
        """
        获取指定窗口所在的进程ID.
        :param hwnd: 指定的窗口句柄
        """
        return self.dm.GetWindowProcessId(hwnd)

    def get_window_process_path(self, hwnd: int) -> str:
        """
        获取指定窗口所在的进程的exe文件全路径
        :param hwnd: 指定的窗口句柄
        """
        return self.dm.GetWindowProcessPath(hwnd)

    def get_window_state(self, hwnd: str, flag: int) -> bool:
        """
        获取指定窗口的一些属性
        :param hwnd: 指定的窗口句柄
        :param flag: 取值定义如下
                    0 : 判断窗口是否存在
                    1 : 判断窗口是否处于激活
                    2 : 判断窗口是否可见
                    3 : 判断窗口是否最小化
                    4 : 判断窗口是否最大化
                    5 : 判断窗口是否置顶
                    6 : 判断窗口是否无响应
        """
        return True if self.dm.GetWindowState(hwnd, flag) == 1 else False

    def get_window_title(self, hwnd: str) -> str:
        """
        获取窗口的标题
        :param hwnd: 指定的窗口句柄
        """
        return self.dm.GetWindowTitle(hwnd)

    def move_window(self, hwnd: int, x: int, y: int) -> bool:
        """
        移动指定窗口到指定位置
        :param hwnd: 指定的窗口句柄
        :param x: X坐标
        :param y: Y坐标
        """
        return True if self.dm.MoveWindow(hwnd, x, y) == 1 else False

    def send_paste(self, hwnd: int, content: str) -> bool:
        """
        向指定窗口发送粘贴命令
        :param hwnd: 指定的窗口句柄
        :param content: 粘贴的内容
        """
        self.dm.SetClipboard(content)
        return True if self.dm.endPaste(hwnd) == 1 else False

    def send_string(self, hwnd: int, content: str) -> bool:
        """
        向指定窗口发送文本数据
        :param hwnd: 指定的窗口句柄
        :param content: 发送的文本数据
        :return:
        """
        return True if self.dm.SendString(hwnd, content) == 1 else False

    def send_string_old(self, hwnd: int, content: str) -> bool:
        """
        向指定窗口发送文本数据
        注: 此接口为老的SendString，如果新的SendString不能输入，可以尝试此接口
        :param hwnd: 指定的窗口句柄
        :param content: 发送的文本数据
        :return:
        """
        return True if self.dm.SendString2(hwnd, content) == 1 else False

    def set_client_size(self, hwnd: int, width: int, height: int) -> bool:
        """
        设置窗口客户区域的宽度和高度
        :param hwnd: 指定的窗口句柄
        :param width: 宽度
        :param height: 高度
        """
        return True if self.dm.SetClientSize(hwnd, width, height) == 1 else False

    def set_window_size(self, hwnd: int, width: int, height: int) -> bool:
        """
        设置窗口的大小
        :param hwnd: 指定的窗口句柄
        :param width: 宽度
        :param height: 高度
        """
        return True if self.dm.SetWindowSize(hwnd, width, height) == 1 else False

    def set_window_state(self, hwnd: int, flag: int) -> bool:
        """
        设置窗口的状态
        :param hwnd: 指定的窗口句柄
        :param flag: 取值定义如下
                    0 : 关闭指定窗口
                    1 : 激活指定窗口
                    2 : 最小化指定窗口,但不激活
                    3 : 最小化指定窗口,并释放内存,但同时也会激活窗口.
                    4 : 最大化指定窗口,同时激活窗口. 但如果窗口已经是最大化了，不会激活
                    5 : 恢复指定窗口 ,但不激活
                    6 : 隐藏指定窗口
                    7 : 显示指定窗口
                    8 : 置顶指定窗口
                    9 : 取消置顶指定窗口
                    10 : 禁止指定窗口
                    11 : 取消禁止指定窗口
                    12 : 恢复并激活指定窗口
                    13 : 强制结束窗口所在进程.
        """
        return True if self.dm.SetWindowState(int(hwnd), flag) == 1 else False

    def set_window_title(self, hwnd: int, title: str) -> bool:
        """
        设置窗口的标题
        :param hwnd: 指定的窗口句柄
        :param title: 标题
        :return:
        """
        return True if self.dm.SetWindowText(hwnd, title) == 1 else False
