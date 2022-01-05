from ctypes import windll, byref, c_ubyte
from ctypes.wintypes import RECT, HWND
import numpy as np
import win32gui

GetDC = windll.user32.GetDC
CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
GetClientRect = windll.user32.GetClientRect
CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
SelectObject = windll.gdi32.SelectObject
BitBlt = windll.gdi32.BitBlt
SRCCOPY = 0x00CC0020
GetBitmapBits = windll.gdi32.GetBitmapBits
DeleteObject = windll.gdi32.DeleteObject
ReleaseDC = windll.user32.ReleaseDC

# 排除缩放干扰
windll.user32.SetProcessDPIAware()


class windowsCap(object):

    def capture(self, handle: HWND):
        """窗口客户区截图

        Args:
            handle (HWND): 要截图的窗口句柄

        Returns:
            numpy.ndarray: 截图数据
        """
        # 获取窗口客户区的大小
        r = RECT()
        GetClientRect(handle, byref(r))
        # width, height = r.right, r.bottom
        width = 1920
        height = 1020
        # 开始截图
        dc = GetDC(handle)
        cdc = CreateCompatibleDC(dc)
        bitmap = CreateCompatibleBitmap(dc, width, height)
        SelectObject(cdc, bitmap)
        BitBlt(cdc, 0, 0, width, height, dc, 0, 0, SRCCOPY)
        # 截图是BGRA排列，因此总元素个数需要乘以4
        total_bytes = width*height*4
        buffer = bytearray(total_bytes)
        byte_array = c_ubyte*total_bytes
        GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
        DeleteObject(bitmap)
        DeleteObject(cdc)
        ReleaseDC(handle, dc)
        # 返回截图数据为numpy.ndarray
        return np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)

    def get_windows_handle(self):
        """
        查找游戏窗口，只允许双开游戏
        :return:
        """
        handle_list = []
        handle = win32gui.FindWindow("FxMain", None)
        if handle > 0:
            handle_list.append(handle)
            while True:
                handle = win32gui.FindWindowEx(None, handle, "FxMain", None)
                if handle > 0:
                    handle_list.append(handle)
                else:
                    break
        return handle_list


if __name__ == "__main__":
    import cv2  # 197946
    handle = windll.user32.FindWindowW(None, "九阴真经  武侠服专区-侠骨丹心")
    # handle = windll.user32.FindWindowW("FxMain", None)
    # handle = win32gui.FindWindowEx(windll.user32.FindWindowW("FxMain", None), None, "FxMain", None)
    win32gui.SetForegroundWindow(handle)
    image = windowsCap().capture(handle)
    cv2.imshow("Capture Test", image)
    cv2.waitKey()

