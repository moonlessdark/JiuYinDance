# coding: utf-8
"""
窗口枚举、可见性判断与激活。

激活失败是旧实现的高频问题：SetForegroundWindow 受两条系统规则限制：
1. 前台锁：只有当前前台进程（或刚收到用户输入的进程）才能切换前台窗口；
2. UIPI：低权限进程不能操作高权限窗口。
本模块用 AttachThreadInput 临时共享输入队列绕过前台锁，并用 SwitchToThisWindow
兜底，失败时返回可读原因，便于区分“权限不足”和“前台锁超时”。
"""
from __future__ import annotations

import ctypes
import time
from typing import List, Optional

import psutil
import win32api
import win32con
import win32gui
import win32process

from Core.windows.dpi import is_process_elevated

# 默认目标窗口规则，可由调用方覆盖，便于复用到其他游戏
DEFAULT_TITLE_PREFIX = "九阴真经 "
DEFAULT_PROCESS_NAME = "fxgame.exe"


def get_windows_handle(title_prefix: str = DEFAULT_TITLE_PREFIX,
                       process_name: str = DEFAULT_PROCESS_NAME) -> List[int]:
    """
    枚举所有窗口，过滤出标题以指定前缀开头且进程名匹配的窗口。

    :param title_prefix: 窗口标题前缀
    :param process_name: 进程名，例如 fxgame.exe
    :return: 排序后的窗口句柄列表
    """
    handle_list: List[int] = []
    hwnd_list: List[int] = []
    win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), hwnd_list)
    for handle_id in hwnd_list:
        try:
            main_text: str = win32gui.GetWindowText(handle_id)
            if not main_text.startswith(title_prefix):
                continue

            _thread_id, process_id = win32process.GetWindowThreadProcessId(handle_id)
            process = psutil.Process(process_id)
            if process.name().lower() == process_name.lower():
                handle_list.append(handle_id)
        except (psutil.NoSuchProcess, psutil.AccessDenied, win32gui.error, OSError):
            # 枚举过程中进程可能刚好退出，跳过即可，不能影响其他窗口
            continue
    handle_list.sort()
    return handle_list


def is_window_capturable(hwnd: int) -> bool:
    """
    判断窗口是否可以截图：存在、可见、非最小化。

    BitBlt 无法从最小化窗口获取有效内容，因此这里直接排除。
    """
    try:
        handle_id = int(hwnd)
    except (TypeError, ValueError):
        return False

    try:
        if not win32gui.IsWindow(handle_id):
            return False
        if win32gui.IsIconic(handle_id):
            return False
        if not win32gui.IsWindowVisible(handle_id):
            return False
    except (win32gui.error, OSError):
        return False
    return True


def activate_windows(hwnd: int) -> bool:
    """
    激活窗口（兼容旧调用，只需要成功与否）。

    :param hwnd: 窗口句柄
    :return: 是否成功前台化
    """
    success, _reason = activate_windows_ex(hwnd)
    return success


def activate_windows_ex(hwnd: int) -> tuple[bool, str]:
    """
    激活窗口并返回失败原因。

    实现步骤：
    1. 已在前台直接返回；
    2. 最小化则先恢复，再显示；
    3. AttachThreadInput 共享前台线程输入队列，绕过前台锁；
    4. BringWindowToTop + SetForegroundWindow + SetFocus；
    5. 仍然失败时用 SwitchToThisWindow 兜底；
    6. 给出可读失败原因（权限 / 前台锁）。

    :param hwnd: 窗口句柄
    :return: (是否成功, 中文原因)
    """
    try:
        handle_id = int(hwnd)
    except (TypeError, ValueError):
        return False, "窗口句柄无效"

    if not win32gui.IsWindow(handle_id):
        return False, "窗口不存在或已关闭"

    if win32gui.GetForegroundWindow() == handle_id:
        return True, "窗口已在前台"

    try:
        if win32gui.IsIconic(handle_id):
            win32gui.ShowWindow(handle_id, win32con.SW_RESTORE)
        win32gui.ShowWindow(handle_id, win32con.SW_SHOW)
    except (win32gui.error, OSError):
        pass

    foreground = win32gui.GetForegroundWindow()
    current_thread = win32api.GetCurrentThreadId()
    foreground_thread = 0
    if foreground:
        try:
            foreground_thread, _process_id = win32process.GetWindowThreadProcessId(foreground)
        except (win32gui.error, OSError):
            foreground_thread = 0

    attached = False
    try:
        if foreground_thread and foreground_thread != current_thread:
            attached = bool(ctypes.windll.user32.AttachThreadInput(
                current_thread, foreground_thread, True))
        win32gui.BringWindowToTop(handle_id)
        win32gui.SetForegroundWindow(handle_id)
        if attached:
            try:
                win32gui.SetFocus(handle_id)
            except (win32gui.error, OSError):
                pass
    except (win32gui.error, OSError):
        pass
    finally:
        if attached:
            try:
                ctypes.windll.user32.AttachThreadInput(current_thread, foreground_thread, False)
            except (OSError, AttributeError):
                pass

    time.sleep(0.1)
    if win32gui.GetForegroundWindow() == handle_id:
        return True, "激活成功"

    # 兜底：SwitchToThisWindow 是未文档化接口，但多年保持可用
    try:
        ctypes.windll.user32.SwitchToThisWindow(handle_id, True)
        time.sleep(0.1)
    except (OSError, AttributeError):
        pass
    if win32gui.GetForegroundWindow() == handle_id:
        return True, "通过 SwitchToThisWindow 激活成功"

    return False, describe_activation_failure(handle_id)


def describe_activation_failure(hwnd: int) -> str:
    """
    生成激活失败原因。

    :param hwnd: 目标窗口句柄
    :return: 中文原因描述
    """
    if not win32gui.IsWindow(int(hwnd)):
        return "激活失败：窗口已关闭"

    foreground = win32gui.GetForegroundWindow()
    try:
        foreground_title = win32gui.GetWindowText(foreground)
    except (win32gui.error, OSError):
        foreground_title = str(foreground)

    if not is_process_elevated():
        return ("激活失败：当前进程不是管理员权限。目标窗口权限更高时，"
                "Windows 的 UIPI 机制会拒绝前台切换，请以管理员身份运行本程序")

    return (f"激活失败：系统拒绝前台切换（当前前台窗口：{foreground_title}）。"
            "可能触发了前台锁限制，请稍后重试；若持续失败，请手动点击一次游戏窗口")


def get_foreground_window() -> int:
    """获取当前前台窗口句柄。"""
    return int(win32gui.GetForegroundWindow())


class WindowsHandle:
    """
    窗口操作门面类。

    底层实现是上面的模块函数；保留类形式是为了让业务层可以按实例注入依赖，
    也方便后续替换实现（例如测试时替换成假窗口）。
    """

    @staticmethod
    def get_windows_handle(title_prefix: str = DEFAULT_TITLE_PREFIX,
                           process_name: str = DEFAULT_PROCESS_NAME) -> List[int]:
        return get_windows_handle(title_prefix=title_prefix, process_name=process_name)

    @staticmethod
    def activate_windows(hwnd: int) -> bool:
        return activate_windows(hwnd)

    @staticmethod
    def activate_windows_ex(hwnd: int) -> tuple[bool, str]:
        return activate_windows_ex(hwnd)

    @staticmethod
    def is_window_capturable(hwnd: int) -> bool:
        return is_window_capturable(hwnd)
