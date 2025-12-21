import cv2
import numpy as np
from Utils.FindWindowsImage import WindowsHandle, PicCapture
from Utils.FindWindowsImage import WindowsCapture
from Utils.ImageUtils.ThresholdImage import custom_image

"""
查找漠西挖宝，右上角箭头的指向
本模块为找色，模板匹配有点难
由于这只是个单独的小功能，我不想和旧的功能耦合在一起，方便随时剥离出来。所以这个模块有完整的业务逻辑。
"""


class MoXiMapLine:

    def __init__(self):
        self.find_hwnd = WindowsHandle()
        self.windows_cap = WindowsCapture()

        self.windows_hwnd_list = []

    def _find_game_windows(self):
        """
        查找游戏窗口
        :return:
        """
        _hwnd_list: list = self.find_hwnd.get_windows_handle()
        if len(_hwnd_list) == 0:
            return None
        self.windows_hwnd_list = _hwnd_list
        return _hwnd_list

    def get_game_windows_mini_map(self) -> tuple:
        """
        截图窗口右上角小地图，在进行此操作时请确保已经开启了挖宝
        :return: code: 200, [最小坐标，最大坐标]
                code: 201, [None, None]  没有发现有窗口在漠西风涛地图
                code: 202, [None, None]  # 发现有多个窗口在漠西风涛地图
                code: 203 没有发现游戏窗口
        """
        _hwnd_list: list or None = self._find_game_windows()
        if _hwnd_list is None:
            return 203, [0, 0]
        _hwnd_list_find: list = self.windows_hwnd_list.copy()
        _find_result: list = []  # 查询到的结果
        for hwnd in _hwnd_list_find:
            # 截图右上角的小地图
            hwnd_img: PicCapture = self.windows_cap.capture_window_region(hwnd,  -43, 58, 126, 126)
            if hwnd_img is None:
                continue
            # cv2.imshow("ss", hwnd_img.pic_content)
            # cv2.waitKey()
            # 分析以下指针
            _min_point, _max_point = self.find_line_three_level(pic=hwnd_img.pic_content)
            if None in [_min_point, _max_point]:
                continue
            _find_result.append([_min_point, _max_point])
        if len(_find_result) == 1:
            return 200, _find_result[0]
        elif len(_find_result) == 0:
            # 没有发现有窗口在漠西地图
            return 201, [0, 0]
        else:
            # 发现有多个窗口在漠西地图，我不知道该以哪个为准
            return 202, [0, 0]

    def find_line(self, pic: np.ndarray) -> tuple:
        """
        将图片二值化，查找指针的坐标
        二级挖宝的罗盘
        :param pic:
        :return:
        """
        xxs: int = 243
        x = self._apply_circular_mask(pic)

        _t_pic: np.ndarray = custom_image(x, xxs, xxs+1)  # 对图片进行二值化，把指针(箭头)高亮
        _min_point, _max_point = self._find_color_extremes_and_draw_line(_t_pic)
        # print(f"1:{_min_point},2:{_max_point}")
        cv2.imshow("ss", _t_pic)
        cv2.waitKey()
        # 画一下连线
        # targets_rgb = (240, 240, 240)  # 红色
        # tolerances = 20  # 容差范围
        # result_img, min_p, max_p = find_color_extremes_and_draw_line(_t_pic, targets_rgb, tolerances)
        # # 显示结果
        # if result_img is not None:
        #     cv2.imshow("Result with Extremes Line", result_img)
        #     cv2.waitKey(0)
        #     cv2.destroyAllWindows()
        #
        #     if min_p is not None and max_p is not None:
        #         print(f"x坐标最小的点: {min_p}")
        #         print(f"x坐标最大的点: {max_p}")
        #
        # if None in [_min_point, _max_point]:
        #     return None, None
        # return _min_point, _max_point

    def find_line_three_level(self, pic: np.ndarray) -> tuple:
        """
        三级挖宝的罗盘
        """
        xxs: int = 225
        x = self._apply_circular_mask(pic)

        _t_pic: np.ndarray = custom_image(x, xxs, xxs + 1)  # 对图片进行二值化，把指针(箭头)高亮
        _min_point, _max_point = self._find_color_extremes_and_draw_line(_t_pic)
        # print(f"1:{_min_point},2:{_max_point}")
        # cv2.imshow("ss", _t_pic)
        # cv2.waitKey()
        # 画一下连线

    @staticmethod
    def _find_color_extremes_and_draw_line(image: np.ndarray) -> tuple:
        """
        在图片中查找与目标RGB值匹配的区域，并返回x坐标最小和最大的点

        :param image:
        :return:
            min_x_point: x坐标最小的点坐标(x,y)
            max_x_point: x坐标最大的点坐标(x,y)
            由于渲染的是位于第二象限的坐标，但是 x 坐标确实 正数，在象限中渲染时需要给 x 加个正数
        """

        if type(image) is str:
            # 读取图片(OpenCV默认读取为BGR格式)
            img = cv2.imread(image)
            if img is None:
                return None, None
        else:
            img = image

        # 将目标RGB转换为BGR格式
        # target_bgr = target_rgb[::-1]

        # # 计算颜色范围
        # lower_bound = np.array([max(0, x - tolerance) for x in target_bgr], dtype=np.uint8)
        # upper_bound = np.array([min(255, x + tolerance) for x in target_bgr], dtype=np.uint8)
        #
        # # 创建颜色掩码
        # mask = cv2.inRange(img, lower_bound, upper_bound)

        # 查找匹配像素的坐标(注意OpenCV的坐标顺序是(y,x))
        matched_pixels = np.column_stack(np.where(img > 242))

        # 如果没有匹配像素，直接返回原图
        if len(matched_pixels) == 0:
            return None, None

        # 找到x坐标最小和最大的点
        # 注意: matched_pixels中的坐标是(y,x)格式，所以取第1列(x坐标)
        min_x_idx = np.argmin(matched_pixels[:, 1])
        max_x_idx = np.argmax(matched_pixels[:, 1])

        # 找一下y坐标的最小和最大值
        min_y_idx = np.argmin(matched_pixels[:, 0])
        max_y_idx = np.argmax(matched_pixels[:, 0])

        _x_absolute: int = abs(int(min_x_idx) - int(max_x_idx))
        _y_absolute: int = abs(int(min_y_idx) - int(max_y_idx))

        if _x_absolute > _y_absolute:
            _min_idx, _max_idx = min_x_idx, max_x_idx
        else:
            _min_idx, _max_idx = min_y_idx, max_y_idx

        # min_x_point = (int(-matched_pixels[min_x_idx][1]), int(matched_pixels[min_x_idx][0]))  # (x,y)
        # max_x_point = (int(-matched_pixels[max_x_idx][1]), int(matched_pixels[max_x_idx][0]))  # (x,y)

        min_x_point = (int(-matched_pixels[_min_idx][1]), int(matched_pixels[_min_idx][0]))  # (x,y)
        max_x_point = (int(-matched_pixels[_max_idx][1]), int(matched_pixels[_max_idx][0]))  # (x,y)

        return min_x_point, max_x_point

    @staticmethod
    def _apply_circular_mask(image_path):
        """
        对正方形图片应用圆形掩码，只保留中间圆形区域

        参数:
            image_path: 输入图片路径
            output_path: 输出图片路径(可选)

        返回:
            masked_img: 应用掩码后的图像
        """
        img = image_path

        # 确保图片是正方形
        height, width = img.shape[:2]
        if height != width:
            print("警告: 图片不是正方形，将自动裁剪为正方形")
            size = min(height, width)
            img = img[:size, :size]
            height = width = size

        # 创建黑色背景的掩码
        mask = np.zeros((height, width), dtype=np.uint8)

        # 计算圆心和半径
        center = (width // 2, height // 2)
        # radius = min(center[0], center[1])
        radius = int(min(center[0], center[1]) * 0.75)  # 调整圆的大小

        # 在掩码上绘制白色圆形
        cv2.circle(mask, center, radius, 255, -1)

        # 应用掩码
        masked_img = cv2.bitwise_and(img, img, mask=mask)

        return masked_img


if __name__ == '__main__':
    # 1:(28, 37),2:(58, 62)
    x = MoXiMapLine()
    pics = cv2.imread(r"D:\XX.jpg")
    x.find_line_three_level(pics)
    #
    # pics2 = cv2.imread(r"D:\SoftWare\Developed\Projected\JiuYinDnaceRemake\xx\ss2.png")
    # x.find_line(pics2)