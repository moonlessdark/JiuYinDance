import ctypes
import sys
from PyQt5 import QtWidgets, QtCore
from gui.connect.connect_gui import mainUI


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        return False


if __name__ == '__main__':
    if is_admin():
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        app = QtWidgets.QApplication(sys.argv)
        main_gui = mainUI()
        main_gui.show()
        sys.exit(app.exec_())
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
