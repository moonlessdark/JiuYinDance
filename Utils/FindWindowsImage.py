"""
查询游戏窗口中的图标
"""
import sys
from collections import namedtuple
from ctypes import windll, c_ubyte, wintypes, byref
from typing import List, Union, Tuple

import cv2
import numpy as np
import psutil
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image
from numpy import fromfile, uint8

from Utils.ImageUtils.FindImageTemplate import find_all_template
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows

PicCapture = namedtuple("PicCapture", ["pic_content", "pic_width", "pic_height"])


def is_window_dpi_aware(hwnd):
    """检测窗口是否为DPI感知模式"""
    try:
        # 获取窗口DPI
        window_dpi = windll.user32.GetDpiForWindow(hwnd)
        # 获取系统DPI
        hdc = win32gui.GetDC(0)
        try:
            system_dpi = windll.gdi32.GetDeviceCaps(hdc, win32con.LOGPIXELSX)
        finally:
            win32gui.ReleaseDC(0, hdc)

        # 如果窗口DPI等于系统DPI，可能是DPI感知窗口
        return window_dpi == system_dpi
    except:
        return False


def get_appropriate_scaling_factor(hwnd):
    """获取适当的缩放因子"""
    if is_window_dpi_aware(hwnd):
        # DPI感知窗口，使用1.0缩放因子
        # print("DPI感知窗口，使用1.0缩放因子")
        return 1.0
    else:
        # 非DPI感知窗口，使用系统缩放因子
        # print("非DPI感知窗口，使用系统缩放因子")
        return get_window_scaling_factor()


def get_window_scaling_factor():
    """获取系统缩放因子"""
    # 获取主显示器的DPI
    hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
    dpi = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
    hdc.DeleteDC()

    # 标准DPI是96，缩放因子 = 当前DPI / 96
    scaling_factor = dpi / 96.0
    # print("系统缩放因子:", scaling_factor)
    return scaling_factor


def capture_window_client_area(hwnd):
    """根据窗口句柄对窗口客户区进行后台截图"""
    try:
        # 获取客户区尺寸和位置信息
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)

        # 计算客户区在窗口中的偏移量
        border_width = (right - left - (client_right - client_left)) // 2
        caption_height = (bottom - top - (client_bottom - client_top)) - border_width

        # 获取客户区尺寸
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        # 获取缩放因子
        scaling_factor = get_appropriate_scaling_factor(hwnd)

        # 应用缩放因子
        width = int(client_width * scaling_factor)
        height = int(client_height * scaling_factor)

        if width <= 0 or height <= 0:
            raise Exception("窗口尺寸无效")

        # 创建设备上下文
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        # 创建位图
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # 使用BitBlt截图客户区（从边框偏移位置开始截图）
        src_x = border_width
        src_y = caption_height
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (src_x, src_y), win32con.SRCCOPY)

        # 转换为PIL图像
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # 保存图像
        # img.save(filename)

        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        # print(f"截图成功: {filename}")
        # print(f"窗口分辨率: {width}x{height}")
        return True, (width, height)

    except Exception as e:
        print(f"截图失败: {str(e)}")
        return False, (0, 0)


