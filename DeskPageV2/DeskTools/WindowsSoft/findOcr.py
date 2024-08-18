# coding=utf-8
import os
import time

import numpy as np
from ppocronnx.predict_system import TextSystem
import cv2


class FindPicOCR:

    def __init__(self):
        self.text_sys = TextSystem(use_angle_cls=True,
                                   box_thresh=0.6,
                                   unclip_ratio=1.5)

    @staticmethod
    def _format_img(image: np.ndarray) -> np.ndarray:
        """
        格式化一下通道
        """
        channel = 1 if len(image.shape) == 2 else image.shape[2]
        if channel == 4:
            # 他这个文字识别只支持3通道的，所以要处理一下
            images = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            images = image
        return images

    def find_ocr(self, image: np.ndarray, temp_text: str) -> list or None:
        """
        :param image: 需要查找文字的图片
        :param temp_text: 想要再图片中查询的文字
        :return 查找到的第一个匹配的文字的坐标
        """
        images = self._format_img(image)
        if images is not None:
            res = self.text_sys.detect_and_ocr(images)
            for boxed_result in res:
                if temp_text in boxed_result.ocr_text:
                    rect = boxed_result.box
                    x_center = (rect[0][0] + rect[2][0]) / 2
                    y_center = (rect[0][1] + rect[2][1]) / 2
                    return [int(x_center), int(y_center)]
        return None

    def find_truck_car_ocr(self, image: np.ndarray, temp_text: str) -> list or None:
        """
        :param image: 专门来找镖车
        :param temp_text: 想要再图片中查询的文字
        :return 查找到的第一个匹配的文字的坐标
        """

        images = self._format_img(image)
        if images is not None:
            start_time = time.time()
            # print(f"正在识别图片中的文字“{time.time()}")
            res = self.text_sys.detect_and_ocr(images)
            end_time = time.time()
            elapsed_time = end_time - start_time
            # print("本次识别耗时：", elapsed_time)
            for boxed_result in res:
                if temp_text in boxed_result.ocr_text:
                    rect = boxed_result.box

                    new_cap = images[int(rect[0][1]): int(rect[2][1]), int(rect[0][0]): int(rect[1][0])]
                    h: int = int(new_cap.shape[0])
                    w: int = int(new_cap.shape[1])
                    edges: int = 0
                    element_sum: int = h * w  # 总元素
                    # 先算高度，从底部侧往上算，左下角往上算，碰到非透明的就结束
                    for i in range(h):
                        for n in range(w):
                            if min(new_cap[i][n]) > 150:
                                edges += 1
                    r = edges / element_sum
                    if r < 0.1:
                        # print("白色区域太少")
                        return None
                    x_center = (rect[0][0] + rect[2][0]) / 2
                    y_center = (rect[0][1] + rect[2][1]) / 2
                    # print("有白色区域，镖车识别成功")
                    return [int(x_center), int(y_center)]
        return None

    def find_ocr_arbitrarily(self, image: np.ndarray, temp_text_list: list) -> dict:
        """
        能够匹配到
        :param image: 需要查找文字的图片
        :param temp_text_list: 想要再图片中查询的文字,数组
        :return 查找到的第一个匹配的文字的坐标
        """
        start_time = time.time()
        images = self._format_img(image)
        result: dict = {}
        if images is not None:
            res = self.text_sys.detect_and_ocr(images)
            for boxed_result in res:
                for text in temp_text_list:
                    if text in boxed_result.ocr_text:
                        rect = boxed_result.box
                        x_center = (rect[0][0] + rect[2][0]) / 2
                        y_center = (rect[0][1] + rect[2][1]) / 2
                        result[text] = [int(x_center), int(y_center)]
        end_time = time.time()
        elapsed_time = end_time - start_time
        # print("本次识别耗时：", elapsed_time)
        return result

    def get_person_map(self, image: np.ndarray):
        """
        寻找人物的在地图上的坐标
        """
        pos: int = 0
        area: str = ""
        person_name: str = ""
        if image is not None:
            images = self._format_img(image)
            h: int = int(images.shape[0])
            w: int = int(images.shape[1])
            image_cap = images[int(1): int(h * 0.4), int(w * 0.8): int(w * 0.99)]
            res = self.text_sys.detect_and_ocr(image_cap)

            for res_cap in res:
                if res_cap.ocr_text in ["成都", "金陵", "燕京", "洛阳", "苏州"]:
                    area = res_cap.ocr_text
                elif res_cap.ocr_text.isdigit():
                    pos = int(res_cap.ocr_text)

            image_cap2 = images[int(1): int(h * 0.4), int(1): int(w * 0.4)]
            res2 = self.text_sys.detect_and_ocr(image_cap2)
            for res_cap2 in res2:
                person_name_school = res_cap2.ocr_text
                school_name: list = ["哦眉", "峨眉", "武当"]
                find_value_in_list = lambda s: next((value for value in school_name if value in s), None)
                result = find_value_in_list(person_name_school)
                if result is not None:
                    person_name = person_name_school.replace(result, "")
        return pos, area, person_name

    def find_ocr_all(self, image: np.ndarray):
        images = self._format_img(image)
        if images is not None:
            res = self.text_sys.detect_and_ocr(images)
            return res
        return None
