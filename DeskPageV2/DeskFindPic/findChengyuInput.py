import json

import cv2
import numpy as np
from numpy import fromfile

from DeskPageV2.DeskTools.WindowsSoft.findOcr import FindPicOCR
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, find_area
from DeskPageV2.Utils.load_res import GetConfig


def bitwise_and(image: np.ndarray, mask_position: tuple):
    """
    给图片加个掩膜遮罩，避免干扰。保留目标区域，其他的区域都遮住
    :param image: 图片
    :param mask_position: # 指定掩膜位置（左上角坐标， 右下角坐标） mask_position = (50, 50, 200, 200)
    """
    if image is not None:
        # print(image.shape[0], image.shape[1])
        # 绘制掩膜（矩形）
        # 参数分别为：图像、矩形左上角坐标、矩形右下角坐标、颜色（BGR）、线条粗细
        # cv2.rectangle(image, mask_position[0:2], mask_position[2:4], (0, 255, 0), -1)  # 遮住目标区域
        # 遮住左侧
        image = cv2.rectangle(image, [0, 0], [mask_position[0], image.shape[1]], (0, 255, 0), -1)
        # 遮住右侧
        image = cv2.rectangle(image, [mask_position[2], 0], [image.shape[1], image.shape[0]], (0, 255, 0), -1)
        # 遮住上面
        image = cv2.rectangle(image, [0, 0], [image.shape[1], mask_position[1]], (0, 255, 0), -1)
        # 遮住下面
        image = cv2.rectangle(image, [0, mask_position[3]], [image.shape[1], image.shape[0]], (0, 255, 0), -1)
    return image


