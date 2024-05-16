# -*- coding:utf-8 -*-
import datetime
import re
import threading
import time

import cv2
import numpy
import numpy as np
from typing import List

from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.findOcr import FindPicOCR
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, find_area


class FindAuctionMarket:

    def __init__(self):
        self.__f = FindPicOCR()

    @staticmethod
    def __check_person_self(person_image: np.ndarray):
        """
        检测当前竞拍人是不是账号本人
        :param person_image:
        """
        hsv_image = cv2.cvtColor(person_image, cv2.COLOR_BGR2HSV)

        # 定义绿色的范围
        lower_red = np.array([35, 50, 100])
        upper_red = np.array([77, 255, 255])

        # 创建掩膜
        mask = cv2.inRange(hsv_image, lower_red, upper_red)

        # 计算非零像素的数量
        red_exists = cv2.countNonZero(mask)

        # 如果非零像素的数量大于某个阈值，则认为红色存在
        if red_exists > 100:
            print("---当前物品竞拍成功")
            return True
        return False

    def find_goods(self, image: np.ndarray):
        """
        查找物品
        """
        small = cv2.imread(
            "D:\\SoftWare\\Developed\\Projected\\JiuYinDance\\DeskPageV2\\Resources\\AuctionMarket\\main_line_v2.png")
        bigger = image
        start_time = time.time()
        res = find_area(small, bigger)
        if res[-1] > 0.8:
            l_b: tuple = res[1]
            r_b: tuple = res[3]
            cap_pic_all = bigger[int(l_b[1]): int(l_b[1]) + 550, int(l_b[0]): int(r_b[0])]

            cap_pic_list: list = []
            tx = self.__f.find_ocr_all(cap_pic_all)
            res_list: list = []  # 过滤一下

            # 处理小图的逻辑
            for good_index in range(7):
                good_list: list = []
                for index in tx:
                    g_h = index.box[0][1]
                    if good_index * 75 < g_h < (good_index + 1) * 75:
                        good_list.append(index)
                res_list.append(good_list)
            if len(res_list) > 0:
                get_numbers = lambda s: re.findall(r'\d+', s)
                for goods_content in res_list:

                    goods_name: str = goods_content[0].ocr_text
                    __p: str = goods_content[-1].ocr_text

                    if "成交者" in __p:
                        break

                    person: str = "无" if __p.split("竞价者：")[1] in ['一', ""] else __p.split("竞价者：")[1]

                    if len(goods_content) == 3:
                        price_temp = goods_content[1].ocr_text
                        if "两" not in price_temp:
                            # 妈耶，上1000两银子了，有钱人啊
                            price_temp += "000"
                        price = int(''.join(map(str, get_numbers(price_temp))))
                    else:
                        price_str: str = ""
                        for price_index in goods_content[1:-1]:
                            price_temp: str = price_index.ocr_text
                            price_str += price_temp
                        price = int(''.join(map(str, get_numbers(price_str))))
                    print(f"物品: {goods_name}, 价格: {price} 两, 竞拍人: {person}")
                    good_pos: numpy.ndarray = goods_content[-1].box  # 坐标
                    person_pic = cap_pic_all[int(good_pos[0][1]): int(good_pos[3][1]),
                                 int(good_pos[0][0]): int(good_pos[1][0])]
                    self.__check_person_self(person_pic)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"本次识别耗时: {round(elapsed_time, 2)} 秒")
            # cv2.imshow("ss", cap_pic_all)
            # cv2.waitKey()


if __name__ == '__main__':
    find = FindAuctionMarket()
    pic = cv2.imread("D:\\SoftWare\\Game\\SnailGames\\JiuDancing\\JiuYinScreenPic\\21_34\\21_35_37.png")
    find.find_goods(pic)

