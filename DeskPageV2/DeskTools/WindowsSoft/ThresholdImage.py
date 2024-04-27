import cv2 as cv
import numpy as np


# 全局
def threshold_image(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    ret, binary = cv.threshold(src=gray, thresh=0, maxval=255, type=cv.THRESH_BINARY | cv.THRESH_OTSU)
    # ret, binary = cv.threshold(src=gray, thresh=0, maxval=255, type=cv.THRESH_BINARY | cv.THRESH_TRIANGLE)
    # ret, binary = cv.threshold(src=gray, thresh=115, maxval=255, type=cv.THRESH_BINARY)
    # ret, binary = cv.threshold(src=gray, thresh=127, maxval=255, type=cv.THRESH_BINARY_INV)  # 相反
    # ret, binary = cv.threshold(src=gray, thresh=127, maxval=255, type=cv.THRESH_TRUNC)
    # ret, binary = cv.threshold(src=gray, thresh=115, maxval=255, type=cv.THRESH_TOZERO)
    # print(f'threshold value：{ret}')  # 阈值    看图像信息丢失情况
    # cv.imshow('threshold binary image', binary)
    # cv.imwrite("./01.png", binary, [int(cv.IMWRITE_PNG_COMPRESSION), 0])
    return binary


# 局部  自适应阈值
def local_image(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    # dst = cv.adaptiveThreshold(src=gray, maxValue=255, adaptiveMethod=cv.ADAPTIVE_THRESH_MEAN_C,
    #                      thresholdType=cv.THRESH_BINARY, blockSize=25, C=10)     # blockSize必须是奇数  C 常量
    dst = cv.adaptiveThreshold(src=gray, maxValue=255, adaptiveMethod=cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                               thresholdType=cv.THRESH_BINARY, blockSize=25, C=10)  # blockSize必须是奇数  C 常量

    cv.imshow('local binary image', dst)
    cv.waitKey()
    # cv.imwrite("../02.png", dst, [int(cv.IMWRITE_PNG_COMPRESSION), 0])
    # cv.imshow('local_image', dst)
    return dst


# 自定义   均值作为阈值
def custom_image(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    m = np.reshape(gray, [1, h * w])
    mean = m.sum() / (w * h)
    # print(f'mean：{mean}')
    ret, binary = cv.threshold(gray, mean, 255, cv.THRESH_BINARY)
    # cv.imshow('custom binary image', binary)
    # cv.imwrite("../03.png", binary, [int(cv.IMWRITE_PNG_COMPRESSION), 0])
    return binary


if __name__ == '__main__':
    pic_name: str = "D"
    src = cv.imread(f'/Users/luojun/Downloads/Doa/{pic_name}.PNG')
    height, width = src.shape[:2]

    # src = src[int(height * 0.70):int(height * 0.78), int(width * 0.35):int(width * 0.65)]
    # cv.imshow('input image', src)
    threshold_image(src)
    # local_image(src)
    # custom_image(src)
    # cv.waitKey(0)
    cv.destroyAllWindows()
