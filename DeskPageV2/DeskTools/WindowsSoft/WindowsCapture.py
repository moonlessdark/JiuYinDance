
from ctypes import c_ubyte, windll

import cv2
from numpy import fromfile, uint8, frombuffer

from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import display_windows_detection
from DeskPageV2.DeskTools.WindowsSoft.ThresholdImage import threshold_image
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import PicCapture
from DeskPageV2.DeskTools.WindowsSoft.findImage import find_all_template


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

    def capture(self, handle: int, binational: bool = False) -> PicCapture:
        """
        窗口区域显示在屏幕上的地方截图
        :param binational: 是否二值化
        :param handle: 窗口句柄
        :return: 截图数据 numpy.ndarray格式 和 图片宽度, 图片高度
        """

        # 窗口模式，高度减30
        width, height = display_windows_detection(handle)

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
        # cap_pic_content = frombuffer(buffer, dtype=uint8).reshape(height, width, 4)
        cap_pic_content = frombuffer(buffer, dtype=uint8).reshape(height, width, 4)
        if binational:
            """
            二值化
            """
            cap_pic_content = threshold_image(cap_pic_content)
        cap_pic = PicCapture(cap_pic_content, width, height)
        return cap_pic

    def capture_and_clear_black_area(self, handle: int) -> PicCapture:
        """
        切图并且去除黑边。
        :param handle: 需要切图的窗口句柄
        :return: 处理后的图片，图片的宽， 图片的高
        """
        f_img = self.capture(handle)
        return self.__clear_black_area2(f_img.pic_content)

    @staticmethod
    def __clear_black_area(read_img) -> PicCapture:
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
    def __clear_black_area2(read_img) -> PicCapture:
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

    def find_coordinate_area(self, handle: int, img, threshold: float, edge: bool):
        """
        查找图片在目标窗口中的区域,返回匹配度最高的
        :param edge:
        :param threshold:
        :param handle: 句柄
        :param img: 要查找的图片,可以是opencv已加载的，也可以是文件路径
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
        img_result: list = self.__find_area(smaller_pic=source_img, bigger_img=cap_img, threshold=threshold, edge=edge)
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
        return img_result_check

    def find_all_coordinate_area(self, handle: int, img, threshold: float, edge: bool):
        """
        查找图片在目标窗口中的区域
        :param edge:
        :param threshold:
        :param handle: 句柄
        :param img: 要查找的图片,可以是opencv已加载的，也可以是文件路径
        :return: 目标窗口内的区域，4个角度
        """
        cap_img, width, high = self.capture(handle)
        if isinstance(img, str):
            """
            如果时字符串形式的，说明时本地图片，那么就读取吧
            """
            source_img = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            source_img = img
        find_all_list = self.__find_area(smaller_pic=source_img, bigger_img=cap_img, threshold=threshold, edge=edge)
        return find_all_list

    @staticmethod
    def __find_area(smaller_pic, bigger_img, threshold: float, edge: bool) -> list:
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
        return img_result

    def find_coordinate(self, smaller_pic, bigger_img, threshold, edge: bool = False) -> list:
        """
        大图里面找小图,返回匹配度最高的
        :param edge:
        :param threshold: 相似度，0-1
        :param bigger_img: 大图
        :param smaller_pic: 小图'
        :return [[x, y, confidence]]  #坐标和相似度
        """
        img_result = self.find_all_coordinate(smaller_pic=smaller_pic, bigger_img=bigger_img, threshold=threshold,
                                              edge=edge)
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
        return img_result_check

    @staticmethod
    def find_all_coordinate(smaller_pic, bigger_img, threshold, edge: bool = False) -> list:
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
