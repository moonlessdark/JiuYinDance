from ctypes import windll, byref, c_ubyte
from ctypes.wintypes import RECT, HWND
# import win32gui
from numpy import frombuffer, uint8

# GetDC = windll.user32.GetDC
# CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
# GetClientRect = windll.user32.GetClientRect
# CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
# SelectObject = windll.gdi32.SelectObject
# BitBlt = windll.gdi32.BitBlt
# SRCCOPY = 0x00CC0020
# GetBitmapBits = windll.gdi32.GetBitmapBits
# DeleteObject = windll.gdi32.DeleteObject
# ReleaseDC = windll.user32.ReleaseDC
#
# # 排除缩放干扰
# windll.user32.SetProcessDPIAware()


class windowsCap:

    def __init__(self):
        self.GetDC = windll.user32.GetDC
        self.CreateCompatibleDC = windll.gdi32.CreateCompatibleDC
        self.GetClientRect = windll.user32.GetClientRect
        self.CreateCompatibleBitmap = windll.gdi32.CreateCompatibleBitmap
        self.SelectObject = windll.gdi32.SelectObject
        self.BitBlt = windll.gdi32.BitBlt
        self.SRCCOPY = 0x00CC0020
        self.GetBitmapBits = windll.gdi32.GetBitmapBits
        self.DeleteObject = windll.gdi32.DeleteObject
        self.ReleaseDC = windll.user32.ReleaseDC

        # 排除缩放干扰
        windll.user32.SetProcessDPIAware()

    def capture(self, handle: int):
        """窗口客户区截图

        Args:
            handle (HWND): 要截图的窗口句柄

        Returns:
            numpy.ndarray: 截图数据
        """
        # 获取窗口客户区的大小
        r = RECT()
        self.GetClientRect(handle, byref(r))
        # width, height = r.right, r.bottom
        width = 1920
        height = 1020
        # 开始截图
        dc = self.GetDC(handle)
        cdc = self.CreateCompatibleDC(dc)
        bitmap = self.CreateCompatibleBitmap(dc, width, height)
        self.SelectObject(cdc, bitmap)
        self.BitBlt(cdc, 0, 0, width, height, dc, 0, 0, self.SRCCOPY)
        # 截图是BGRA排列，因此总元素个数需要乘以4
        total_bytes = width*height*4
        buffer = bytearray(total_bytes)
        byte_array = c_ubyte*total_bytes
        self.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
        self.DeleteObject(bitmap)
        self.DeleteObject(cdc)
        self.ReleaseDC(handle, dc)
        # 返回截图数据为numpy.ndarray
        return frombuffer(buffer, dtype=uint8).reshape(height, width, 4)
#
#     def get_windows_handle(self):
#         """
#         查找游戏窗口，只允许双开游戏
#         :return:
#         """
#         handle_list = []
#         handle_2 = win32gui.FindWindow("FxMain", None)
#         if handle_2 > 0:
#             handle_list.append(handle_2)
#             while True:
#                 handle_2 = win32gui.FindWindowEx(None, handle_2, "FxMain", None)
#                 if handle_2 > 0:
#                     handle_list.append(handle_2)
#                 else:
#                     break
#         return list(set(handle_list))


# if __name__ == "__main__":
#     import cv2  # 197946
#     # handle = windll.user32.FindWindowW(None, "九阴真经  武侠服专区-侠骨丹心")
#     # handle = windll.user32.FindWindowW("FxMain", None)
#     # handle = win32gui.FindWindowEx(windll.user32.FindWindowW("FxMain", None), None, "FxMain", None)
#     # win32gui.SetForegroundWindow(handle)
#     image = windowsCap().capture(198240)
#     cv2.imshow("Capture Test", image)
#     cv2.waitKey()

