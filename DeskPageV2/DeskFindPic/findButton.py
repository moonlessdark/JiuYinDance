from collections import namedtuple

import cv2
import numpy as np
from PySide6.QtCore import Signal
from numpy import fromfile

from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic, Config
from DeskPageV2.Utils.load_res import GetConfig
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, WindowsCapture, PicCapture, find_area

FindPicTemplate = namedtuple("FindPicTemplate", ["template_list", "pic_threshold"])


def button_area_x(count: int) -> list:
    """
    获取按钮开始的坐标
    1: 239
    2: 219 - 259
    3: 199 - 279
    4: 179 - 299 = 120 = 3*40
    5: 159 - 319 = 160 = 4*40
    6: 139 - 339
    7: 119 - 359
    :return:
    """
    min_x: int = 259-count*20 - 5  # 偏移量
    max_x: int = min_x + 40*(count-1) + 10  # 偏移量
    return [min_x, max_x]


class FindButton:
    """
    大图找小图的方式查找按钮
    """

    def __init__(self):

        config = GetConfig()
        self.dance_pic: DancePic = config.get_dance_pic()
        self.whz_dance_pic: WhzDancePic = config.get_whz_dance_pic()
        self.find_pic_config: Config = config.get_find_pic_config()

        self.dance_area = cv2.imdecode(fromfile(self.dance_pic.dance_area, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.dance_area_night = cv2.imdecode(fromfile(self.dance_pic.dance_area_night, dtype=np.uint8),
                                             cv2.IMREAD_UNCHANGED)

        self.j = cv2.imdecode(fromfile(self.dance_pic.dance_J, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.k = cv2.imdecode(fromfile(self.dance_pic.dance_K, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.l = cv2.imdecode(fromfile(self.dance_pic.dance_L, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.up = cv2.imdecode(fromfile(self.dance_pic.dance_Up, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.down = cv2.imdecode(fromfile(self.dance_pic.dance_Down, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.left = cv2.imdecode(fromfile(self.dance_pic.dance_Left, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.right = cv2.imdecode(fromfile(self.dance_pic.dance_Right, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

        self.whz_dance_area = cv2.imdecode(fromfile(self.whz_dance_pic.dance_area, dtype=np.uint8),
                                           cv2.IMREAD_UNCHANGED)
        self.whz_dance_up = cv2.imdecode(fromfile(self.whz_dance_pic.dance_Up, dtype=np.uint8), -1)
        self.whz_dance_down = cv2.imdecode(fromfile(self.whz_dance_pic.dance_Down, dtype=np.uint8), -1)
        self.whz_dance_left = cv2.imdecode(fromfile(self.whz_dance_pic.dance_Left, dtype=np.uint8), -1)
        self.whz_dance_right = cv2.imdecode(fromfile(self.whz_dance_pic.dance_Right, dtype=np.uint8), -1)

        self.dance_threshold: float = self.find_pic_config.dance_threshold
        self.whz_dance_threshold: float = self.find_pic_config.whz_dance_threshold
        self.area_dance_threshold: float = self.find_pic_config.area_dance_threshold

        self.button_list: list = []
        self.whz_dance_button_list: list = []

    def get_dance_pic(self) -> tuple:
        """
        团练授业
        先将图标加载到内存中，方便后面调用
        :return:
        """
        if len(self.button_list) == 0:
            self.button_list = [("J", self.j), ("K", self.k), ("L", self.l), ("上", self.up), ("下", self.down),
                                ("左", self.left), ("右", self.right)]
        return self.button_list, self.dance_threshold, False

    def get_whz_dance_pic(self) -> tuple:
        """
        获取望辉洲的图片
        :return:
        """
        if len(self.whz_dance_button_list) == 0:
            self.whz_dance_button_list = [("上", self.whz_dance_up), ("下", self.whz_dance_down),
                                          ("左", self.whz_dance_left), ("右", self.whz_dance_right)]
        return self.whz_dance_button_list, self.whz_dance_threshold, False

    @staticmethod
    def sort_button(button_dict: list, images, debug: bool, single: Signal, dance_type: str):
        """
        给按钮排序。

        处理规则：
        1、每个按钮间隔的距离为 40.用相似度最高的那个按钮作为标准
        2、如果有多个按钮的 横坐标相同，那么就取相似度最高的那个
        :param button_dict:
        :param debug:
        :param dance_type:
        :param single:
        :param images: 按钮出现的区域图
        :return:
        """

        def get_key_count(img) -> int:
            """
            计算出现的按钮数量
            :param img:
            :return:
            """
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, binary = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)  # 阈值化
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # 寻找轮廓线
            i = 0
            for contour in contours:  # 遍历所有轮廓
                area: float = cv2.contourArea(contour)  # 轮廓图面积
                if area > 600:  # 轮廓面积大于600的做 mask
                    i += 1
            if i == 0:
                return i
            return i - 1

        res_button_dict: list = []
        button_key_list: list = []

        if len(button_dict) > 0:
            """
            过滤一下，把识别率太低的按钮排除掉
            """
            button_dict_reverse = sorted(button_dict, reverse=True)  # 排个序，从大到小，拿出匹配最大的值，用于排除掉匹配度错误的数值
            max_threshold_x = button_dict_reverse[0][1]  # 最大匹配值的X坐标
            for line in button_dict_reverse:
                """
                先把匹配对最高的一个按钮，按 40像素一个按钮切割，把值拿出来
                """
                if abs(line[1] - max_threshold_x) % 40 == 0:  # 对40取余
                    res_button_dict.append([line[1], line[0], line[2]])

            if dance_type == "团练":
                button_sum: int = get_key_count(images)
                button_area_x_list: list = button_area_x(button_sum)  # 得到一个大致的范围
                if len(res_button_dict) > 0:
                    """
                    过滤一下，把不在按钮范围内的排除掉
                    """
                    res_button_dict_step1: list = []
                    for line in res_button_dict:
                        if min(button_area_x_list) <= line[0] <= max(button_area_x_list):
                            res_button_dict_step1.append([line[0], line[1], line[2]])
                    if len(res_button_dict_step1) == button_sum:
                        res_button_dict = res_button_dict_step1
            else:
                """
                那就是授业了
                """
                for line in button_dict:
                    res_button_dict.append([line[1], line[0], line[2]])

        if len(res_button_dict) > 0:
            res_button_dict.sort()  # 排个序，从小到大
            res_button_dict.append([None, None, None])  # 增加一个结束表示，循环到他的时候就可以结束了
            button_x, button_p, button_name = 0, 0, ""

            if debug:
                single.emit(f"当前界面识别到 {button_sum} 个按钮")

            for button_param in res_button_dict:
                x, t, n = button_param
                if x is None or x > button_x > 0:
                    # 说明是下一个按钮，先保存上一个按钮
                    button_key_list.append(button_name)
                    if debug:
                        single.emit(f"识别按钮 {button_name} 的最高阈值: {button_p}")
                    button_x, button_p, button_name = x, t, n
                    continue
                # 好了，这个按钮已经处理了，更新一下
                button_x, button_p, button_name = x, t, n
        return button_key_list

    def find_pic_by_bigger(self, bigger_pic_cap: PicCapture, find_type="团练", debug: bool = False, single: Signal = None) -> list:
        """
        从大图里面找小图，并进行从左到右排序
        :param single:
        :param debug:
        :param find_type: 查找方式，团练 或者 望辉洲
        :param bigger_pic_cap: 需要找的大图，是已经读取的图片
        :return: list[str]
        """

        def print_log(string: str):
            """
            打印一下日志
            :param string:
            :return:
            """
            if single is not None:
                single.emit(string)

        bigger_pic = bigger_pic_cap.pic_content
        width, height = bigger_pic_cap.pic_width, bigger_pic_cap.pic_height
        button_dict: list = []
        check_button_list, dance_threshold, edges = self.get_dance_pic() if find_type == "团练" else self.get_whz_dance_pic()
        if width == 0 or height == 0:
            return []
        else:
            bigger_pic = bigger_pic[int(height * 0.6):int(height * 1), int(width * 0.2):int(width * 1)]
        if find_type == "团练":
            """
            先分开查一下白天和黑夜的，看看哪个的识别率高就用哪个
            """
            day: list = find_area(self.dance_area, bigger_pic, threshold=self.area_dance_threshold, edge=True)
            night: list = find_area(self.dance_area_night, bigger_pic, threshold=self.area_dance_threshold, edge=True)

            find_param_type: str = "day" if day[4] > night[4] else "night"
            button_area_list: list = day if day[4] > night[4] else night
            if find_param_type == "night":
                if button_area_list[4] > 0:
                    dance_threshold = dance_threshold - 0.1  # 说明切换了画质，识别阈值降低10%
                    if debug:
                        print_log(f"启用识别模式二(当前区域最高阈值: {button_area_list[4]},设置按钮最低匹配阈值: {dance_threshold})")
            else:
                if debug:
                    print_log(f"启用识别模式一(当前区域最高阈值: {button_area_list[4]},设置按钮最低匹配阈值: {dance_threshold})")
        else:
            """
            望辉洲，势力，挖宝
            """
            button_area_list: list = find_area(self.whz_dance_area, bigger_pic, threshold=dance_threshold, edge=False)

        if button_area_list[4] > 0:
            """
            如果按钮区域的匹配度大于0
            如果只找到了一个，那么就是我需要的，如果找到了多个，那就说明精度有问题，太低了
            bigger_pic = bigger_pic[int(height * 0.7):int(height * 0.85), int(width * 0.4):int(width * 0.6)]
            """
            if find_type == "团练":
                bigger_pic = bigger_pic[int(button_area_list[0][1]):int(button_area_list[1][1]),
                             int(button_area_list[1][0]):int(button_area_list[3][0])]
            else:
                # 挖宝、修罗刀的按钮区域长度400
                bigger_pic = bigger_pic[int(button_area_list[0][1]):int(button_area_list[1][1]),
                             int(button_area_list[1][0] - 10):int(button_area_list[3][0] + 350)]
            # cv2.imshow("dd", bigger_pic)
            # cv2.waitKey()
            for i in check_button_list:
                button_num_list: list = find_pic(i[1], bigger_pic, threshold=dance_threshold, edge=edges)  # 去界面找一下按钮的坐标
                for bu in button_num_list:
                    button_dict.append([bu[2], bu[0], i[0]])  # 把获取到的按钮 x(横坐标) 拿出来，待会要进行排序使用 [相似度， X， 按钮]
        button_dict_result: list = self.sort_button(button_dict, bigger_pic, debug=debug, single=single, dance_type=find_type)
        return button_dict_result


if __name__ == '__main__':
    import time

    pic_path = "02.png"
    pic = cv2.imread(f"D:\\JiuYinScreenPic\\19_29\\{pic_path}", 1)

    # pic = cv2.imread(f"D:\\JiuYinScreenPic\\dao\\44.png", 1)  # 黑色

    start_time = time.time()
    pic = WindowsCapture().clear_black_area2(pic)
    end_time = time.time()
    execution_time = end_time - start_time
    print("执行时间为: " + str(execution_time) + "秒")

    start_time = time.time()
    b = FindButton().find_pic_by_bigger(bigger_pic_cap=pic, find_type="团练", debug=False)
    print(f"查询到的按钮：{b}")
    end_time = time.time()
    execution_time = end_time - start_time
    print("执行时间为: " + str(execution_time) + "秒")

    """
    当前按钮模板的最低识别率：
    up: 0.71
    down: 0.71
    right: 0.78
    left: 0.81
    J: 0.80
    K:0.9
    """
