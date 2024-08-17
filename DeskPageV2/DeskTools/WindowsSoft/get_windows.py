from collections import namedtuple
from ctypes import windll, c_ubyte, wintypes, pointer, byref, sizeof
from typing import List

import cv2
import psutil
import win32api
import win32com
import win32con
import win32gui
import win32process
from numpy import frombuffer, fromfile, uint8
from win32com import client

from DeskPageV2.DeskTools.WindowsSoft.windows import AllowSetForegroundWindow
from DeskPageV2.DeskTools.WindowsSoft.findImage import find_all_template, find_template

PicCapture = namedtuple("PicCapture", ["pic_content", "pic_width", "pic_height"])


class GetHandleList:
    shell = None

    @staticmethod
    def get_windows_handle() -> List[int]:
        """
        通过便利的方式获取所有的窗口id，然后过滤出我要的
        :return:
        """
        handle_list: List[int] = []
        hwnd_list: List[int] = []
        win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), hwnd_list)
        if len(hwnd_list) > 0:
            for handle_id in hwnd_list:
                main_text: str = win32gui.GetWindowText(handle_id)

                # 读取任务进程id
                thread_id, process_id = win32process.GetWindowThreadProcessId(handle_id)
                # Get the process name and executable path
                process: psutil.Process = psutil.Process(process_id)
                process_name: str = process.name()

                if main_text.find("九阴真经 ") == 0 and process_name == 'fxgame.exe':
                    handle_list.append(handle_id)
        handle_list.sort()
        return handle_list

    def activate_windows(self, windows_handle: int) -> bool:
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        return self.activate_windows_1(windows_handle)

    @staticmethod
    def activate_windows_1(windows_handle: int):
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        if windows_handle != win32gui.GetForegroundWindow():
            try:
                win32api.keybd_event(0xC, 0, 0, 0)
                win32gui.ShowWindow(windows_handle, win32con.SW_SHOWNA)
                win32gui.SetForegroundWindow(windows_handle)
            except Exception as e:
                return False
        return True

    @staticmethod
    def activate_windows_2(windows_handle: int):
        """
        激活窗口
        :param windows_handle:
        :return:
        """
        if windows_handle != win32gui.GetForegroundWindow():
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                # input("Press Enter")
                shell.SendKeys(' ')  # Undocks my focus from Python IDLE
                win32gui.SetForegroundWindow(windows_handle)  # It works!
                shell.SendKeys('%')
            except Exception as e:
                return False
        return True

    @staticmethod
    def activate_windows_3(windows_handle: int):
        """
        激活窗口方法3
        注意，此方法完全无效
        :param windows_handle:
        :return:
        """
        try:
            h_fore_wind: str = win32gui.GetForegroundWindow()
            dw_curth_id: str= win32process.GetCurrentProcessId()
            dw_fore_id = win32process.GetWindowThreadProcessId(h_fore_wind, None)
            win32process.AttachThreadInput(dw_curth_id, dw_fore_id, True)
            win32gui.SetWindowPos(windows_handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
            win32gui.SetWindowPos(windows_handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOMOVE)
            win32gui.SetForegroundWindow(windows_handle)
            win32process.AttachThreadInput(dw_curth_id, dw_fore_id, False)
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def set_allow_set_foreground_window():
        """
        允许其他窗口来到前台
        :return:
        """
        windows_foregroud_handle_id = win32gui.GetForegroundWindow()
        # 读取任务进程id
        thread_id, process_id = win32process.GetWindowThreadProcessId(windows_foregroud_handle_id)
        # Get the process name and executable path
        AllowSetForegroundWindow(0)


def get_window_rect(handle) -> list:
    """
    获取窗口在屏幕上的位置
    :param handle: 窗口的handle
    :return:
        返回的内容为
        [left, top],  # 左上角坐标
        [left, bottom],  # 左下角坐标
        [right, top],  # 右上角坐标
        [right, bottom]  # 右下角坐标
    """
    rect = wintypes.RECT()
    windll.user32.GetWindowRect(handle, pointer(rect))
    return [[rect.left, rect.top], [rect.left, rect.bottom], [rect.right, rect.top], [rect.right, rect.bottom]]


def mapping_coordinates(handle, x, y):
    """
    映射窗口中的坐标在屏幕上的位置
    :param handle: 句柄
    :param x: 窗口中的x轴
    :param y: 窗口中的y轴
    :return: 在屏幕上的x,y
    """
    rect = get_window_rect(handle)
    return rect[0][0] + x, rect[0][1] + y


def find_pic(smaller_pic, bigger_img, threshold=0.7, edge: bool = False) -> list:
    """
    大图里面找小图
    :param edge:
    :param threshold: 相似度，0-1
    :param bigger_img: 大图
    :param smaller_pic: 小图'
    :return [[x, y, confidence]]  #坐标和相似度
    """
    match_result = find_all_template(bigger_img, smaller_pic, threshold, edge=edge)
    img_result = []
    if len(match_result) > 0:
        for mr in match_result:
            rect = mr['rectangle']
            x = (int(rect[1][0]) + int(rect[2][0])) / 2 + 0
            y = (int(rect[0][1]) + int(rect[1][1])) / 2 + 0
            confidence: float = mr['confidence']
            confidence = round(confidence, 2)  # 相似度保留2位小数
            img_result.append([x, y, confidence])
    return img_result


def find_area(smaller_pic, bigger_img, threshold=0.7, edge: bool = False) -> list:
    """
    大图中寻找小区的坐标区域
    :param smaller_pic:
    :param bigger_img:
    :param threshold:
    :param edge:
    :return: [(左上角，右上角，左下角，右下角)， 相似度]
    """
    match_result = find_all_template(bigger_img, smaller_pic, threshold, edge=edge)
    img_result = []
    if len(match_result) > 0:
        for mr in match_result:
            rect = mr['rectangle']

            # img_result = bigger_img.copy()
            # cv2.rectangle(img_result, (rect[0][0], rect[0][1]), (rect[3][0], rect[3][1]), (0, 0, 220), 2)
            # cv2.imshow('find_all_template_result.en.png', img_result)
            # cv2.waitKey()

            confidence: float = mr['confidence']
            confidence = round(confidence, 2)  # 相似度保留2位小数
            img_result.append(
                [(rect[0][0], rect[0][1]),  # 左上角
                 (rect[1][0], rect[1][1]),  # 右上角
                 (rect[2][0], rect[2][1]),  # 左下角
                 (rect[3][0], rect[3][1]),  # 右上角
                 confidence  # 相似度
                 ]
            )
    img_result_check: list = []
    if len(img_result) > 1:
        # 如果找到了多个结果的时候,把匹配对最高的那个拿出来
        confidence_check: float = 0
        for area_li in img_result:
            if area_li[4] > confidence_check:
                img_result_check = area_li
            confidence_check = area_li[4]
    elif len(img_result) == 1:
        img_result_check: list = img_result[0]
    img_result_check = [0, 0, 0, 0, 0] if len(img_result_check) == 0 else img_result_check
    return img_result_check


def get_handle_size(handle: int):
    """
    获取游戏窗口的实际大小，注意，如果是高分辨率显示，且有缩放，那么这个方法就要注意了。使用此方法获取的截图，会有大黑边
    该代码来自于 https://stackoverflow.com/questions/3192232/getwindowrect-too-small-on-windows-7
    :return:
    """
    try:
        f = windll.dwmapi.DwmGetWindowAttribute
    except Exception as e:
        f = None
    if f:
        pic_size = namedtuple("PicSize", ["width", "high"])
        rect = wintypes.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        f(wintypes.HWND(handle),
          wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
          byref(rect),
          sizeof(rect)
          )
        width, high = (rect.right - rect.left, rect.bottom - rect.top)
        pic_size(width=width, high=high)
        return pic_size


# def get_handle_scale_size(handle_id):
#     """
#     获取窗口在高分辨显示器下进行缩放设置后的大小
#     :param handle_id: 窗口句柄
#     :return: 窗口宽度，窗口高度
#     """
#     rect = win32gui.GetClientRect(handle_id)
#     x = rect[0]
#     y = rect[1]
#     w = rect[2] - x
#     h = rect[3] - y
#     return w, h


class WindowsCapture:

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

    def capture(self, handle: int) -> PicCapture:
        """
        窗口区域显示在屏幕上的地方截图
        :param handle: 窗口句柄
        :return: 截图数据 numpy.ndarray格式 和 图片宽度, 图片高度
        """

        handle = int(handle)

        r = wintypes.RECT()
        self.GetClientRect(handle, byref(r))
        width, height = r.right, r.bottom
        # 开始截图
        dc = self.GetDC(handle)
        cdc = self.CreateCompatibleDC(dc)
        bitmap = self.CreateCompatibleBitmap(dc, width, height)
        self.SelectObject(cdc, bitmap)
        self.BitBlt(cdc, 0, 0, width, height, dc, 0, 0, self.SRCCOPY)
        # 截图是BGRA排列，因此总元素个数需要乘以4
        total_bytes = width * height * 4
        buffer = bytearray(total_bytes)
        byte_array = c_ubyte * total_bytes
        self.GetBitmapBits(bitmap, total_bytes, byte_array.from_buffer(buffer))
        self.DeleteObject(bitmap)
        self.DeleteObject(cdc)
        self.ReleaseDC(handle, dc)
        # 返回截图数据为numpy.ndarray
        # cap_pic = PicCapture(frombuffer(buffer, dtype=uint8).reshape(height, width, 4)[:, :, :3], width, height)
        cap_pic = PicCapture(frombuffer(buffer, dtype=uint8).reshape(height, width, 4), width, height)
        return cap_pic

    def capture_and_clear_black_area(self, handle: int) -> PicCapture:
        """
        切图并且去除黑边。
        :param handle: 需要切图的窗口句柄
        :return: 处理后的图片，图片的宽， 图片的高
        """
        f_img = self.capture(handle)
        return self.clear_black_area2(f_img.pic_content)

    @staticmethod
    def clear_black_area(read_img) -> PicCapture:
        """
        去除屏幕黑边，并返回去除后的分辨率。
        由于是正序(从左上角(0,0)开始)遍历整张图片的所有分辨率的像素，此方法效率很慢，只能用在不是很急的时候
        :param read_img:
        :return: 图片，高，宽
        """
        if isinstance(read_img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            image = cv2.imdecode(fromfile(read_img, dtype=uint8), -1)
        else:
            image = read_img
        # image = cv2.imread(read_img, 1)  # 读取图片 image_name应该是变量
        img = cv2.medianBlur(image, 5)  # 中值滤波，去除黑色边际中可能含有的噪声干扰
        b = cv2.threshold(img, 15, 255, cv2.THRESH_BINARY)  # 调整裁剪效果
        binary_image = b[1]  # 二值图--具有三通道
        binary_image = cv2.cvtColor(binary_image, cv2.COLOR_BGR2GRAY)
        h: int = binary_image.shape[0]
        w: int = binary_image.shape[1]
        # print("高度x=", x)
        # print("宽度y=", y)
        edges_x = []
        edges_y = []
        for i in range(h):
            for j in range(w):
                if binary_image[i][j] != 0:
                    # 如果是非透明像素
                    edges_x.append(i)
                    edges_y.append(j)

        left = min(edges_x)  # 左边界
        right = max(edges_x)  # 右边界
        width = right - left  # 宽度

        bottom = min(edges_y)  # 底部
        top = max(edges_y)  # 顶部
        height = top - bottom  # 高度

        pre1_picture = image[left:left + width, bottom:bottom + height]  # 图片截取
        cap_pic = PicCapture(pre1_picture, pre1_picture.shape[1], pre1_picture.shape[0])
        return cap_pic

    @staticmethod
    def clear_black_area2(read_img) -> PicCapture:
        """
        采用倒序的方式，去除透明图层。并返回去除后的分辨率。速度快很多
        :param read_img:
        :return: 图片，高，宽
        """
        if isinstance(read_img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            image = cv2.imdecode(fromfile(read_img, dtype=uint8), -1)
        else:
            image = read_img
        # image = cv2.imread(read_img, 1)  # 读取图片 image_name应该是变量
        img = cv2.medianBlur(image, 5)  # 中值滤波，去除黑色边际中可能含有的噪声干扰
        b = cv2.threshold(img, 15, 255, cv2.THRESH_BINARY)  # 调整裁剪效果
        binary_image = b[1]  # 二值图--具有三通道
        binary_image = cv2.cvtColor(binary_image, cv2.COLOR_BGR2GRAY)
        h: int = int(binary_image.shape[0])
        w: int = int(binary_image.shape[1])
        edges_w: list = []
        edges_h: list = []
        # 先算高度，从底部侧往上算，左下角往上算，碰到非透明的就结束
        for i in range(h - 1, -1, -1):
            edges_h.append(i)
            if binary_image[i][int(h / 2)] != 0:  # 偏移一下，从第10个像素开始取值，避免截图位移产生误差
                #  如果是非透明像素，说明没有透明的了，就退出
                break
        # 先算宽度，从右侧往左算，从右上角往左算，碰到非透明的就结束
        for j in range(w - 1, -1, -1):
            edges_w.append(j)
            if binary_image[int(w / 2)][j] != 0:
                # 如果是非透明像素，说明没有透明的了，就退出
                break
        left = min(edges_w)  # 图片中，透明部分的开始的宽度
        bottom = min(edges_h)  # 图片中，透明部分的开始的高度
        pre1_picture = image[0:bottom, 0:left]  # 图片截取，只截图非透明的那部分
        cap_pic = PicCapture(pre1_picture, pre1_picture.shape[1], pre1_picture.shape[0])
        return cap_pic

    def capture_by_coordinate(self, handle: int, height_top: int, height_down: int, width_left: int, width_right: int):
        """
        截图后，再次根据坐标二次截取
        :param handle: 窗口handle
        :param height_top: 高度坐标(顶部)
        :param height_down: 高度坐标(底部)
        :param width_left: 宽度坐标(左侧)
        :param width_right: 宽度坐标(右侧)
        :return: 返回图片在窗口中的中心点坐标
        """
        if height_top >= height_down or width_left >= width_right:
            """
            坐标错误
            """
            return None

        img = self.capture(handle)
        return img[height_top:height_down, width_left:width_right]

    def find_coordinate(self, handle: int, img, x_offset: int = 0, y_offset: int = 0):
        """
        查找图片在目标窗口中的坐标
        :param handle: 句柄
        :param img: 要查找的图片,可以是opencv已加载的，也可以是文件路径
        :param x_offset: x轴的偏移量
        :param y_offset: y轴的偏移量
        :return: 目标窗口内的坐标
        """
        cap_img, width, high = self.capture(handle)
        if isinstance(img, str):
            """
            如果时字符串形式的，说明时本地图片，那么就读取吧
            """
            source_img = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            source_img = img
        match_result = find_template(cap_img, source_img, threshold=0.8)
        if match_result is not None:
            rect = match_result['rectangle']
            x = (int(rect[1][0]) + int(rect[2][0])) / 2 + x_offset
            y = (int(rect[0][1]) + int(rect[1][1])) / 2 + y_offset
            return int(x), int(y)
        return 0, 0

    def find_coordinate_to_rect(self, handle: int, img, x_offset: int = 0, y_offset: int = 0):
        """
        查找图片，在屏幕上的坐标
        :param handle: 句柄
        :param img: 要查找的图片,可以是opencv已加载的，也可以是文件路径
        :param x_offset: x轴的偏移量,在4K分辨率下建议 0
        :param y_offset: y轴的偏移量,在4K分辨率下建议 50
        :return: 图片在屏幕上的坐标
        """
        x, y = self.find_coordinate(handle, img, x_offset, y_offset)
        return mapping_coordinates(handle, x, y)

    def find_coordinate_to_rect_2(self, handle: int, img, x_offset: int = 0, y_offset: int = 0):
        """
        查找图片，在屏幕上的坐标, 方法2，以另一种逻辑实现
        :param y_offset: y 坐标的便宜量
        :param x_offset: x 坐标的偏移量
        :param handle: 窗口ID
        :param img: 图片，可以时已经读取在内存中的，也可以是本地文件
        :return: 查找的图片的中心坐标点映射在屏幕上的坐标
        """
        cap_img, width, high = self.capture(handle)
        if isinstance(img, str):
            """
            如果时字符串形式的，说明时本地图片，那么就读取吧
            """
            source_img = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            source_img = img
        match_result = find_template(cap_img, source_img, threshold=0.8)
        cop: list = get_window_rect(handle)
        if match_result is not None:
            rect = match_result['rectangle']
            x = (int(rect[1][0] + int(cop[1][0])) + int(rect[2][0]) + cop[1][0]) / 2 + x_offset
            y = (int(rect[0][1] + int(cop[0][1])) + int(rect[1][1]) + cop[0][1]) / 2 + y_offset
            return x, y
        return 0, 0
