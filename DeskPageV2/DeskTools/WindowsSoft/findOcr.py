# coding=utf-8
import os
import time

import numpy as np
from numpy import fromfile, uint8
from ppocronnx.predict_system import TextSystem
import cv2


class FindPicOCR:

    def __init__(self):
        self.text_sys = TextSystem()

    def find_ocr(self, image: np.ndarray, temp_text: str) -> list or None:
        """
        :param image: 需要查找文字的图片
        :param temp_text: 想要再图片中查询的文字
        :return 查找到的第一个匹配的文字的坐标
        """
        channel = 1 if len(image.shape) == 2 else image.shape[2]
        if channel == 4:
            # 他这个文字识别只支持3通道的，所以要处理一下
            images = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            images = image
        if images is not None:
            res = self.text_sys.detect_and_ocr(images)
            for boxed_result in res:
                if temp_text in boxed_result.ocr_text:
                    rect = boxed_result.box
                    x_center = (rect[0][0] + rect[2][0]) / 2
                    y_center = (rect[0][1] + rect[2][1]) / 2
                    return [int(x_center), int(y_center)]
        return None

    def find_ocr_arbitrarily(self, image: np.ndarray, temp_text_list: list) -> dict:
        """
        能够匹配到
        :param image: 需要查找文字的图片
        :param temp_text_list: 想要再图片中查询的文字,数组
        :return 查找到的第一个匹配的文字的坐标
        """
        channel = 1 if len(image.shape) == 2 else image.shape[2]
        if channel == 4:
            # 他这个文字识别只支持3通道的，所以要处理一下
            images = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            images = image
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
        return result

    def get_person_map(self, image: np.ndarray):
        """
        寻找人物的在地图上的坐标
        """
        channel = 1 if len(image.shape) == 2 else image.shape[2]
        if channel == 4:
            # 他这个文字识别只支持3通道的，所以要处理一下
            images = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            images = image
        h: int = int(images.shape[0])
        w: int = int(images.shape[1])
        image_cap = images[int(1): int(h * 0.4), int(w * 0.8): int(w * 0.99)]
        res = self.text_sys.detect_and_ocr(image_cap)

        pos: int = 0
        area: str = ""
        person_name: str = ""
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
