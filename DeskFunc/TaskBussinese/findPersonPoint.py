from operator import itemgetter

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import FindWindowsImageTemplate
from Utils.dataClass import MapPointNum
from Utils.loadResources import GetConfig


class FindPoint:
    """
    团练授业、
    绿色的上下左右
    """

    def __init__(self):
        self.__find_pic = FindWindowsImageTemplate()
        _num: MapPointNum = GetConfig().find_person_point()

        self.num_list: list = [
            ("0", _num.zero),
            ("1", _num.one),
            ("2", _num.two),
            ("3", _num.three),
            ("4", _num.four),
            ("5", _num.five),
            ("6", _num.six),
            ("7", _num.seven),
            ("8", _num.eight),
            ("9", _num.nine),
            ("DH", _num.d),  # 逗号
            ("FS", _num.f),  # 负数
        ]

    @staticmethod
    def load_pic(pic_path: str):
        """
        加载图片
        :param pic_path:
        :return:
        """
        return cv2.imdecode(fromfile(pic_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def find_button_sort(self, orign_pic: np.ndarray) -> str:
        """
        查询并排序
        :return:
        """

        _search_button_list: list = []
        for _btn_pic_tuple in self.num_list:
            xx = _btn_pic_tuple[1]
            _button_list: list = self.__find_pic.get_windows_image_all_rect(source_image=orign_pic, template_image=xx, threshold=0.9)
            if _button_list is None:
                continue
            _button_list.sort()
            if [_btn_pic_tuple[0], _button_list.copy()] not in _search_button_list:
                _search_button_list.append([_btn_pic_tuple[0], _button_list.copy()])
        return self._optimized_sort(_search_button_list)

    @staticmethod
    def _optimized_sort(btn_list: list) -> str:
        """
        给按钮排序
        :param btn_list:
        :return:
        """
        flat_data = []
        for char, coord in btn_list:
            flat_data.extend((x, char) for x, _ in coord)
        str_l: list = [char for _, char in sorted(flat_data, key=itemgetter(0))]
        str_l = ['-' if x == "FS" else x for x in str_l]
        str_l = [',' if x == "DH" else x for x in str_l]

        # 一些数据处理，可能识别有点问题
        if str_l[-1] == "-":
            str_l.pop(-1)

        return "".join(str_l)


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

    xxx = FindPoint()
    saa = xxx.find_button_sort(xxx.load_pic("D:\\1222.png"))
    print(saa)
