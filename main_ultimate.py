import ctypes
import sys
from ctypes import wintypes

from PySide6.QtWidgets import QApplication
from DeskPageV2.DeskFindPic.connect_gui import Dance
from DeskPageV2.DeskTools.WindowsSoft import hotKey


def is_admin():
    # python 提权方法 https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 1:
            return True
        return False
    except Exception as e:
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_gui = Dance()
    main_gui.setWindowTitle("摸鱼助手(极致模式)")
    main_gui.show()
    hot_key = hotKey.HotKey()
    hot_key.ShowWindow.connect(main_gui.hot_key_event)
    hot_key.start()
    app.aboutToQuit.connect(main_gui.on_application_about_to_quit)
    sys.exit(app.exec())
