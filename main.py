import sys

from PySide6.QtWidgets import QApplication
from DeskFunc.v2.QtConnect import TaskConnect
from Core.config.paths import PathUtil
from Core.windows.dpi import set_process_dpi_awareness
import configparser
import ctypes
import os


def get_app_config_path() -> str:
    """获取 app_config.ini 的绝对路径，避免受启动工作目录影响。"""
    return os.path.join(PathUtil().get_app_dir(), "app_config.ini")


def load_dpi_config():
    """加载DPI配置"""
    config = configparser.ConfigParser()
    config_file = get_app_config_path()

    if os.path.exists(config_file):
        # 使用 utf-8-sig 兼容记事本保存时可能带上的 BOM
        config.read(config_file, encoding="utf-8-sig")
        return config.getint('display', 'dpi_mode', fallback=2)
    else:
        # 配置文件不存在时弹窗提示用户选择
        return prompt_dpi_mode_selection()


def prompt_dpi_mode_selection() -> int:
    """
    使用 Win32 原生消息框选择 DPI 模式。

    必须在创建 QApplication 之前调用：Qt 初始化时会设置进程 DPI 感知，
    之后再用 SetProcessDpiAwareness 会失败。
    返回 0=经典模式，2=极致模式；取消、关闭或调用失败时统一按经典模式处理。
    """
    MB_YESNOCANCEL = 0x00000003
    MB_ICONWARNING = 0x00000030
    MB_DEFBUTTON1 = 0x00000000
    IDYES = 6
    IDNO = 7

    message = (
        "请选择与游戏一致的窗口缩放模式。\n\n"
        "【是】经典模式（推荐）\n"
        "游戏默认模式，支持全部功能。\n\n"
        "【否】极致模式（不推荐）\n"
        "涉及鼠标的功能可能无法使用。\n\n"
        "模式不一致会导致截图识别和坐标计算出现偏差。\n"
        "查看游戏设置：登录界面 → 右下角“游戏设置” → “游戏窗口缩放设置”。"
    )

    try:
        user32 = ctypes.windll.user32
        user32.MessageBoxW.argtypes = [
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
        user32.MessageBoxW.restype = ctypes.c_int
        result = user32.MessageBoxW(
            None,
            message,
            "九阴日常助手 - 请选择游戏缩放模式",
            MB_YESNOCANCEL | MB_ICONWARNING | MB_DEFBUTTON1,
        )
    except (AttributeError, OSError):
        # 极端情况下弹窗不可用，按经典模式继续启动
        result = IDYES

    mode = 2 if result == IDNO else 0
    save_dpi_config(mode)
    return mode


def save_dpi_config(mode):
    """保存DPI配置"""
    config = configparser.ConfigParser()
    config['display'] = {'dpi_mode': str(mode)}

    with open(get_app_config_path(), "w", encoding="utf-8") as f:
        config.write(f)

def get_current_dpi_mode():
    """获取当前DPI模式"""
    return load_dpi_config()


def restart_application():
    """重启应用程序"""
    import subprocess
    subprocess.Popen([sys.executable] + sys.argv[1:])
    QApplication.quit()


if __name__ == '__main__':

    # 加载配置并设置DPI感知模式（必须在创建任何窗口之前）
    dpi_mode: int = load_dpi_config()
    dpi_api: str = set_process_dpi_awareness(dpi_mode)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    # 可以在界面中显示当前DPI模式
    mode_name = "极致模式" if dpi_mode == 2 else "经典模式"

    w.setWindowTitle(f"九阴日常助手({mode_name})")

    w.log_print(f"当前DPI模式: 【{mode_name}】 (API: {dpi_api})\n"
                "请确保游戏游戏设置与此脚本的DPI缩放设置一致。\n")

    w.log_print(f"更新日期: 2026-10-31\n"
                "更新内容: \n"
                "1、启用 v2 架构：团练授业、上下左右、9点开卡、地图采集、世界竞拍、挑战点兑换书页、清理禁地包裹\n"
                "2、v2 全部功能均为纯模板匹配，不再依赖 OCR\n"
                "3、修复团练授业昼夜切换后识别失效的问题\n"
                "4、支持按鼠标中键停止任务(需以管理员权限运行脚本)")

    w.show()
    app.exec()
