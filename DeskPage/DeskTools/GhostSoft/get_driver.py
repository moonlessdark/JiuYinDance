from ctypes import WinDLL, c_char_p


def reg_dll(dll_path):
    try:
        dll = WinDLL(dll_path)
        return dll
    except Exception as e:
        return None


class GetGhostDriver:
    dll = None

    def __init__(self, dll_path):
        self.__class__.dll = reg_dll(dll_path)


class SetGhostDriver:
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
        model = self.ghost_driver.GetModel()
        buffer_model = c_char_p(model)
        version_str: str = buffer_model.value.decode('utf-8')
        return version_str

    def get_usb_number(self) -> str:
        """
        获取设备序列号
        :return:
        """
        serial_number = self.ghost_driver.GetSerialNumber()
        sz_buff_serial_number = c_char_p(serial_number)
        return sz_buff_serial_number.value.decode('utf-8')

    def get_usb_version(self) -> str:
        """
        获取设备版本
        :return:
        """
        firmware_version = self.ghost_driver.GetFirmwareVersion()
        sz_buff_firmware_version = c_char_p(firmware_version)
        return sz_buff_firmware_version.value.decode('utf-8')

    def get_usb_list(self) -> str:
        """
        获取设备列表
        :return:
        """
        device_list_by_serial_number = self.ghost_driver.GetDeviceListByModel("")
        sz_buff_device_list_by_serial_number = c_char_p(device_list_by_serial_number)
        return sz_buff_device_list_by_serial_number.value.decode('utf-8')

    def check_usb_connect(self) -> bool:
        """
        检查设备链接状态
        :return:
        """
        return self.ghost_driver.IsDeviceConnected()

    def select_usb_devices(self, device_code) -> int:
        return self.ghost_driver.SelectDeviceBySerialNumber(device_code)

    def click_press_and_release_by_key_name(self, key_str: str) -> bool:
        """
        按下并释放键盘上的键
        :param key_str:
        :return:
        2：表示按键成功
        0：表示按键失败，键无效或设备未执行
        """
        result_int: int = self.ghost_driver.PressAndReleaseKeyByName(key_str)
        return True if result_int > 0 else False

    def click_press_and_release_by_code(self, key_code: int) -> bool:
        """

        :param key_code:
        :return:
        """
        result_int: int = self.ghost_driver.PressAndReleaseKeyByValue(key_code)
        return True if result_int > 0 else False

    def set_press_key_delay(self, min_delay: int, max_delay: int):
        """
        设置按钮直接的随机等待时间
        如果不调用此接口，插件会设置默认值  30-100毫秒之间
        :param min_delay: 最小等待时间，毫秒
        :param max_delay: 最大等待时间，毫秒
        :return:
        """
        result_int: int = self.ghost_driver.SetPressKeyDelay(min_delay, max_delay)
        return True if result_int > 0 else False


class SetGhostBoards(SetGhostDriver):
    def __init__(self):
        super().__init__()
        self.get_ghost_driver(GetGhostDriver.dll)
