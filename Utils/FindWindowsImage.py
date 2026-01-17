"""
查询游戏窗口中的图标
"""
import time
from collections import namedtuple
from ctypes import windll, c_ubyte, wintypes, byref
from typing import List, Optional, Any

import cv2
import numpy as np
import psutil
import win32con
import win32gui
import win32process
import win32ui

from Utils.ImageUtils.FindImageTemplate import find_all_template
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows

PicCapture = namedtuple("PicCapture", ["pic_content", "pic_width", "pic_height"])


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
    def _check_capture_width_height_is_zero(cap_pic_temp: PicCapture) -> bool:
        """
        检测这个截图是否有效，宽高是否存在 0 像素的情况
        :param cap_pic_temp: 截图
        :return: True，有效， False,无效
        """
        if 0 in [cap_pic_temp.pic_width, cap_pic_temp.pic_height]:
            # 如果宽或者高为0，表示这张图片有问题
            return False
        return True

    def _capture_bitblt(self, handle: int) -> Optional[PicCapture]:
        """
        使用BitBlt方法截图窗口

        GetWindowRect vs GetClientRect
        GetWindowRect 返回包括边框和标题栏的整个窗口区域坐标
        GetClientRect 返回不包括边框的客户区（实际内容区域）坐标，且左上角始终为(0,0)
        坐标原点位置
        对于窗口整体坐标：原点(0,0)位于窗口的左上角边框处
        对于客户区坐标：原点(0,0)位于去除边框后的可绘制区域左上角

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

        if not self._check_capture_width_height_is_zero(cap_pic):
            return None
        return cap_pic

    def capture(self, handle: int) -> Optional[PicCapture]:
        # 其次尝试BitBlt方法
        result = self._capture_bitblt(handle)
        if result is not None:
            return result
        return None

    @staticmethod
    def _calculate_region_coordinates(hwnd: int, x: int, y: int, width: int, height: int) -> tuple:
        """计算区域截图的准确坐标"""
        # 获取窗口和客户区尺寸
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        window_width = right - left
        window_height = bottom - top

        client_rect = win32gui.GetClientRect(hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        # 计算边框尺寸
        border_width = (window_width - client_width) // 2
        title_height = window_height - client_height - border_width

        # 处理特殊坐标值
        x = -1 if x == -0 else x
        y = -1 if y == -0 else y

        # 转换坐标
        actual_x = client_width + x - width + border_width if x < 0 else x + border_width
        actual_y = client_height + y - height + title_height if y < 0 else y + title_height

        # 边界检查
        if (actual_x < border_width or actual_y < title_height or
                (actual_x + width) > (client_width + border_width) or
                (actual_y + height) > (client_height + title_height)):
            raise ValueError(f"坐标超出窗口范围，窗口尺寸: {client_width}*{client_height}")

        return actual_x, actual_y, width, height, client_width, client_height

    def capture_window_region(self, hwnd: int, x: int, y: int, width: int, height: int) -> Optional[PicCapture]:
        """
        根据坐标在窗口中截取一部分的画面。\n
        注意传的x和y别比实际窗口要大。\n
        注意传入的 x，y 的正负\n
        例如: \n
        1、截图左上角，宽高为100的画面: x=0, y=0, width=100, height=100\n
        2、截图右上角，宽高为100的画面: x=-0, y=0, width=100, height=100\n
        2、截图左下角，宽高为100的画面: x=0, y=-0, width=100, height=100\n
        2、截图右下角，宽高为100的画面: x=-0, y=-0, width=100, height=100\n

        GetWindowRect vs GetClientRect
        GetWindowRect 返回包括边框和标题栏的整个窗口区域坐标
        GetClientRect 返回不包括边框的客户区（实际内容区域）坐标，且左上角始终为(0,0)
        坐标原点位置
        对于窗口整体坐标：原点(0,0)位于窗口的左上角边框处
        对于客户区坐标：原点(0,0)位于去除边框后的可绘制区域左上角

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
        if not self._check_capture_width_height_is_zero(cap_pic):
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
        :param windows_handle: 窗口句柄
        :return: 激活是否成功
        """
        if not win32gui.IsWindow(windows_handle):
            return False

        current_foreground = win32gui.GetForegroundWindow()
        if windows_handle == current_foreground:
            return True

        try:
            # 检查窗口是否最小化，如果是则恢复
            if win32gui.IsIconic(windows_handle):
                win32gui.ShowWindow(windows_handle, win32con.SW_RESTORE)

            # 尝试激活窗口
            win32gui.ShowWindow(windows_handle, win32con.SW_SHOWNA)
            win32gui.SetForegroundWindow(windows_handle)

            # 验证激活是否成功
            time.sleep(0.2)  # 短暂等待窗口激活
            return win32gui.GetForegroundWindow() == windows_handle

        except (win32gui.error, AttributeError):
            return False


class FindWindowsImageTemplate:
    """
    查询游戏窗口中的图标的位置
    """

    def __init__(self):
        self._windows_cap = WindowsCapture()

    def get_windows_image_rect(self, hwnd: int, template_image: np.ndarray,
                               threshold: float = 0.7,
                               max_cnt: int = 0,
                               auto_scale: tuple[float, float, float] = None,
                               edge: bool = False,
                               to_gray: bool = True,
                               result_type: int = 0,
                               coordinate_change_to_windows: bool = True) -> Optional[tuple]:
        """
        查询图标模板在游戏窗口中的匹配度最高的坐标，并将坐标映射到Windows窗口中。
        此坐标可被鼠标直接使用
        :param edge: 是否支持透明图层
        :param threshold: 匹配度 0 - 1
        :param hwnd: 窗口id
        :param template_image: 需要寻找的模板
        :param to_gray: 是否需要灰度处理
        :param max_cnt: 最大匹配数量
        :param auto_scale: 是否需要进行缩放，参数格式： (min_scale, max_scale, step)
        :param coordinate_change_to_windows: 是否需要将坐标转换为Windows窗口中的坐标，如果需要使用到鼠标时那么就需要转换
        :param result_type: 排序类型
                            0-表示返回匹配度最高的结果
                            1-表示返回最靠左上角的结果
                            2-表示返回最靠右下角的结果
        :return: None 或者 （x, y）
        """
        _windows_cap: PicCapture = self._windows_cap.capture(hwnd)
        if _windows_cap is None:
            return None
        match_result = find_all_template(im_source=_windows_cap.pic_content, im_template=template_image,
                                         threshold=threshold,
                                         edge=edge,
                                         max_cnt=max_cnt,
                                         auto_scale=auto_scale,
                                         to_gray=to_gray)
        if match_result is None or len(match_result) == 0:
            return None
        """
        match_result = [{'result': (951.0, 770.0), 'rectangle': ((933, 752), (933, 788), (969, 752), (969, 788)), 'confidence': 0.9120017886161804}, 
                        {'result': (911.0, 770.0), 'rectangle': ((893, 752), (893, 788), (929, 752), (929, 788)), 'confidence': 0.9051406979560852}, 
                        {'result': (871.0, 770.0), 'rectangle': ((853, 752), (853, 788), (889, 752), (889, 788)), 'confidence': 0.90046226978302}, 
                        {'result': (831.0, 770.0), 'rectangle': ((813, 752), (813, 788), (849, 752), (849, 788)), 'confidence': 0.884774923324585}]
        """
        if result_type == 0:
            # 按置信度降序排列（优先高匹配度）
            match_result.sort(key=lambda x: x['confidence'], reverse=True)
        elif result_type == 1:
            # 按左上角坐标升序排列
            match_result.sort(key=lambda x: x['result'][0])
        elif result_type == 2:
            # 多级排序（先按Y坐标，再按X坐标）
            match_result.sort(key=lambda x: (x['result'][1], x['result'][0]))
        else:
            raise ValueError("result_type参数错误")

        result_match = match_result[0]
        coordinate_x, coordinate_y = result_match['result']
        if coordinate_change_to_windows:
            # 如果需要转换为窗口坐标
            windows_coordinate: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=(coordinate_x, coordinate_y))
            coordinate_x, coordinate_y = windows_coordinate
        return coordinate_x, coordinate_y

    @staticmethod
    def get_windows_image_all_rect(source_image: np.ndarray, template_image: np.ndarray,
                                   threshold: float = 0.7,
                                   edge: bool = False,
                                   max_cnt: int = 0,
                                   auto_scale: tuple[float, float, float] = None,
                                   to_gray: bool = True,
                                   coordinate_change_to_windows: bool = True,
                                   hwnd: int = None) -> Optional[list]:
        """
        查询所有相似度匹配的坐标，并映射到windows窗口中，此坐标可被鼠标直接使用
        :param source_image: 原图(完整图片)
        :param template_image: 需要查询的图片模板(小图)
        :param threshold: 相似度
        :param edge: 是否支持透明图层
        :param max_cnt: 最大匹配数量
        :param auto_scale: 是否需要缩放匹配
        :param coordinate_change_to_windows: 是否需要转为window坐标
        :param to_gray: 是否需要灰度计算
        :param hwnd: 窗口句柄，用于转换Windows坐标
        :return: None 或者 [(x1, y1), (x2, y2)]
        """

        match_result = find_all_template(im_source=source_image, im_template=template_image,
                                         threshold=threshold,
                                         edge=edge,
                                         max_cnt=max_cnt,
                                         auto_scale=auto_scale,
                                         to_gray=to_gray)
        if match_result is None or len(match_result) == 0:
            return None

        img_result = []
        if coordinate_change_to_windows:
            for result in match_result:
                coordinate_x, coordinate_y = result['result']
                if hwnd is not None:
                    windows_coordinate: tuple = coordinate_change_from_windows(hwnd=hwnd, coordinate=(coordinate_x, coordinate_y))
                    coordinate_x, coordinate_y = windows_coordinate
                img_result.append((coordinate_x, coordinate_y))
        else:
            for result in match_result:
                img_result.append(result['result'])
        return img_result

    @staticmethod
    def get_windows_image_area(bigger_img, smaller_pic,
                               threshold=0.7,
                               edge: bool = False,
                               auto_scale: tuple[float, float, float] = None,
                               to_gray: bool = True,
                               result_type: int = 0, ) -> list[tuple[Any, Any] | float] | None:
        """
        通过模板匹配，返回匹配度最高的4个坐标(非圆心点)
        :param smaller_pic:
        :param bigger_img:
        :param threshold:
        :param edge: 是否边缘计算
        :param auto_scale: 缩放
        :param to_gray: 是否灰度计算
        :param result_type 排序类型
                            0-表示返回匹配度最高的结果
                            1-表示返回最靠左上角的结果
                            2-表示返回最靠右下角的结果
        :return: [(左上角，右上角，左下角，右下角)， 相似度]
        """

        match_result = find_all_template(im_source=bigger_img, im_template=smaller_pic, threshold=threshold, edge=edge,
                                         auto_scale=auto_scale, to_gray=to_gray)
        if len(match_result) == 0 or match_result is None:
            return None
        if result_type == 0:
            # 按置信度降序排列（优先高匹配度）
            match_result.sort(key=lambda x: x['confidence'], reverse=True)
        elif result_type == 1:
            # 按左上角坐标升序排列
            match_result.sort(key=lambda x: x['result'][0])
        elif result_type == 2:
            # 多级排序（先按Y坐标，再按X坐标）
            match_result.sort(key=lambda x: (x['result'][1], x['result'][0]))
        else:
            raise ValueError("result_type参数错误")

        match = match_result[0]
        rect = match['rectangle']
        confidence: float = match['confidence']
        confidence = round(confidence, 2)  # 相似度保留2位小数
        img_result = [(rect[0][0], rect[0][1]),  # 左上角
                      (rect[1][0], rect[1][1]),  # 右上角
                      (rect[2][0], rect[2][1]),  # 左下角
                      (rect[3][0], rect[3][1]),  # 右上角
                      confidence  # 相似度
                      ]
        return img_result