class ChengYuInput:

    def __init__(self):
        self.__f = FindPicOCR()
        __chengyu_pic = GetConfig().get_chengyu_pic()

        self.chengyu_pic_up_move = cv2.imdecode(fromfile(__chengyu_pic.up_move, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.chengyu_pic_down_move = cv2.imdecode(fromfile(__chengyu_pic.down_move, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.chengyu_pic_unlock = cv2.imdecode(fromfile(__chengyu_pic.unlock, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.chengyu_pic_l_r_tag = cv2.imdecode(fromfile(__chengyu_pic.l_r_tag, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.chengyu_pic_file_json = __chengyu_pic.idiom

        self._chengyu_json_load: list = []

    @staticmethod
    def less_str_chengyu(str_list) -> list:
        """
        由于OCR识别精度的问题，导致部分词语识别失败，所以会产生确实。这里可以补充一下
        """
        less_chengyu: list = [
            (['纷', '至', '来'], '沓'),
            (['莫', '衷', '是'], '一'),
            (['老', '奸', '巨'], '猾'),
            (['患', '难', '与'], '共'),
            (['云', '覆', '雨'], '翻')
        ]
        for chengyu_str in less_chengyu:
            if set(list(chengyu_str[0])).issubset(str_list) is True:
                if chengyu_str[1] not in str_list:
                    str_list.append(chengyu_str[1])
        return str_list

    def get_chengyu_string_key(self, image: np.ndarray):
        """
        识别游戏画面中出现的成语文字
        """

        res_up = find_area(self.chengyu_pic_up_move, image)
        res_down = find_area(self.chengyu_pic_down_move, image)
        res_l_r = find_pic(self.chengyu_pic_l_r_tag, image)
        res_unlock = find_area(self.chengyu_pic_unlock, image)

        res_up_x, res_up_y, res_down_x, res_down_y, res_unlock_x, res_unlock_y, res_left_x, res_right_x = 0, 0, 0, 0, 0, 0, 0, 0

        if res_up[-1] > 0:
            # 如果找到了 上 的图标
            res_up_x, res_up_y = res_up[0][0], res_up[0][1]
        if res_down[-1] > 0:
            # 找到 下 的图标
            res_down_x, res_down_y = res_down[0][0], res_down[0][1]
        if res_unlock[-1] > 0:
            # 找到尝试解锁的按钮
            res_unlock_x, res_unlock_y = res_unlock[2][0], res_unlock[2][1]
        if len(res_l_r) > 0:
            x_list: list = []
            for pos in res_l_r:
                x_list.append(pos[0])
            res_left_x = min(x_list)
            res_right_x = max(x_list)

        # 拼接一下坐标,上部分
        _chengyu_pos_up_x, _chengyu_pos_up_y = int(res_left_x), int(res_up_y)
        _chengyu_pos_down_x, _chengyu_pos_down_y = int(res_unlock_x), int(res_unlock_y)

        """
        确定上半部分边框坐标
        """
        # 左上角pos
        _chengyu_wait_left_up_x, _chengyu_wait_left_up_y = int(res_left_x), int(res_up_y)
        # 左下角pos
        _chengyu_wait_left_down_x, _chengyu_wait_left_down_y = int(res_left_x), int(res_down_y)
        # 右上角pos
        _chengyu_wait_right_up_x, _chengyu_wait_right_up_y = int(res_unlock_x), int(res_up_y)
        # 右下角pos
        _chengyu_wait_right_down_x, _chengyu_wait_right_down_y = int(res_unlock_x), int(res_down_y)

        # print(f"左上角:{_chengyu_wait_left_up_x}_{_chengyu_wait_left_up_y}, 右上角:{_chengyu_wait_right_up_x}_{_chengyu_wait_right_up_y}")
        # print(f"左下角:{_chengyu_wait_left_down_x}_{_chengyu_wait_left_down_y}, 右下角:{_chengyu_wait_right_down_x}_{_chengyu_wait_right_down_y}")

        """
        确定下半部分的边框坐标
        """
        # 左上角pos
        _chengyu_input_left_up_x, _chengyu_input_left_up_y = int(res_left_x), int(res_down_y)
        # 左下角pos
        _chengyu_input_left_down_x, _chengyu_input_left_down_y = int(res_left_x), int(res_unlock_y)
        # 右上角pos
        _chengyu_input_right_up_x, _chengyu_input_right_up_y = int(res_unlock_x), int(res_down_y)
        # 右下角pos
        _chengyu_input_right_down_x, _chengyu_input_right_down_y = int(res_unlock_x), int(res_unlock_y)

        print(f"左上角:{_chengyu_input_left_up_x}_{_chengyu_input_left_up_y}, 右上角:{_chengyu_input_right_up_x}_{_chengyu_input_right_up_y}")
        print(f"左下角:{_chengyu_input_left_down_x}_{_chengyu_input_left_down_y}, 右下角:{_chengyu_input_right_down_x}_{_chengyu_input_right_down_y}")


        up_pic = bitwise_and(image, (_chengyu_pos_up_x, _chengyu_pos_up_y, _chengyu_pos_down_x, _chengyu_pos_down_y))

        # cv2.imshow("s", up_pic)
        # cv2.waitKey()

        res = FindPicOCR().find_ocr_all(up_pic)
        # print(res)
        # 过滤一下，上半部分和下半部分,区分的坐标是 down_tag的坐标

        up_str_list: list = []
        down_str_list: list = []

        for res_str in res:
            if res_str is None:
                continue
            res_ocr_text = res_str.ocr_text
            # print(f"{res_ocr_text}{res_str.box}")
            # 识别异常的文字，先慢慢累积
            if "知口" == res_ocr_text:
                res_ocr_text = '知'

            if len(res_ocr_text) > 1:
                continue

            if 'o' in res_ocr_text:
                continue

            res_y = res_str.box[0][1]
            if res_y <= res_down_y:
                up_str_list.append(res_ocr_text)

                """
                计算文字坐标。
                box中的值如下:
                [[531. 197.]
                [562. 197.]
                [562. 221.]
                [531. 221.]]
                """
                _str_pox_center_x = int((res_str.box[0][0] + res_str.box[1][0]) / 2)
                _str_pox_center_y = int((res_str.box[1][1] + res_str.box[2][1]) / 2)
                """
                计算文字在第几行第几列
                每个文字的边框为: 长70,宽60
                """

                # row, columns
                _str_columns, _str_row = int(np.ceil((_str_pox_center_x - _chengyu_wait_left_up_x) / 70)), int(
                    np.ceil((_str_pox_center_y - _chengyu_wait_left_up_y) / 60))
                print(f"{res_ocr_text}的坐标:{_str_pox_center_x}_{_str_pox_center_y}, 行列为{_str_row}_{_str_columns}")
            else:
                down_str_list.append(res_ocr_text)
                _str_pox_center_x = int((res_str.box[0][0] + res_str.box[1][0]) / 2)
                _str_pox_center_y = int((res_str.box[1][1] + res_str.box[2][1]) / 2)
                _str_columns, _str_row = int(np.ceil((_str_pox_center_x - _chengyu_input_left_down_x) / 70)), int(
                    np.ceil((_str_pox_center_y - _chengyu_input_left_up_y - 20) / 60))
                print(f"{res_ocr_text}的坐标:{_str_pox_center_x}_{_str_pox_center_y}, 行列为{_str_row}_{_str_columns}")

        # print(f"上部分:{up_str_list}, \n下部分:{down_str_list}")
        return up_str_list, down_str_list

    def check_chengyu(self, image: np.ndarray) -> list:
        """
        拼接成语
        """
        if len(self._chengyu_json_load) == 0:
            with open(self.chengyu_pic_file_json, "r", encoding='UTF-8') as f:
                data = json.load(f)

                for dict_key in data:
                    self._chengyu_json_load.append(dict_key.get("word"))

        up_str, down_str = self.get_chengyu_string_key(image)

        _key_input = up_str
        _key_wait = down_str

        new_list: list = _key_wait + _key_input

        new_list = self.less_str_chengyu(new_list)

        result_list: list = []
        for chengyu_str in self._chengyu_json_load:
            str_result_sum: int = 0

            for chengyu_len_str in chengyu_str:
                if chengyu_len_str in new_list:
                    str_result_sum += 1
            if len(chengyu_str) > 4:
                continue
            if str_result_sum >= 4:
                result_list.append(chengyu_str)
        return list(set(result_list))

    def search_chengyu(self, key_str: list) -> list:
        """
        查询成语
        """
        if len(self._chengyu_json_load) == 0:
            with open(self.chengyu_pic_file_json, "r", encoding='UTF-8') as f:
                data = json.load(f)

                for dict_key in data:
                    self._chengyu_json_load.append(dict_key.get("word"))
        _wait_search_key: list = list(set(key_str))  # 顺便去重一下

        if len(_wait_search_key) == 0:
            return []
        result_list: list = []
        for chengyu_str in self._chengyu_json_load:
            if len(chengyu_str) != 4:
                # 我们只查询4个字的成语
                continue
            _is_equal_num: int = 0
            for wai_s in chengyu_str:
                if wai_s in _wait_search_key:
                    # 如果出现待查询的字符不在此成语中
                    _is_equal_num += 1
            if _is_equal_num == 4:
                result_list.append(chengyu_str)
        return sorted(list(set(result_list)))


if __name__ == '__main__':
    o_pic = cv2.imread('D:\\SoftWare\\Game\\SnailGames\\JiuDancing\\JiuYinScreenPic\\20_59\\20_59_15.png')
    ChengYuInput().check_chengyu(o_pic)