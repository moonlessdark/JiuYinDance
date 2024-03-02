import ctypes
import sys
from ctypes import wintypes

from PySide6.QtWidgets import QApplication
from DeskPageV2.DeskFindPic.connect_gui import Dance


def is_admin():
    # python 提权方法 https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 1:
            return True
        return False
    except Exception as e:
        return False


if __name__ == '__main__':

    # 需要在渲染GUI前执行，False表示不启用获取显示器真是分辨率。得到的结果是缩放分辨率(例如4K进行缩放到150%的分辨率变成了2K)
    ctypes.windll.user32.SetThreadDpiAwarenessContext(wintypes.HANDLE(-2))  # Toggle ON
    # ctypes.windll.user32.SetThreadDpiAwarenessContext(wintypes.HANDLE(-1))  # Toggle OFF
    app = QApplication(sys.argv)
    main_gui = Dance()
    main_gui.show()
    sys.exit(app.exec())
