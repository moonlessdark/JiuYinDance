"""
本模块方法方法请参考
https://learn.microsoft.com/zh-cn/windows/win32/gdi/multiple-display-monitors-functions
"""
import ctypes
import ctypes.wintypes
from collections import namedtuple
from ctypes import windll, c_ubyte, wintypes, pointer, byref, sizeof
import win32api
import win32con
import win32gui
import win32print
from screeninfo import get_monitors
from typing import List


monitorSize = namedtuple("monitorSize", ["windows_desk_handle", "width", "height", "x", "y", "is_primary"])


def display_monitor_detection(scale: bool) -> List[monitorSize]:
    """
    检测显示器信息，
    :param scale: 是否返回完整的分辨率

    monitorSize.windows_desk_handle: 桌面句柄
    width，height: 该显示器桌面的宽高
    x, y: 该桌面的左上角起始坐标，如果 x 是负数，说明这个桌面位置主屏幕的左侧
    is_primary: 是否为主屏幕

    :return:
    """
    monitors = win32api.EnumDisplayMonitors()
    monitors_scale = get_monitors()
    monitor_size_list: list = []
    for m, mc in zip(monitors, monitors_scale):
        windows_desk_handle: int = m[0].handle
        is_primary: bool = mc.is_primary
        if scale:
            """
            如果需要完整未进行缩放的真实分辨率
            """
            width: int = abs(mc.width)
            height: int = abs(mc.height)
            x: int = mc.x
            y: int = mc.y
        else:
            width: int = abs(m[2][0]) if abs(m[2][0]) > 0 else abs(m[2][2])
            height: int = abs(m[2][3])
            x: int = m[2][0]
            y: int = m[2][1]
        ms = monitorSize(windows_desk_handle=windows_desk_handle, width=width, height=height, x=x, y=y,
                         is_primary=is_primary)
        monitor_size_list.append(ms)
    return monitor_size_list


def display_windows_detection(hwnd) -> tuple:
    """
    检测窗口大小。
    如果该窗口是
    :param hwnd:
    :return:
    """
    handle = int(hwnd)
    try:
        f = ctypes.windll.dwmapi.DwmGetWindowAttribute
    except WindowsError as e:
        f = None
    if f:
        rect = ctypes.wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        f(ctypes.wintypes.HWND(handle),
          ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
          ctypes.byref(rect),
          ctypes.sizeof(rect)
          )
        return (rect.left, rect.top), (rect.right, rect.bottom)


def display_windows_border_size(hwnd):
    """
    窗口的边框大小
    """
    # 获取标题栏的高度
    title_bar_height = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)

    # 获取标题栏的宽度
    title_bar_width = win32api.GetSystemMetrics(win32con.SM_CXFRAME) + win32api.GetSystemMetrics(win32con.SM_CXSIZE)

    return title_bar_width, title_bar_height


def get_window_dpi_scale(hwnd: int) -> float:
    """
    计算目标窗口所在的屏幕的缩放比例
    :param hwnd: 目标窗口句柄
    :return:
    """
    try:
        # 获取窗口的设备上下文
        hdc = win32gui.GetWindowDC(hwnd)
        # 获取缩放比例
        dpi = win32print.GetDeviceCaps(hdc, win32con.LOGPIXELSX)
        scale: float = dpi / 96.0
        return scale
    except Exception as e:
        raise RuntimeError(f"Error getting DPI scale: {e}")


def get_monitor_from_window(hwnd) -> int or None:
    """
    获取指定的窗口句柄所在的桌面handle。
    :param hwnd: 该桌面打开的程序的句柄，不能是窗口本身
    :return:
    """
    windows_desk_handle = None
    windows_desk = win32api.MonitorFromWindow(hwnd)
    if windows_desk is not None:
        windows_desk_handle = windows_desk.handle
    return windows_desk_handle


def get_monitor_from_point(x: int, y: int) -> int or None:
    """
    获取指定坐标的是位于哪个显示器的handle
    :param x: x 坐标
    :param y: y 坐标
    :return:
    """
    windows_desk_handle = None
    windows_desk = win32api.MonitorFromPoint((x, y))
    if windows_desk is not None:
        windows_desk_handle = windows_desk.handle
    return windows_desk_handle


def coordinate_change_from_monitor(coordinate: tuple, old_monitor_size: tuple, new_monitor_size: tuple) -> tuple:
    """
    坐标映射。  \n
    例如：将 1366*768分辨率的 坐标(50, 50) 映射到 1980*1080对应的位置。 \n
    从A映射到B，A不等于B \n
    注意，这是单显示器处理，多显示器的组合分辨率(x轴可能为负数，即坐标在主显示器的左侧)可能有异常. \n
    参考链接：https://blog.csdn.net/weixin_38940097/article/details/130314665
    :param coordinate: 需要映射的坐标 (x, y)
    :param old_monitor_size: 当前窗口的宽高 (width, height)
    :param new_monitor_size: 需要转换的宽高 (width, height)
    :return:
    """
    old_width: int = old_monitor_size[0]
    old_height: int = old_monitor_size[1]

    new_width: int = new_monitor_size[0]
    new_height: int = new_monitor_size[1]

    w_scale: float = round(new_width/old_width, 2)
    h_scale: float = round(new_height/old_height, 2)

    source_x = coordinate[0]
    source_y = coordinate[1]

    if source_x < 0:
        """
        坐标在主显示器左侧
        """
        raise RuntimeError("目标坐标在主显示器左侧，请先预处理坐标后再调用本方法")
    tag_x: int = int(source_x * w_scale)
    tag_y: int = int(source_y * h_scale)
    return tag_x, tag_y


def coordinate_change_from_windows(hwnd: int, coordinate: tuple or list):
    """
    坐标映射，从游戏窗口中的某个坐标映射到屏幕显示器上，用于鼠标点击
    :param hwnd: 游戏窗口所句柄，用于获取桌面所在的尺寸
    :param coordinate: 在游戏窗口中获取的坐标（x, y）
    :return:
    """

    def client_to_screen(hwnd_id: int, x, y):
        """
        映射为桌面坐标
        """
        hwnd_id = int(hwnd_id)
        rec = win32gui.ClientToScreen(hwnd_id, (x, y))
        return rec

    # 获取中心点坐标
    if len(coordinate) == 2:
        """
        如果是已经处理好的坐标 （X，Y）
        """
        x_center = int((coordinate[0]))
        y_center = int((coordinate[1]))
    else:
        x_center = int((coordinate[0][0] + coordinate[3][0]) // 2)
        y_center = int((coordinate[0][1] + coordinate[3][1]) // 2)

    rs = client_to_screen(hwnd, x_center, y_center)
    return rs






if __name__ == '__main__':
    # hwnds = 460560
    # import ctypes
    # from ctypes import windll, c_ubyte, wintypes, pointer, byref, sizeof
    # print(display_detection(True))
    # # print(get_monitor_from_window(hwnds))
    # # print(get_monitor_from_point(991, 1))
    # # print(get_window_dpi_scale(65537))
    #
    # # rect = wintypes.RECT()
    # # ctypes.windll.user32.GetWindowRect(hwnds, pointer(rect))
    # # ss = [[rect.left, rect.top], [rect.left, rect.bottom], [rect.right, rect.top], [rect.right, rect.bottom]]
    # # print(ss)
    # # pyautogui.moveTo(rect.left, rect.top, duration=2)
    pass
