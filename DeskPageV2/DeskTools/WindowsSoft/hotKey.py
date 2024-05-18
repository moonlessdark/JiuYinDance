import win32con
from ctypes import *
from ctypes.wintypes import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

main_key = 192


class HotKey(QThread):
    ShowWindow = Signal(int)

    def __init__(self):
        super(HotKey, self).__init__()
        self.main_key = 0x7B

    def run(self):
        user32 = windll.user32
        while True:
            if not user32.RegisterHotKey(None, 1, win32con.MOD_ALT, self.main_key):  # alt+~
                self.ShowWindow.emit("´íÎó", "È«¾ÖÈÈ¼ü×¢²áÊ§°Ü¡£")
            try:
                msg = MSG()
                if user32.GetMessageA(byref(msg), None, 0, 0) != 0:
                    if msg.message == win32con.WM_HOTKEY:
                        if msg.wParam == win32con.MOD_ALT:
                            self.ShowWindow.emit(msg.lParam)
            finally:
                user32.UnregisterHotKey(None, 1)
