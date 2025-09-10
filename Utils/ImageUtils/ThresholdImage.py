import cv2 as cv
import numpy as np


"""
图片二值化
"""


# 全局
def threshold_image(image: np.array):

    """
    全局模式
    :param image:
    :return:
    """
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    ret, binary = cv.threshold(src=gray, thresh=0, maxval=255, type=cv.THRESH_BINARY | cv.THRESH_OTSU)
    # ret, binary = cv.threshold(src=gray, thresh=0, maxval=255, type=cv.THRESH_BINARY | cv.THRESH_TRIANGLE)
    # ret, binary = cv.threshold(src=gray, thresh=115, maxval=255, type=cv.THRESH_BINARY)
    # ret, binary = cv.threshold(src=gray, thresh=127, maxval=255, type=cv.THRESH_BINARY_INV)  # 相反
    # ret, binary = cv.threshold(src=gray, thresh=127, maxval=255, type=cv.THRESH_TRUNC)
    # ret, binary = cv.threshold(src=gray, thresh=115, maxval=255, type=cv.THRESH_TOZERO)
    # print(f'threshold value：{ret}')  # 阈值    看图像信息丢失情况
    return binary


# 局部  自适应阈值
def local_image(image):
    """
    自适应
    :param image:
    :return:
    """
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    # dst = cv.adaptiveThreshold(src=gray, maxValue=255, adaptiveMethod=cv.ADAPTIVE_THRESH_MEAN_C,
    #                            thresholdType=cv.THRESH_BINARY, blockSize=25, C=10)     # blockSize必须是奇数  C 常量
    dst = cv.adaptiveThreshold(src=gray, maxValue=255, adaptiveMethod=cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                               thresholdType=cv.THRESH_BINARY, blockSize=25, C=10)  # blockSize必须是奇数  C 常量
    return dst


# 自定义   均值作为阈值
def custom_image(image, mean: int = 1, max_val: int = 255):
    """
    自定义，如果mead不传的话，表示均值
    :param max_val:
    :param image:
    :param mean:
    :return:
    """
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    m = np.reshape(gray, [1, h * w])
    if mean is None:
        # 去个平均值
        mean = m.sum() / (w * h)
    ret, binary = cv.threshold(gray, mean, max_val, cv.THRESH_BINARY)
    return binary
