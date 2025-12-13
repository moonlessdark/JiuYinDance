import ctypes
import sys

from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(False)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    w.log_print("\n\n更新日期: 2025-12-13\n"
                "更新内容: \n"
                "新增内容: \n"
                "玄机报名时检测当前是否组队\n"
                "每天首次押镖时自动接取每日任务\n")

    w.show()
    app.exec()