class WindowsCapture:
    """
    窗口截图
    """

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

    @staticmethod
    def windows_handle_visible(handle_id: int) -> bool:
        """
        查询Windows窗口是否存在
        :param handle_id: 窗口id
        :return:
        """
        _check_result: bool = True
        if not win32gui.IsWindow(handle_id):
            _check_result = False
        else:
            if win32gui.IsIconic(handle_id):
                # IsIconic‌：返回一个布尔值，表示窗口是否最小化。如果窗口最小化，返回TRUE；否则返回FALSE。
                _check_result = False
            elif not win32gui.IsWindowVisible(handle_id):
                # IsWindowVisible‌：返回一个布尔值，表示窗口是否可见。如果窗口可见，返回TRUE；否则返回FALSE。
                _check_result = False
        return _check_result

    @staticmethod
    def check_capture_width_height_is_zero(cap_pic_temp: PicCapture) -> bool:
        """
        检测这个截图是否有效，宽高是否存在 0 像素的情况
        :param cap_pic_temp: 截图
        :return: True，有效， False,无效
        """
        if 0 in [cap_pic_temp.pic_width, cap_pic_temp.pic_height]:
            # 如果宽或者高为0，表示这张图片有问题
            return False
        return True

    def capture_bitblt(self, handle: int) -> PicCapture:
        """
        使用BitBlt方法截图窗口（原capture方法）
        :param handle: 窗口句柄
        :return: 截图数据
        """
        handle = int(handle)
        if not self.windows_handle_visible(handle):
            return None

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

        # 清理资源
        self.DeleteObject(bitmap)
        self.DeleteObject(cdc)
        self.ReleaseDC(handle, dc)

        # 返回截图数据为numpy.ndarray
        cap_pic = PicCapture(np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4), width, height)

        if not self.check_capture_width_height_is_zero(cap_pic):
            return None
        print(f"{cap_pic.pic_width} x {cap_pic.pic_height}")
        return cap_pic

    def capture(self, handle: int) -> PicCapture:
        # 其次尝试BitBlt方法
        result = self.capture_bitblt(handle)
        if result is not None:
            return result
        return None

    def capture_window_region(self, hwnd: int, x: int, y: int, width: int, height: int) -> PicCapture:
        """
        根据坐标在窗口中截取一部分的画面。\n
        注意传的x和y别比实际窗口要大。\n
        注意传入的 x，y 的正负\n
        例如: \n
        1、截图左上角，宽高为100的画面: x=0, y=0, width=100, height=100\n
        2、截图右上角，宽高为100的画面: x=-0, y=0, width=100, height=100\n
        2、截图左下角，宽高为100的画面: x=0, y=-0, width=100, height=100\n
        2、截图右下角，宽高为100的画面: x=-0, y=-0, width=100, height=100\n

        :param hwnd: 窗口句柄
        :param x: 截取区域的左上角 x 坐标，如果传负数，表示从右侧往左计算，计算规则与正数时相反
        :param y: 截取区域的左上角 y 坐标，如果传负数，表示有下往上计算，计算规则与正数时相反
        :param width: 要截取的宽度
        :param height: 要截取的高度
        :return:
        """

        hwnd = int(hwnd)

        if not self.windows_handle_visible(hwnd):
            return None

        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        window_width = right - left
        window_height = bottom - top

        # 获取客户区尺寸（不含边框）
        client_rect = win32gui.GetClientRect(hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        # 计算边框和标题栏尺寸
        border_width = (window_width - client_width) // 2
        title_height = window_height - client_height - border_width

        # 针对 -0 特别处理一下，因为 -0 不太好判断。一般没有 +-0 这种概念
        x = -1 if x == -0 else x
        y = -1 if y == -0 else y

        # 处理负坐标转换（核心新增功能）
        if x < 0:
            x = client_width + x - width + border_width
        else:
            x += border_width

        if y < 0:
            y = client_height + y - height + title_height
        else:
            y += title_height

        # 边界检查
        if x < border_width or y < title_height or \
                (x + width) > (client_width + border_width) or \
                (y + height) > (client_height + title_height):
            raise ValueError("传的x,y坐标超出游戏窗口的实际大小了\n"
                             f"当前窗口的宽高为{client_width}*{client_height}")

        # 创建设备上下文
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # 执行区域拷贝
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(save_bitmap)
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (x, y), win32con.SRCCOPY)

        # 转换为OpenCV格式
        bmp_info = save_bitmap.GetInfo()
        bmp_array = np.frombuffer(save_bitmap.GetBitmapBits(True), dtype=np.uint8)
        img = bmp_array.reshape((bmp_info['bmHeight'], bmp_info['bmWidth'], 4))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 资源释放
        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        cap_pic = PicCapture(img, width, height)
        if not self.check_capture_width_height_is_zero(cap_pic):
            return None
        return cap_pic


class WindowsHandle:

    @staticmethod
    def get_windows_handle() -> List[int]:
        """
        通过便利的方式获取所有的窗口id，然后过滤出我要的
        :return:
        """
        handle_list: List[int] = []
        hwnd_list: List[int] = []
        win32gui.EnumWindows(lambda hwnd, param: param.append(hwnd), hwnd_list)
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

    @staticmethod
    def activate_windows(windows_handle: int) -> bool:
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
            except Exception:
                return False
        return True


