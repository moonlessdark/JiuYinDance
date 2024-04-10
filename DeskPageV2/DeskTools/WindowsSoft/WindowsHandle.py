from collections import namedtuple
from typing import List

import psutil
import win32api
import win32com
import win32con
import win32gui
import win32process
from win32com import client

PicCapture = namedtuple("PicCapture", ["pic_content", "pic_width", "pic_height"])


class WindowsHandle:
    """
    窗口句柄的获取和激活
    """
    shell = None

    @staticmethod
    def get_windows_handle() -> List[int]:
        """
        通过便利的方式获取所有的窗口id，然后过滤出我要的
        :return:
        """
        handle_list: List[int] = []
        hwnd_list: List[int] = []
        win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), hwnd_list)
        if len(hwnd_list) > 0:
            for handle_id in hwnd_list:
                main_text: str = win32gui.GetWindowText(handle_id)

                # 读取任务进程id
                thread_id, process_id = win32process.GetWindowThreadProcessId(handle_id)
                # Get the process name and executable path
                process: psutil.Process = psutil.Process(process_id)
                process_name: str = process.name()
                if main_text.find("九阴真经 ") == 0 and process_name == 'fxgame.exe':
                    handle_list.append(handle_id)
        handle_list.sort()
        return handle_list

    def activate_windows(self, windows_handle: int) -> bool:
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        return self.activate_windows_1(windows_handle)

    @staticmethod
    def activate_windows_1(windows_handle: int):
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        if windows_handle != win32gui.GetForegroundWindow():
            try:
                win32api.keybd_event(0xC, 0, 0, 0)
                win32gui.ShowWindow(windows_handle, win32con.SW_SHOWNA)
                win32gui.SetForegroundWindow(windows_handle)
            except Exception as e:
                return False
        return True

    @staticmethod
    def activate_windows_2(windows_handle: int):
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        if windows_handle != win32gui.GetForegroundWindow():
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                # input("Press Enter")
                shell.SendKeys(' ')  # Undocks my focus from Python IDLE
                win32gui.SetForegroundWindow(windows_handle)  # It works!
                shell.SendKeys('%')
            except Exception as e:
                return False
        return True

    @staticmethod
    def activate_windows_3(windows_handle: int):
        """
        激活窗口方法3
        注意，此方法完全无效
        :param windows_handle:
        :return:
        """
        try:
            h_fore_wind: str = win32gui.GetForegroundWindow()
            dw_curth_id: str= win32process.GetCurrentProcessId()
            dw_fore_id = win32process.GetWindowThreadProcessId(h_fore_wind, None)
            win32process.AttachThreadInput(dw_curth_id, dw_fore_id, True)
            win32gui.SetWindowPos(windows_handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
            win32gui.SetWindowPos(windows_handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
            win32gui.SetForegroundWindow(windows_handle)
            win32process.AttachThreadInput(dw_curth_id, dw_fore_id, False)
            return True
        except Exception as e:
            return False
