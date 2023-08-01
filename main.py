import ctypes
import sys

from PySide2 import QtCore
from PySide2.QtWidgets import QApplication

from DeskPage.DeskGUIConnect.connect_gui import Dance


def is_admin():
    # python 提权方法 https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 1:
            return True
        return False
    except Exception as e:
        return False


if __name__ == '__main__':

    if is_admin():
        try:
            # >= win8.1
            # 需要在渲染GUI前执行，False表示不启用获取显示器真是分辨率。得到的结果是缩放分辨率(例如4K进行缩放到150%的分辨率变成了2K)
            ctypes.windll.shcore.SetProcessDpiAwareness(False)
        except:
            # win7
            ctypes.windll.user32.SetProcessDpiAware()
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        app = QApplication(sys.argv)
        main_gui = Dance()
        main_gui.show()
        sys.exit(app.exec_())
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 0)  # pyinstaller 打包模式
        # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 0)  # 调试模式