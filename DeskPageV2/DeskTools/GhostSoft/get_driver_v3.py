import collections
from ctypes import c_char_p, windll


def reg_dll(dll_path: str):
    """
    加载驱动
    :param dll_path:
    :return:
    """
    try:
        dll = windll.LoadLibrary(dll_path)
        dll.getmodel.restype = c_char_p
        dll.getserialnumber.restype = c_char_p
        dll.getproductiondate.restype = c_char_p
        dll.getfirmwareversion.restype = c_char_p
        return dll
    except Exception as e:
        return None


class GetGhostDriver:
    dll = None

    def __init__(self, dll_path):
        self.__class__.dll = reg_dll(dll_path)


class SetGhostDriver:
    """
    驱动设置
    """

    def __init__(self):
        self.ghost_driver = None

    def get_ghost_driver(self, driver_dll):
        """

        :param driver_dll: 已经初始化好的驱动对象
        :return:
        """
        if self.ghost_driver is None:
            self.ghost_driver = driver_dll

    def get_usb_model(self) -> str:
        """
        获取设备型号
        :return:
        """
        model: bytes = self.ghost_driver.getmodel()
        return model.decode("utf-8")

    def get_usb_number(self) -> str:
        """
        获取设备序列号
        :return: ""：为空表示当前未连接设备
                "xxx"：非空表示当前连接设备的序列号
        """
        serial_number: bytes = self.ghost_driver.getserialnumber()
        return serial_number.decode("utf-8")

    def get_usb_version(self) -> str:
        """
        获取设备版本
        :return:
        """
        firmware_version: bytes = self.ghost_driver.getfirmwareversion()
        return firmware_version.decode("utf-8")

    def check_usb_connect(self) -> bool:
        """
        检查设备链接状态
        :return:
        """
        result_int: int = self.ghost_driver.isconnected()
        return True if result_int > 0 else False

    def open_device(self, device_index: int = 0) -> bool:
        """
        打开设备
        从3.0开始需要手动打开设备
        :param device_index: 设备序列号，默认0，表示读取到的第一个设备
        :return:
        """
        if self.check_usb_connect() is False:
            result_int: int = self.ghost_driver.opendevice(device_index)
            return True if result_int > 0 else False
        return True

    def close_device(self):
        """
        关闭usb设备
        :return:
        """
        result_int: int = self.ghost_driver.closedevice()
        return True if result_int > 0 else False

    def reset_device(self):
        """
        设备重启
        会断开当前设备与计算机的连接并重新连接计算机，也会关闭当前设备，需要等待设备连接计算机成功后再次调用opendevice打开设备
        :return:
        """
        result_int: int = self.ghost_driver.resetdevice()
        return True if result_int > 0 else False


class SetGhostBoards(SetGhostDriver):
    """
    操作键盘
    """

    def __init__(self):
        super().__init__()
        self.get_ghost_driver(GetGhostDriver.dll)

    def click_press_and_release_by_key_name(self, key_str: str) -> bool:
        """
        按下并释放键盘上的键
        :param key_str: 按键字符,不区分大小写
        :return:
        """
        result_int: int = self.ghost_driver.pressandreleasekeybyname(key_str)
        return True if result_int > 0 else False

    def click_press_and_release_by_code(self, key_code: int) -> bool:
        """
        按下并释放键盘上的键
        :param key_code: 按键code
        :return:
        """
        result_int: int = self.ghost_driver.pressandreleasekeybyvalue(key_code)
        return True if result_int > 0 else False

    def click_all_press_and_release_by_key_name(self, key_str_list: list) -> bool:
        """
        按下多个组合键，并释放
        :param key_str_list:
        :return:
        """
        for key in key_str_list:
            self.ghost_driver.presskeybyname(key)
        result_int: int = self.ghost_driver.releaseallkey()
        return True if result_int > 0 else False

    def click_all_press_and_release_by_key_code(self, key_code_list: list) -> bool:
        """
        按下多个组合键，并释放
        :param key_code_list:
        :return:
        """
        for key in key_code_list:
            self.ghost_driver.presskeybyvalue(key)
        result_int: int = self.ghost_driver.releaseallkey()
        return True if result_int > 0 else False

    def set_press_key_delay(self, min_delay: int, max_delay: int):
        """
        设置按钮直接的随机等待时间
        如果不调用此接口，插件会设置默认值  30-100毫秒之间
        :param min_delay: 最小等待时间，毫秒
        :param max_delay: 最大等待时间，毫秒
        :return:
        """
        result_int: int = self.ghost_driver.setpresskeydelay(min_delay, max_delay)
        return True if result_int > 0 else False


