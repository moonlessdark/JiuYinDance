import ctypes
import sys

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect


if __name__ == '__main__':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("JiuYinDancing")
    ctypes.windll.shcore.SetProcessDpiAwareness(False)  # 对应游戏的经典模式，如果是极致模式，请设置为True
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    w.log_print("\n\n更新日期: 2025-12-21\n"
                "更新内容: \n"
                "   新增农夫自动种植(测试版)\n")
    w.show()
    app.exec()
