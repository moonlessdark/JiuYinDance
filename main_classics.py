import ctypes
import sys
import platform

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
        main_gui = Dance()
        main_gui.setWindowTitle("JDancing(经典)")
        main_gui.text_browser_print_log.setText("更新日期: 2024-05-20"
                                                "\n注意："
                                                "\n1:游戏客户端设置为【经典模式】，不然无法正常识别到游戏画面。窗口分辨率请确保大于1388*768"
                                                "\n2:本工具需要搭配“幽灵键鼠”使用，请自行购买(淘宝8块钱的那个就可以了)"
                                                "\n3:开始执行后，请不要做其他操作，保持游戏窗口一直显示在最前面"
                                                "\n4:双开时如果激活窗口失败，请尝试以“管理员权限”运行此脚本或修改注册表(请查看帮助说明)"
                                                "\n5:本工具为免费工具，请勿支付金钱购买")

        main_gui.show()
        app.aboutToQuit.connect(main_gui.on_application_about_to_quit)
        sys.exit(app.exec())
