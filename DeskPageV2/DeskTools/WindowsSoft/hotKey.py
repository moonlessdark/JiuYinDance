# -*- coding:utf-8 -*-

import win32con
from ctypes import *
from ctypes.wintypes import *
from PySide6.QtCore import *


class HotKey(QThread):
    ShowWindow = Signal(int)

    def __init__(self):
        super(HotKey, self).__init__()
        self.main_key = 123

    def run(self):
        user32 = windll.user32
        while True:
            if not user32.RegisterHotKey(None, 1, 0, win32con.VK_F11):  # alt+~
                pass
            try:
                msg = MSG()
                if user32.GetMessageA(byref(msg), None, 0, 0) != 0:
                    if msg.message == win32con.WM_HOTKEY:
                        if msg.wParam == win32con.MOD_ALT:
                            self.ShowWindow.emit(msg.lParam)
            finally:
                user32.UnregisterHotKey(None, 1)
