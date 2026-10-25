# coding: utf-8
"""
窗口几何与坐标映射。

本模块修复了旧 MonitorDisplay 的两个关键问题：
1. 不再用 GetWindowRect - GetClientRect 反推标题栏/边框尺寸。
   客户区原点是系统已知的，直接用 ClientToScreen(hwnd, (0, 0)) 获取，
   这样 DWM 阴影边框、多显示器、窗口贴边、任务栏都不会影响计算。
2. 不再手动乘 DPI 缩放。进程 DPI 感知级别设置正确后，Win32 返回的坐标已经是
   当前感知级别下的正确坐标；再乘一次缩放会导致重复放大。

使用约定：
- 截图坐标 = 客户区坐标，原点为客户区左上角；
- 点击坐标 = 屏幕坐标，必须经过 client_to_screen() 转换；
- 业务层不要自己加减窗口边框或标题栏高度。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import win32api
import win32con
import win32gui

from Core.windows.dpi import get_window_dpi, get_window_scale, is_process_elevated


@dataclass(frozen=True)
class MonitorInfo:
    """一块显示器的信息，坐标均为虚拟桌面坐标（主屏左上为原点，左侧屏 x 可能为负）。"""

    handle: int
    left: int
    top: int
    right: int
    bottom: int
    is_primary: bool

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def list_monitors() -> list[MonitorInfo]:
    """
    枚举所有显示器。

    :return: 显示器列表，按系统枚举顺序
    """
    monitors: list[MonitorInfo] = []
    try:
        for item in win32api.EnumDisplayMonitors():
            handle = item[0]
            info = win32api.GetMonitorInfo(handle)
            # 优先使用完整显示器区域，而不是工作区（工作区会扣掉任务栏）
            left, top, right, bottom = info["Monitor"]
            monitors.append(MonitorInfo(
                handle=int(handle),
                left=int(left), top=int(top), right=int(right), bottom=int(bottom),
                is_primary=bool(info.get("Flags", 0) & 1),  # MONITORINFOF_PRIMARY
            ))
    except (win32gui.error, OSError):
        pass
    return monitors


def get_monitor_from_window(hwnd: int) -> Optional[MonitorInfo]:
    """获取窗口所在显示器。"""
    try:
        handle = win32api.MonitorFromWindow(int(hwnd))
        for monitor in list_monitors():
            if monitor.handle == int(handle):
                return monitor
    except (win32gui.error, OSError):
        pass
    return None


def get_monitor_from_point(x: int, y: int) -> Optional[MonitorInfo]:
    """获取屏幕坐标所在显示器。"""
    try:
        handle = win32api.MonitorFromPoint((int(x), int(y)))
        for monitor in list_monitors():
            if monitor.handle == int(handle):
                return monitor
    except (win32gui.error, OSError):
        pass
    return None


def get_virtual_desktop_bounds() -> tuple[int, int, int, int]:
    """
    获取整个虚拟桌面的边界。

    :return: (左上角 x, 左上角 y, 宽度, 高度)
    """
    return (
        int(win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)),
        int(win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)),
        int(win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)),
        int(win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)),
    )


def is_point_in_virtual_desktop(point: tuple[int, int]) -> bool:
    """
    判断屏幕坐标是否落在虚拟桌面内。

    幽灵键鼠这类硬件注入设备对负坐标、多屏拼接的支持差异较大，
    调用方可以在点击前用本函数做一次校验并记录警告。
    """
    left, top, width, height = get_virtual_desktop_bounds()
    x, y = int(point[0]), int(point[1])
    return left <= x < left + width and top <= y < top + height


def get_client_size(hwnd: int) -> tuple[int, int]:
    """
    获取客户区宽高。

    :return: (宽, 高)；窗口无效时返回 (0, 0)
    """
    try:
        left, top, right, bottom = win32gui.GetClientRect(int(hwnd))
        return max(0, right - left), max(0, bottom - top)
    except (win32gui.error, OSError):
        return 0, 0


def get_client_origin_on_screen(hwnd: int) -> tuple[int, int]:
    """
    获取客户区左上角在虚拟桌面中的坐标。

    这是坐标映射的唯一基准点，不要用窗口 rect + 边框推算。

    :return: (x, y)；窗口无效时返回 (0, 0)
    """
    try:
        return win32gui.ClientToScreen(int(hwnd), (0, 0))
    except (win32gui.error, OSError):
        return 0, 0


def client_to_screen(hwnd: int, point: tuple[float, float]) -> tuple[int, int]:
    """
    客户区坐标 -> 屏幕坐标（鼠标点击使用）。

    :param hwnd: 窗口句柄
    :param point: 客户区坐标 (x, y)
    :return: 虚拟桌面屏幕坐标 (x, y)
    """
    origin_x, origin_y = get_client_origin_on_screen(hwnd)
    return origin_x + int(round(point[0])), origin_y + int(round(point[1]))


def screen_to_client(hwnd: int, point: tuple[float, float]) -> tuple[int, int]:
    """
    屏幕坐标 -> 客户区坐标。

    :param hwnd: 窗口句柄
    :param point: 虚拟桌面屏幕坐标 (x, y)
    :return: 客户区坐标 (x, y)
    """
    try:
        return win32gui.ScreenToClient(int(hwnd), (int(round(point[0])), int(round(point[1]))))
    except (win32gui.error, OSError):
        return 0, 0


def _coordinate_center(coordinate) -> tuple[float, float]:
    """
    兼容两种坐标入参：
    - (x, y)
    - 四个角点 ((x1,y1), (x2,y2), (x3,y3), (x4,y4))，取左上与右下中心
    """
    if len(coordinate) == 2:
        return float(coordinate[0]), float(coordinate[1])
    return (
        (float(coordinate[0][0]) + float(coordinate[3][0])) / 2.0,
        (float(coordinate[0][1]) + float(coordinate[3][1])) / 2.0,
    )


def coordinate_change_from_windows(hwnd: int, coordinate) -> tuple[int, int]:
    """
    客户区坐标 -> 屏幕坐标。

    保留旧函数名和入参语义，内部改为 ClientToScreen，不再推算边框。

    :param hwnd: 游戏窗口句柄
    :param coordinate: 客户区坐标 (x, y) 或四个角点
    :return: 屏幕坐标 (x, y)
    """
    return client_to_screen(hwnd, _coordinate_center(coordinate))


def get_window_dpi_scale(hwnd: int) -> float:
    """获取窗口所在显示器的缩放比例（1.0 = 100%）。"""
    return get_window_scale(hwnd)


def coordinate_change_from_monitor(coordinate: tuple[int, int],
                                   old_monitor_size: tuple[int, int],
                                   new_monitor_size: tuple[int, int]) -> tuple[int, int]:
    """
    按分辨率比例把坐标从一种分辨率映射到另一种分辨率。

    :param coordinate: 原始坐标
    :param old_monitor_size: 原始分辨率 (宽, 高)
    :param new_monitor_size: 目标分辨率 (宽, 高)
    """
    old_width, old_height = old_monitor_size
    new_width, new_height = new_monitor_size
    if old_width <= 0 or old_height <= 0:
        return int(coordinate[0]), int(coordinate[1])
    return int(coordinate[0] * new_width / old_width), int(coordinate[1] * new_height / old_height)


def describe_window_geometry(hwnd: int) -> dict:
    """
    输出窗口几何诊断信息，用于多显示器/DPI 问题实测排查。

    :param hwnd: 窗口句柄
    :return: 可直接打印或写入日志的字典
    """
    client_width, client_height = get_client_size(hwnd)
    origin_x, origin_y = get_client_origin_on_screen(hwnd)
    try:
        window_rect = win32gui.GetWindowRect(int(hwnd))
    except (win32gui.error, OSError):
        window_rect = (0, 0, 0, 0)

    monitor = get_monitor_from_window(hwnd)
    return {
        "hwnd": int(hwnd),
        "client_size": (client_width, client_height),
        "client_origin": (origin_x, origin_y),
        "window_rect": tuple(window_rect),
        "dpi": get_window_dpi(hwnd),
        "scale": get_window_scale(hwnd),
        "monitor": None if monitor is None else {
            "handle": monitor.handle,
            "rect": (monitor.left, monitor.top, monitor.right, monitor.bottom),
            "primary": monitor.is_primary,
        },
        "virtual_desktop": get_virtual_desktop_bounds(),
        "elevated": is_process_elevated(),
    }
