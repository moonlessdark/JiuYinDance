# coding: utf-8
"""
窗口客户区截图。

相比旧实现的关键改动：
1. 区域截图改为使用客户区 DC（GetDC），坐标直接是客户区坐标，
   不再用 GetWindowRect - GetClientRect 推算标题栏和边框；
2. 修复旧实现中 `-0` 判断恒为真的问题（Python 中 -0 == 0，无法区分）；
3. GDI 资源统一在 finally 中释放，异常分支不泄漏句柄。
"""
from __future__ import annotations

from collections import namedtuple
from ctypes import windll, c_ubyte
from typing import Optional

import numpy as np

from Core.windows.geometry import get_client_size
from Core.windows.window import is_window_capturable

PicCapture = namedtuple("PicCapture", ["pic_content", "pic_width", "pic_height"])


class WindowsCapture:
    """基于 Win32 BitBlt 的窗口客户区截图。"""

    def __init__(self):
        self.GetDC = windll.user32.GetDC
        self.CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
        self.CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
        self.SelectObject = windll.gdi32.SelectObject
        self.BitBlt = windll.gdi32.BitBlt
        self.SRCCOPY = 0x00CC0020
        self.GetBitmapBits = windll.gdi32.GetBitmapBits
        self.DeleteObject = windll.gdi32.DeleteObject
        self.DeleteDC = windll.gdi32.DeleteDC
        self.ReleaseDC = windll.user32.ReleaseDC

    def capture(self, hwnd: int) -> Optional[PicCapture]:
        """
        截取整个客户区。

        :param hwnd: 窗口句柄
        :return: 截图结果（BGRA）；窗口不可见、最小化或截图失败时返回 None
        """
        return self.capture_window_region(hwnd, 0, 0, *get_client_size(hwnd))

    def capture_window_region(self, hwnd: int, x: int, y: int,
                              width: int, height: int) -> Optional[PicCapture]:
        """
        按客户区坐标截取一部分画面。

        坐标约定：
        - x >= 0：从客户区左侧开始；
        - x < 0：按 ``客户区宽度 - 截取宽度 + x`` 计算，兼容旧调用中“靠右截取”的写法；
        - y 同理。

        :param hwnd: 窗口句柄
        :param x: 客户区左上角 x
        :param y: 客户区左上角 y
        :param width: 截取宽度
        :param height: 截取高度
        :return: 截图结果（BGRA）；失败返回 None
        """
        try:
            handle_id = int(hwnd)
            x, y, width, height = int(x), int(y), int(width), int(height)
        except (TypeError, ValueError):
            return None

        if width <= 0 or height <= 0:
            return None
        if not is_window_capturable(handle_id):
            return None

        client_width, client_height = get_client_size(handle_id)
        if client_width <= 0 or client_height <= 0:
            return None

        left = client_width - width + x if x < 0 else x
        top = client_height - height + y if y < 0 else y

        if left < 0 or top < 0 or left + width > client_width or top + height > client_height:
            raise ValueError(
                f"截图区域超出客户区范围：区域=({left},{top},{width},{height})，"
                f"客户区={client_width}x{client_height}")

        return self._capture_region_bitblt(handle_id, left, top, width, height)

    def _capture_region_bitblt(self, hwnd: int, left: int, top: int,
                               width: int, height: int) -> Optional[PicCapture]:
        """
        使用客户区 DC 执行 BitBlt。

        GetDC(hwnd) 的原点就是客户区左上角，因此这里的 left/top 可以直接使用，
        不需要再加标题栏或边框偏移。
        """
        dc = None
        compatible_dc = None
        bitmap = None
        try:
            dc = self.GetDC(hwnd)
            if not dc:
                return None
            compatible_dc = self.CreateCompatibleDC(dc)
            if not compatible_dc:
                return None
            bitmap = self.CreateCompatibleBitmap(dc, width, height)
            if not bitmap:
                return None

            self.SelectObject(compatible_dc, bitmap)
            if not self.BitBlt(compatible_dc, 0, 0, width, height, dc, left, top, self.SRCCOPY):
                return None

            # 截图是 BGRA 排列，因此总元素个数需要乘以 4
            total_bytes = width * height * 4
            buffer = bytearray(total_bytes)
            byte_array = c_ubyte * total_bytes
            if self.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer)) == 0:
                return None

            pic_content = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
            return PicCapture(pic_content, width, height)
        except (OSError, ValueError):
            return None
        finally:
            # 释放顺序与创建顺序相反，保证异常分支也不泄漏 GDI 资源
            if bitmap:
                self.DeleteObject(bitmap)
            if compatible_dc:
                self.DeleteDC(compatible_dc)
            if dc:
                self.ReleaseDC(hwnd, dc)
