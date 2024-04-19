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
