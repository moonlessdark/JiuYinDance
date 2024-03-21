from collections import namedtuple

import cv2
import numpy as np
from numpy import fromfile

from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic, Config
from DeskPageV2.Utils.load_res import GetConfig
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, WindowsCapture, PicCapture, find_area

FindPicTemplate = namedtuple("FindPicTemplate", ["template_list", "pic_threshold"])


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
        self.dance_area_night = cv2.imdecode(fromfile(self.dance_pic.dance_area_night, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
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
        return self.button_list, self.dance_threshold, True

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
    def sort_button(button_dict: dict):
        """
        给按钮排序
        :param button_dict:
        :return:
        """
        x_list: list = []
        button_key_list = []
        if len(button_dict) > 0:
            for key in button_dict:
                for bs in button_dict.get(key):
                    x_list.append(bs)
            x_list.sort()  # 排序一下，默认按从小打到
            for n in x_list:
                for kk, vv in button_dict.items():
                    if n in vv:  # 如果该坐标在这个key的value数组中
                        button_key_list.append(kk)
        return button_key_list

    def find_pic_by_bigger(self, bigger_pic_cap: PicCapture, find_type="团练", debug: bool = False) -> list:
        """
        从大图里面找小图，并进行从左到右排序
        :param find_type: 查找方式，团练 或者 望辉洲
        :param bigger_pic_cap: 需要找的大图，是已经读取的图片
        :return: list[str]
        """
        bigger_pic = bigger_pic_cap.pic_content
        width, height = bigger_pic_cap.pic_width, bigger_pic_cap.pic_height
        button_dict = {}
        check_button_list, dance_threshold, edges = self.get_dance_pic() if find_type == "团练" else self.get_whz_dance_pic()
        if width == 0 or height == 0:
            return []
        else:
            bigger_pic = bigger_pic[int(height * 0.6):int(height * 1), int(width * 0.2):int(width * 1)]
        if find_type == "团练":
            day: list = find_area(self.dance_area, bigger_pic, threshold=0.4, edge=True)  # 去界面找一下按钮的坐标
            night: list = find_area(self.dance_area_night, bigger_pic, threshold=0.4, edge=True)  # 去界面找一下按钮的坐标

            if len(day) == len(night) == 0:
                """
                如果白天和黑色都没有找到，那就可以放弃了
                """
                button_area_list = []
            elif len(day) == len(night) == 5:
                """
                如果白天和黑色都满足条件，都找到了，那么就把相似度最高的拿出来用
                """
                if day[4] > night[4]:
                    button_area_list = day
                else:
                    button_area_list = night
                    dance_threshold = 0.4
                if debug:
                    print(f"区域识别率: 白天:{day[4]} 晚上:{night[4]}")
            else:
                """
                如果2者找到一个，那么就谁值就用谁
                """
                if len(day) > len(night):
                    button_area_list = day
                else:
                    button_area_list = night
                    dance_threshold = 0.4
                if debug:
                    if len(day) > 0:
                        print(f"区域识别率: 白天{day[4]} 晚上0")
                    else:
                        print(f"区域识别率: 白天0 晚上{night[4]}")
                        
        else:
            button_area_list: list = find_area(self.whz_dance_area, bigger_pic, threshold=dance_threshold, edge=False)  # 去界面找一下按钮的坐标

        if len(button_area_list) == 5:
            """
            如果只找到了一个，那么就是我需要的，如果找到了多个，那就说明精度有问题，太低了
            bigger_pic = bigger_pic[int(height * 0.7):int(height * 0.85), int(width * 0.4):int(width * 0.6)]
            """
            if find_type == "团练":
                bigger_pic = bigger_pic[int(button_area_list[0][1]):int(button_area_list[1][1]), int(button_area_list[1][0]):int(button_area_list[3][0])]
            else:
                # 挖宝、修罗刀的按钮区域长度400
                bigger_pic = bigger_pic[int(button_area_list[0][1]):int(button_area_list[1][1]), int(button_area_list[1][0]-10):int(button_area_list[3][0]+350)]

            # print(f"区域的准确度为{button_area_list[4]}")

            # cv2.imshow("dd", bigger_pic)
            # cv2.waitKey()
            for i in check_button_list:
                button_num_list: list = find_pic(i[1], bigger_pic, threshold=dance_threshold, edge=edges)  # 去界面找一下按钮的坐标
                button_x = []
                for bu in button_num_list:
                    button_x.append(bu[0])  # 把获取到的按钮 x(横坐标) 拿出来，待会要进行排序使用
                    if debug:
                        print(f"按钮 {i[0]} 的相似度为 {bu[2]}")
                if len(button_x) > 0:
                    button_dict[i[0]] = button_x  # {J:[123,456], K:[234,567]}
        return self.sort_button(button_dict)


if __name__ == '__main__':
    import time

    pic_path = "22_42_57.png"
    pic = cv2.imread(f"D:\\JiuYinScreenPic\\check\\{pic_path}", 1)
    # pic = cv2.imread(f"D:\\SoftWare\\Developed\\Projected\\JiuYinDance\\JiuYinScreenPic\\{pic_path}", 1)
    start_time = time.time()
    pic = WindowsCapture().clear_black_area2(pic)
    end_time = time.time()
    execution_time = end_time - start_time
    print("执行时间为: " + str(execution_time) + "秒")

    start_time = time.time()
    b = FindButton().find_pic_by_bigger(bigger_pic_cap=pic, find_type="团练")
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
