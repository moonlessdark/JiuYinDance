import ctypes
import sys

from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(False)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    w.log_print("\n\n更新日期: 2025-10-21\n"
                "更新内容: \n"
                "新增内容: 修复多开开卡后没用成功获取丹药的问题")

    w.show()
    app.exec()