class SetGhostMouse(SetGhostDriver):
    """
    操作鼠标
    """

    def __init__(self):
        super().__init__()
        self.get_ghost_driver(GetGhostDriver.dll)

    def click_mouse_left_button(self):
        """
        点击鼠标左键
        :return:
        """
        result_int: int = self.ghost_driver.pressandreleasemousebutton(1)
        return True if result_int > 0 else False

    def click_mouse_right_button(self):
        """
        点击鼠标右键
        :return:
        """
        result_int: int = self.ghost_driver.pressandreleasemousebutton(3)
        return True if result_int > 0 else False

    def click_mouse_middle_button(self):
        """
        点击鼠标中键
        :return:
        """
        result_int: int = self.ghost_driver.pressandreleasemousebutton(2)
        return True if result_int > 0 else False

    def move_mouse_to(self, x: int, y: int):
        """
        移动鼠标到指定的位置
        从当前位置移动鼠标到指定的坐标，通过多次调用相对移动实现，有轨迹，不限移动范围，
        可通过 setmousemovementdelay 设置两次相对移动之间的随机延时，屏幕左上角坐标为0,0，右下角坐标为屏幕分辨率值减1，
        如800*600的屏幕分辨率有效坐标范围为0,0~799,599
        :param x: 整数类型，屏幕的X坐标，取值范围为正整数
        :param y: 整数类型，屏幕的Y坐标，取值范围为正整数
        :return:
        """
        result_int: int = self.ghost_driver.movemouseto(x, y)
        return True if result_int > 0 else False

    def move_mouse_relative(self, x: int, y: int):
        """
        相对于当前位置移动X、Y坐标，瞬间移动，无轨迹，但是单次移动范围受限于鼠标硬件设置
        :param x: 整数类型，水平移动距离，取值范围为-127~+127，正数为向右移动，负数为向左移动
        :param y: 整数类型，垂直移动距离，取值范围为-127~+127，正数为向下移动，负数为向上移动
        :return:
        """
        result_int: int = self.ghost_driver.movemouserelative(x, y)
        return True if result_int > 0 else False

    def move_mouse_wheel(self, z: int):
        """
        移动鼠标滚轮，可上下滚动指定幅度的值
        :param z: 整数类型，鼠标滚轮移动距离，取值范围为-127~+127，正数向上移动，负数向下移动
        :return:
        """
        result_int: int = self.ghost_driver.movemousewheel(z)
        return True if result_int > 0 else False

    def get_mouse_x_y(self):
        """
        获取鼠标当前位置坐标，对于单接口（单头）设备，是直接通过系统API获得鼠标位置，是即时位置，对于多接口（多头）设备，是从硬件获得被控端鼠标置，
        该位置为记忆位置（并非即时获取）
        :return: 大于等于0：表示获取成功
                -1：表示获取失败，位置未知

        """
        position = collections.namedtuple('position', ['x', 'y'])
        result_int_x: int = self.ghost_driver.getmousex()
        result_int_y: int = self.ghost_driver.getmousey()
        position(result_int_x, result_int_y)
        return position

    def set_mouse_position(self, x: int, y: int):
        """
        对于单接口（单头）设备，效果等同于movemouseto，对于多接口（多头）设备，有两种情况，如果被控端设备不支持绝对值鼠标，则采用复位移动，
        即先把鼠标移动到0,0位置，然后再从0,0位置移动到指定坐标，如果被控端设备支持绝值对鼠标，则使用绝对移动，瞬间移到目标位置，
        调用该接口后被控端鼠标当前位置即为设定位置
        :param x: 整数类型，屏幕的X坐标，取值范围为正整数
        :param y: 整数类型，屏幕的Y坐标，取值范围为正整数
        :return:
        """
        result_int: int = self.ghost_driver.setmouseposition(x, y)
        return True if result_int > 0 else False

    def set_mouse_click_delay(self, min_delay: int = 30, max_delay: int = 100):
        """
        设置鼠标键按下与释放之间的随机延时，用于pressandreleasemousebutton接口的按下延随机延时时间，该功能无记忆，软件每次运行都要重新设置，
        否则将使用默认值
        :param min_delay: 整数类型，最小延时时间，单位毫秒，默认 30
        :param max_delay: 整数类型，最大延时时间，单位毫秒，默认 100
        :return:
        """
        result_int: int = self.ghost_driver.setpressmousebuttondelay(min_delay, max_delay)
        return True if result_int > 0 else False

    def set_mouse_move_delay(self, min_delay: int = 4, max_delay: int = 8):
        """
        设置鼠标每两次移动之间的间隔时间，用于movemouseto和setmouseposition接口，该功能无记忆，软件每次运行都要重新设置，否则将使用默认值
        :param min_delay: 整数类型，最小延时时间，单位毫秒，默认 4
        :param max_delay: 整数类型，最大延时时间，单位毫秒，默认 8
        :return:
        """
        result_int: int = self.ghost_driver.setmousemovementdelay(min_delay, max_delay)
        return True if result_int > 0 else False

    def set_mouse_movement_speed(self, speed_value: int = 7):
        """
        设置移动鼠标到指定坐标时的移动幅度，用于调节移动次数和时间，尽量模拟人工效果，移动速度分为10个等级，等级越高移动速度越快，
        该功能无记忆，软件每次运行都要重新设置，否则将使用默认值
        :param speed_value: 整数类型，移动速度，取值范围1-10，其他值无效，默认 7
        :return:
        """
        speed_value = 10 if speed_value > 10 else 1 if speed_value < 1 else 1
        result_int: int = self.ghost_driver.setmousemovementspeed(speed_value)
        return True if result_int > 0 else False
