#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows related utilities.
"""
import ctypes
import ctypes.wintypes
import logging
import os
from ctypes import *
from ctypes import (
    POINTER,
    Structure
)
from ctypes.wintypes import (
    DWORD,
    LONG,
    WORD,
    BYTE,
    RECT,
    UINT,
    ATOM
)

import win32api
import win32com
import win32con
import win32gui
import win32process
import win32security
from win32api import (
    GetCurrentThreadId
)
from win32con import *
from win32gui import *
from win32process import (
    AttachThreadInput
)


class tagTITLEBARINFO(Structure):
    pass


tagTITLEBARINFO._fields_ = [
    ('cbSize', DWORD),
    ('rcTitleBar', RECT),
    ('rgstate', DWORD * 6),
]
PTITLEBARINFO = POINTER(tagTITLEBARINFO)
LPTITLEBARINFO = POINTER(tagTITLEBARINFO)
TITLEBARINFO = tagTITLEBARINFO

ASFW_ANY = -1

GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
AllowSetForegroundWindow = windll.user32.AllowSetForegroundWindow


def SetForegroundWindowInternal(hwnd):
    if not IsWindow(hwnd):
        return

    # relation time of SetForegroundWindow lock
    lockTimeOut = 0
    hCurrWnd = GetForegroundWindow()
    dwThisTID = GetCurrentThreadId()
    dwCurrTID = GetWindowThreadProcessId(hCurrWnd, 0)

    # we need to bypass some limitations from Microsoft :)
    if dwThisTID != dwCurrTID:
        AttachThreadInput(dwThisTID, dwCurrTID, TRUE)

        # SystemParametersInfo(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, SPIF_SENDWININICHANGE | SPIF_UPDATEINIFILE)

        AllowSetForegroundWindow(ASFW_ANY)
    shell = win32com.client.Dispatch("WScript.Shell")
    # input("Press Enter")
    shell.SendKeys(' ')  # Undocks my focus from Python IDLE
    win32gui.SetForegroundWindow(hwnd)  # It works!
    shell.SendKeys('%')

    # ySetForegroundWindow(hwnd)

    if dwThisTID != dwCurrTID:
        AttachThreadInput(dwThisTID, dwCurrTID, FALSE)


def AdjustPrivilege(priv, enable=1):
    # Get the process token.
    flags = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
    htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
    # Get the ID for the system shutdown privilege.
    id = win32security.LookupPrivilegeValue(None, priv)
    # Now obtain the privilege for this process.
    # Create a list of the privileges to be added.
    if enable:
        newPrivileges = [(id, win32con.SE_PRIVILEGE_ENABLED)]
    else:
        newPrivileges = [(id, 0)]
    # and make the adjustment.
    win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)


def elevate():
    pid = os.getpid()
    phandle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
    token_handle = win32security.OpenProcessToken(phandle, win32con.TOKEN_ALL_ACCESS)
    if token_handle == 0:
        # print('提取令牌失败')
        pass
    else:
        Luid = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        if Luid == 0:
            # print('Luid获取失败')
            pass
        else:
            new_token_pricileges = [(Luid, win32security.SE_PRIVILEGE_ENABLED)]
            i = win32security.AdjustTokenPrivileges(token_handle, 0, new_token_pricileges)
            if i == 0:
                pass
                # print('提权失败')
            else:
                pass
                # print('succ')
    win32api.CloseHandle(token_handle)


def goto(hwnd):
    # _, pid = win32process.GetWindowThreadProcessId(hwnd)
    # shell = win32com.client.Dispatch('WScript.Shell')
    # shell.AppActivate(pid)
    # shell.SendKeys(r'(% )x')
    _old(hwnd)


def _old(hwnd):
    """So ugly here..."""
    if not win32gui.IsWindow(hwnd):
        return

    fgwin = win32gui.GetForegroundWindow()
    fg, fp = win32process.GetWindowThreadProcessId(fgwin)
    current = win32api.GetCurrentThreadId()

    try:
        attached = False
        if current != fg and fg:
            try:
                attached = win32process.AttachThreadInput(fg, current, True)
            except:
                pass
            # AllowSetForegroundWindow(ASFW_ANY)
        _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)
        # to show window owned by admin process when running in user process
        # see http://msdn.microsoft.com/en-us/library/windows/desktop/ms633548(v=vs.85).aspx
        # for details
        if showCmd == SW_SHOWMINIMIZED:
            # win32gui.ShowWindow(hwnd, SW_RESTORE)
            win32api.SendMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
        else:
            # win32gui.ShowWindow(hwnd, SW_SHOW)
            win32api.SendMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SW_SHOW, 0)

        for fn in [
            win32gui.BringWindowToTop,
            win32gui.SetForegroundWindow,
            win32gui.SetActiveWindow,
            win32gui.SetFocus
        ]:
            try:
                fn(hwnd)
            except Exception as e:
                logging.error(str(e))
    except Exception as e:
        logging.error(str(e))
    finally:
        if attached:
            win32process.AttachThreadInput(fg, win32api.GetCurrentThreadId(), False)
        # else:
        # win32gui.SetForegroundWindow(hwnd)


def gotold(hwnd):
    if not win32gui.IsWindow(hwnd):
        return

    _, showCmd, _, _, _ = win32gui.GetWindowPlacement(hwnd)

    if showCmd == SW_SHOWMINIMIZED:
        win32gui.ShowWindow(hwnd, SW_RESTORE)
    else:
        win32gui.ShowWindow(hwnd, SW_SHOW)

    win32gui.SetForegroundWindow(hwnd)
    win32gui.SetActiveWindow(hwnd)


def is_alt_tab_window(hwnd):
    """Check whether a window is shown in alt-tab.

    See http://stackoverflow.com/a/7292674/238472 for details.
    """
    if not win32gui.IsWindowVisible(hwnd) or not win32gui.IsWindow(hwnd):
        return False

    hwnd_walk = win32con.NULL
    hwnd_try = ctypes.windll.user32.GetAncestor(hwnd, win32con.GA_ROOTOWNER)
    while hwnd_try != hwnd_walk:
        hwnd_walk = hwnd_try
        hwnd_try = ctypes.windll.user32.GetLastActivePopup(hwnd_walk)
        if win32gui.IsWindowVisible(hwnd_try):
            break

    if hwnd_walk != hwnd:
        return False

    # the following removes some task tray programs and "Program Manager"
    ti = TITLEBARINFO()
    ti.cbSize = ctypes.sizeof(ti)
    ctypes.windll.user32.GetTitleBarInfo(hwnd, ctypes.byref(ti))
    if ti.rgstate[0] & win32con.STATE_SYSTEM_INVISIBLE:
        return False

    # Tool windows should not be displayed either, these do not appear in the
    # task bar.
    if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
        return False

    pwi = WINDOWINFO()
    windll.user32.GetWindowInfo(hwnd, byref(pwi))
    # A top-level window created with this style does not become the foreground
    # window when the user clicks it. The system does not bring this window to
    # the foreground when the user minimizes or closes the foreground window.
    # The window does not appear on the taskbar by default.
    if pwi.dwExStyle & win32con.WS_EX_NOACTIVATE:
        return False

    return True


def window_title(hwnd):
    return win32gui.GetWindowText(hwnd)


class tagBITMAPINFOHEADER(Structure):
    pass


tagBITMAPINFOHEADER._fields_ = [
    ('biSize', DWORD),
    ('biWidth', LONG),
    ('biHeight', LONG),
    ('biPlanes', WORD),
    ('biBitCount', WORD),
    ('biCompression', DWORD),
    ('biSizeImage', DWORD),
    ('biXPelsPerMeter', LONG),
    ('biYPelsPerMeter', LONG),
    ('biClrUsed', DWORD),
    ('biClrImportant', DWORD),
]

PBITMAPINFOHEADER = POINTER(tagBITMAPINFOHEADER)
BITMAPINFOHEADER = tagBITMAPINFOHEADER
LPBITMAPINFOHEADER = POINTER(tagBITMAPINFOHEADER)


class tagRGBQUAD(Structure):
    pass


tagRGBQUAD._fields_ = [
    ('rgbBlue', BYTE),
    ('rgbGreen', BYTE),
    ('rgbRed', BYTE),
    ('rgbReserved', BYTE),
]

RGBQUAD = tagRGBQUAD
LPRGBQUAD = POINTER(RGBQUAD)


class tagBITMAPINFO(Structure):
    pass


tagBITMAPINFO._fields_ = [
    ('bmiHeader', BITMAPINFOHEADER),
    ('bmiColors', RGBQUAD * 1),
]

PBITMAPINFO = POINTER(tagBITMAPINFO)
LPBITMAPINFO = POINTER(tagBITMAPINFO)
BITMAPINFO = tagBITMAPINFO


class tagWINDOWINFO(Structure):

    def __str__(self):
        return '\n'.join([key + ':' + str(getattr(self, key)) for key, value in self._fields_])


tagWINDOWINFO._fields_ = [
    ('cbSize', DWORD),
    ('rcWindow', RECT),
    ('rcClient', RECT),
    ('dwStyle', DWORD),
    ('dwExStyle', DWORD),
    ('dwWindowStatus', DWORD),
    ('cxWindowBorders', UINT),
    ('cyWindowBorders', UINT),
    ('atomWindowType', ATOM),
    ('wCreatorVersion', WORD),
]
WINDOWINFO = tagWINDOWINFO
LPWINDOWINFO = POINTER(tagWINDOWINFO)
PWINDOWINFO = POINTER(tagWINDOWINFO)


def top_level_windows():
    """ Returns the top level windows in a list of hwnds."""
    windows = []
    win32gui.EnumWindows(_window_enum_top_level, windows)
    return windows


def _window_enum_top_level(hwnd, windows):
    """ Window Enum function for getTopLevelWindows """
    # if win32gui.GetParent(hwnd) == 0 and title != '':
    if is_alt_tab_window(hwnd):
        windows.append(hwnd)
