import ctypes
import sys
import platform

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
    windows_release: int = int(platform.release())
    # 需要在渲染GUI前执行，False表示不启用获取显示器真是分辨率。得到的结果是缩放分辨率(例如4K进行缩放到150%的分辨率变成了2K)
    try:
        """
        请参考
        https://learn.microsoft.com/zh-cn/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process
        """
        if windows_release >= 8:
            ctypes.windll.shcore.SetProcessDpiAwareness(False)
        else:
            ctypes.windll.user32.SetProcessDpiAware()
    except RuntimeError as e:
        raise e
    finally:

        app = QApplication(sys.argv)
        try:
            main_gui = Dance()
            main_gui.setWindowTitle("摸鱼助手(经典模式)")
            main_gui.show()
        except RuntimeError as e:
            main_gui.print_logs(str(e))
        hot_key = hotKey.HotKey()
        hot_key.ShowWindow.connect(main_gui.hot_key_event)
        hot_key.start()
        app.aboutToQuit.connect(main_gui.on_application_about_to_quit)
        sys.exit(app.exec())
