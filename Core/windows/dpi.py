# coding: utf-8
"""
DPI 感知与窗口 DPI 查询。

为什么需要这一层：
1. 进程 DPI 感知级别决定了 Win32 返回的是逻辑坐标还是物理坐标；
2. 游戏窗口可能是不感知 DPI 的进程，Windows 会对坐标做虚拟化；
3. 多显示器混合 DPI 时，只有 Per-Monitor V2 才能同时保证截图尺寸和点击坐标正确。

统一约定：本模块只负责“设置进程感知级别”和“查询窗口 DPI”，
坐标换算由 Core.windows.geometry 统一处理，业务层不要自己做缩放。
"""
from __future__ import annotations

import ctypes
from typing import Optional

import win32con
import win32gui
import win32print

# SetProcessDpiAwarenessContext 的上下文值
DPI_AWARENESS_CONTEXT_UNAWARE = -1
DPI_AWARENESS_CONTEXT_SYSTEM_AWARE = -2
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = -3
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4

# 旧配置值（app_config.ini 中的 dpi_mode）到感知上下文的映射：
# 0 = 经典模式（不感知，交给系统缩放，保证与游戏缩放设置一致）
# 2 = 极致模式（每显示器感知，物理像素）
_DPI_MODE_TO_CONTEXT = {
    0: DPI_AWARENESS_CONTEXT_UNAWARE,
    2: DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2,
}

# 旧 API shcore.SetProcessDpiAwareness 的取值
_DPI_MODE_TO_SHcore = {
    0: 0,  # PROCESS_DPI_UNAWARE
    1: 1,  # PROCESS_SYSTEM_DPI_AWARE
    2: 2,  # PROCESS_PER_MONITOR_DPI_AWARE
}


def set_process_dpi_awareness(dpi_mode: int = 2) -> str:
    """
    设置进程 DPI 感知级别，必须在创建任何窗口之前调用。

    优先使用 Win10 1703+ 的 SetProcessDpiAwarenessContext（Per-Monitor V2），
    失败后回退到 shcore.SetProcessDpiAwareness，再回退到 SetProcessDPIAware。

    :param dpi_mode: 0=经典模式（不感知），2=极致模式（每显示器 V2）
    :return: 实际生效的 API 名称，用于日志排查
    """
    context = _DPI_MODE_TO_CONTEXT.get(int(dpi_mode), DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)

    user32 = ctypes.windll.user32
    set_context = getattr(user32, "SetProcessDpiAwarenessContext", None)
    if set_context is not None:
        try:
            # 参数是 DPI_AWARENESS_CONTEXT（句柄语义），需要按指针宽度传递
            if set_context(ctypes.c_void_p(context)):
                return "SetProcessDpiAwarenessContext"
        except (AttributeError, OSError):
            pass

    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(_DPI_MODE_TO_SHcore.get(int(dpi_mode), 2)) == 0:
            return "SetProcessDpiAwareness"
    except (AttributeError, OSError):
        pass

    try:
        if user32.SetProcessDPIAware():
            return "SetProcessDPIAware"
    except (AttributeError, OSError):
        pass
    return "unchanged"


def get_window_dpi(hwnd: int) -> int:
    """
    获取窗口所在显示器的 DPI。

    :param hwnd: 窗口句柄
    :return: DPI 值，获取失败时返回 96
    """
    user32 = ctypes.windll.user32
    get_dpi = getattr(user32, "GetDpiForWindow", None)
    if get_dpi is not None:
        try:
            dpi = int(get_dpi(int(hwnd)))
            if dpi > 0:
                return dpi
        except (OSError, ValueError):
            pass

    # 旧系统回退：窗口 DC 的水平 DPI
    hdc = None
    try:
        hdc = win32gui.GetWindowDC(int(hwnd))
        dpi = int(win32print.GetDeviceCaps(hdc, win32con.LOGPIXELSX))
        return dpi if dpi > 0 else 96
    except (win32gui.error, OSError):
        return 96
    finally:
        if hdc:
            win32gui.ReleaseDC(int(hwnd), hdc)


def get_window_scale(hwnd: int) -> float:
    """
    获取窗口所在显示器的缩放比例。

    :param hwnd: 窗口句柄
    :return: 缩放比例，1.0 表示 100%
    """
    return round(get_window_dpi(hwnd) / 96.0, 4)


def get_process_dpi_awareness() -> Optional[int]:
    """
    查询当前进程的 DPI 感知级别。

    :return: 0=unaware, 1=system aware, 2=per-monitor aware；查询失败返回 None
    """
    try:
        awareness = ctypes.c_int()
        if ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness)) == 0:
            return int(awareness.value)
    except (AttributeError, OSError):
        pass
    return None


def is_process_elevated() -> bool:
    """判断当前进程是否以管理员权限运行。"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False