class FindWindowsImageTemplate:
    """
    查询游戏窗口中的图标的位置
    """

    def __init__(self):
        self._windows_cap = WindowsCapture()

    def get_windows_image_rect(self, hwnd: int, read_image: np.ndarray, threshold: float = 0.7,
                               edge: bool = False) -> tuple:
        """
        查询图标模板在游戏窗口中的匹配度最高的坐标，并将坐标映射到Windows窗口中。
        此坐标可被鼠标直接使用
        :param edge: 是否支持透明图层
        :param threshold: 匹配度 0 - 1
        :param hwnd: 窗口id
        :param read_image: 需要寻找的模板
        :return: None 或者 （x, y）
        """
        _windows_cap: PicCapture = self._windows_cap.capture(hwnd)

        _cap_point: list = []

        if _windows_cap is not None:
            if isinstance(read_image, str):
                # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
                image = cv2.imdecode(fromfile(read_image, dtype=uint8), cv2.IMREAD_UNCHANGED)
            else:
                image = read_image.copy()
            match_result = find_all_template(_windows_cap.pic_content, image, threshold, edge=edge)
            """
            match_result = [{'result': (951.0, 770.0), 'rectangle': ((933, 752), (933, 788), (969, 752), (969, 788)), 'confidence': 0.9120017886161804}, 
                            {'result': (911.0, 770.0), 'rectangle': ((893, 752), (893, 788), (929, 752), (929, 788)), 'confidence': 0.9051406979560852}, 
                            {'result': (871.0, 770.0), 'rectangle': ((853, 752), (853, 788), (889, 752), (889, 788)), 'confidence': 0.90046226978302}, 
                            {'result': (831.0, 770.0), 'rectangle': ((813, 752), (813, 788), (849, 752), (849, 788)), 'confidence': 0.884774923324585}]
            """
            max_confidence_match_point: tuple = ()
            check_confidence: float = 0
            for match_result_l in match_result:
                # 拿出所有匹配的坐标(x, y),校验一下匹配度大小
                rect_re: float = match_result_l['confidence']
                if rect_re < check_confidence:
                    continue
                check_confidence = rect_re
                max_confidence_match_point = match_result_l['result']
            if len(max_confidence_match_point) != 0:
                _p: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=max_confidence_match_point)
                return _p
        return None

    @staticmethod
    def get_image_all_rect(orign_image: np.ndarray, read_image: np.ndarray, threshold: float = 0.7, edge: bool = False,
                           hwnd: int = None) -> list:
        """
        查询所有相似度匹配的坐标，并映射到windows窗口中，此坐标可被鼠标直接使用
        :param hwnd: 窗口句柄，如果传了的话，那么就返回图片在桌面窗口中的坐标，不传就返回图片在游戏窗口中的坐标
        :param orign_image: 原图(完整图片)
        :param read_image: 需要查询的图片模板(小图)
        :param threshold: 相似度
        :param edge: 是否支持透明图层
        :return: None 或者 [(x1, y1), (x2, y2)]
        """
        img_result = []
        if orign_image is not None:

            if isinstance(read_image, str):
                # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
                image = cv2.imdecode(fromfile(read_image, dtype=uint8), cv2.IMREAD_UNCHANGED)
            else:
                image = read_image.copy()

            match_result = find_all_template(orign_image, image, threshold, edge=edge)

            """
            match_result = [{'result': (951.0, 770.0), 'rectangle': ((933, 752), (933, 788), (969, 752), (969, 788)), 'confidence': 0.9120017886161804}, 
                            {'result': (911.0, 770.0), 'rectangle': ((893, 752), (893, 788), (929, 752), (929, 788)), 'confidence': 0.9051406979560852}, 
                            {'result': (871.0, 770.0), 'rectangle': ((853, 752), (853, 788), (889, 752), (889, 788)), 'confidence': 0.90046226978302}, 
                            {'result': (831.0, 770.0), 'rectangle': ((813, 752), (813, 788), (849, 752), (849, 788)), 'confidence': 0.884774923324585}]
            """

            for match_result_l in match_result:
                # 拿出所有匹配的坐标(x, y)
                rect_re = match_result_l['result']
                img_result.append(rect_re)

        point_result: list = []
        if hwnd is not None:
            # 传入了 窗口句柄，返回窗口桌面中的坐标
            for point in img_result:
                _p: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=point)
                point_result.append(_p)
            if len(point_result) == 0:
                return None
        else:
            # 没有传入句柄，那么就返回在游戏窗口中的坐标
            if len(img_result) == 0:
                return None
            else:
                point_result = img_result
        return point_result

    def get_windows_image_rect_first_pos(self, hwnd: int, read_image: np.ndarray, threshold: float = 0.7,
                                         edge: bool = False) -> tuple:
        """
        返回查询到的坐标在左上位置的第一个坐标
        从左往右查询
        从上往下寻找
        """
        _windows_cap: PicCapture = self._windows_cap.capture(hwnd)
        if _windows_cap is None:
            return None
        pic_result = self.get_image_all_rect(_windows_cap.pic_content, read_image, threshold, edge)
        if pic_result is None:
            return None
        pic_result.sort()
        pos: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=pic_result[0])
        return pos  # 获取排序后的第一个结果

    @staticmethod
    def find_area(bigger_img, smaller_pic, threshold=0.7, edge: bool = False) -> list:
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
