import ctypes
import sys

from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(False)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    w.log_print("\n\n更新日期: 2025-09-10\n"
                "更新内容: \n"
                "新增内容: 新增漠西-挖宝指引")

    w.show()
    app.exec()

