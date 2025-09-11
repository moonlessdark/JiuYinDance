import time
from operator import itemgetter

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import FindWindowsImageTemplate
from Utils.loadResources import GetConfig


class FindButton:
    """
    团练授业、
    绿色的上下左右
    """

    def __init__(self):
        self.__find_pic = FindWindowsImageTemplate()
        _dance_grey = GetConfig().get_dance_grey_pic()
        _dance_green = GetConfig().get_dance_green_pic()  # 漠西风涛使用
        _dance_whz = GetConfig().get_dance_whz_pic()  # 挖宝、望辉州
        # 按钮
        self.grey_up_path: str = self.load_pic(_dance_grey.dance_Up)
        self.grey_down_path: str = self.load_pic(_dance_grey.dance_Down)
        self.grey_left_path: str = self.load_pic(_dance_grey.dance_Left)
        self.grey_right_path: str = self.load_pic(_dance_grey.dance_Right)
        self.grey_J_path: str = self.load_pic(_dance_grey.dance_J)
        self.grey_K_path: str = self.load_pic(_dance_grey.dance_K)
        # 按钮(绿色,漠西风涛)
        self.green_up_path: str = self.load_pic(_dance_green.dance_Up)
        self.green_down_path: str = self.load_pic(_dance_green.dance_Down)
        self.green_left_path: str = self.load_pic(_dance_green.dance_Left)
        self.green_right_path: str = self.load_pic(_dance_green.dance_Right)

        self.button_list_grey: list = [
            ("UP", self.grey_up_path),
            ("Down", self.grey_down_path),
            ("Left", self.grey_left_path),
            ("Right", self.grey_right_path),
            ("J", self.grey_J_path),
            ("K", self.grey_K_path)
        ]

        self.button_list_green: list = [
            ("UP", self.green_up_path),
            ("Down", self.green_down_path),
            ("Left", self.green_left_path),
            ("Right", self.green_right_path)
        ]

    @staticmethod
    def load_pic(pic_path: str):
        """
        加载图片
        :param pic_path:
        :return:
        """
        return cv2.imdecode(fromfile(pic_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def find_pic_grey(self, orign_pic: np.ndarray) -> list:
        """
        团练、授业
        :return:
        """
        return self.__find_button_sort(orign_pic, "grey")

    def find_pic_green(self, orign_pic: np.ndarray) -> list:
        """
        绿色的按钮(漠西风涛)
        :param orign_pic:
        :return:
        """
        return self.__find_button_sort(orign_pic, "green")

    def find_button(self, orign_pic: np.ndarray):
        """
        查询团练授业
        :param orign_pic:
        :return:
        """

        # height, width = orign_pic.shape[:2]
        #
        # # 截取图像的一半（假设水平截取）
        # half_height = height // 2
        # half_image = orign_pic[half_height:height, 0:width]

        _bu_list: list = self.__find_button_sort(orign_pic, "grey")
        return _bu_list

    def find_button_green(self, orign_pic: np.ndarray):
        """
        发现绿色的按钮
        :param orign_pic:
        :return:
        """
        # height, width = orign_pic.shape[:2]
        #
        # # 截取图像的一半（假设水平截取）
        # half_height = height // 2
        # half_image = orign_pic[half_height:height, 0:width]

        _bu_list: list = self.__find_button_sort(orign_pic, "green")
        return _bu_list

    def __find_button_sort(self, orign_pic: np.ndarray, dance_type: str) -> list:
        """
        查询并排序
        :param dance_type: grey or green
        :return:
        """
        if dance_type == "grey":
            # 如果是团练授业，用这个支持透明图层的模式，匹配度会更高
            _edge: bool = True
            _btn_list: list = self.button_list_grey
        else:
            # 绿色的按钮，非透明模式，匹配度会更高
            _edge = False
            _btn_list = self.button_list_green

        _search_button_list: list = []
        for _btn_pic_tuple in _btn_list:
            xx = _btn_pic_tuple[1]
            _button_list: list = self.__find_pic.get_image_all_rect(orign_image=orign_pic, read_image=xx, threshold=0.8,
                                                                    edge=_edge)
            if _button_list is None:
                continue
            _button_list.sort()
            if [_btn_pic_tuple[0], _button_list.copy()] not in _search_button_list:
                _search_button_list.append([_btn_pic_tuple[0], _button_list.copy()])
        return self.__optimized_sort(_search_button_list)

    @staticmethod
    def __optimized_sort(btn_list: list) -> list:
        """
        给按钮排序
        :param btn_list:
        :return:
        """
        flat_data = []
        for char, coord in btn_list:
            flat_data.extend((x, char) for x, _ in coord)
        return [char for _, char in sorted(flat_data, key=itemgetter(0))]


if __name__ == '__main__':
    # button_list: list = [["J", [(100, 30), (260, 30), (180, 30), (0, 30), (300, 30)]],
    #                      ["K", [(80, 30), (220, 30)]],
    #                      ["L", [(40, 30), (140, 30), (260, 30)]]
    #                      ]
    # # s = ["L", "K", "J", "L", "J", "K", "L"]
    # D = FindButton()
    # hw_id: int = 2557618
    # while 1:
    #     x = D.find_pic_grey(hw_id)
    #     if len(x) == 0:
    #         continue
    #     print(x)
    #     time.sleep(0.5)

    def load_pic(pic_path):
        return cv2.imdecode(fromfile(pic_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    xxx = FindButton()
    saa = FindWindowsImageTemplate().get_image_all_rect(orign_image=load_pic(r"D:\2-5-0.png"),
                                                        read_image=load_pic(r'D:\SoftWare\Developed\Projected\JiuYinDnaceRemake\Resources\ImageTemplate\PicPointNum\点.png'),
                                                        threshold=0.9)
    print(saa)
