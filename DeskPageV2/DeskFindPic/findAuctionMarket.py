# -*- coding:utf-8 -*-
import datetime
import re
import threading
import time

import cv2
import numpy
import numpy as np
from typing import List

from numpy import fromfile

from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.findOcr import FindPicOCR
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, find_area
from DeskPageV2.Utils.load_res import GetConfig


class FindAuctionMarket:

    def __init__(self):
        self.__f = FindPicOCR()

        __market_config = GetConfig()
        self.__market_pic = __market_config.get_market_pic()

        self.__market_pic_main_line = cv2.imdecode(fromfile(self.__market_pic.main_line, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.__market_pic_ok = cv2.imdecode(fromfile(self.__market_pic.ok, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.__market_pic_plus_price = cv2.imdecode(fromfile(self.__market_pic.plus_price_10, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.__market_pic_plus_price_100 = cv2.imdecode(fromfile(self.__market_pic.plus_price_100, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.__market_pic_summit_price = cv2.imdecode(fromfile(self.__market_pic.summit_price, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

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

        # 如果非零像素的数量大于某个阈值，则认为绿色存在
        if red_exists > 100:
            return True
        return False

    @staticmethod
    def __check_summit_price_clicked(button_image: np.ndarray):
        """
        检测确认出价按钮是否高亮可点击
        :param person_image:
        """
        hsv_image = cv2.cvtColor(button_image, cv2.COLOR_BGR2HSV)

        # 定义红色的范围

        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])

        # 创建掩膜
        mask = cv2.inRange(hsv_image, lower_red, upper_red)

        # 计算非零像素的数量
        red_exists = cv2.countNonZero(mask)

        # 如果非零像素的数量大于某个阈值，则认为色存在
        if red_exists > 100:
            return True
        return False

    def find_plus_price(self, image: np.ndarray):
        """
        寻找加钱的按钮
        只能加 10 或者 100
        """
        __market_pic_plus_price = self.__market_pic_plus_price
        __market_pic_plus_price_100 = self.__market_pic_plus_price_100
        __res_10 = find_area(__market_pic_plus_price, image)
        __res_100 = find_area(__market_pic_plus_price_100, image)

        if int(__res_10[0][0]) < int(__res_100[0][0]):
            return __res_10
        return __res_100

    def find_summit_price(self, image: np.ndarray):
        """
        判断确认出价按钮是否可点击
        """
        __market_pic_summit_price = self.__market_pic_summit_price
        __summit_price = find_area(__market_pic_summit_price, image)
        __button_pic = image[int(__summit_price[0][1]):int(__summit_price[1][1]),
                             int(__summit_price[1][0]):int(__summit_price[3][0])]
        if self.__check_summit_price_clicked(__button_pic):
            return __summit_price
        return None

    def find_re_summit_price(self, image: np.ndarray):
        """
        判断确认出价按钮是否可点击
        """
        __market_pic_re_summit_price = self.__market_pic_ok
        __summit_price = find_area(__market_pic_re_summit_price, image)
        if __summit_price[-1] > 0:
            return __summit_price
        return None

    def find_goods(self, image: np.ndarray) -> dict:
        """
        查找物品
        """
        # small = cv2.imread(
        #     "D:\\SoftWare\\Developed\\Projected\\JiuYinDance\\DeskPageV2\\Resources\\AuctionMarket\\main_line_v2.png")
        __market_pic_main_line = self.__market_pic_main_line
        bigger = image
        start_time = time.time()
        res = find_area(__market_pic_main_line, bigger)

        __goods_find_res: dict = {}

        if res[-1] > 0.8:
            l_b: tuple = res[1]
            r_b: tuple = res[3]
            cap_pic_all = bigger[int(l_b[1]): int(l_b[1]) + 550, int(l_b[0]): int(r_b[0])]

            tx = self.__f.find_ocr_all(cap_pic_all)
            res_list: list = []  # 过滤一下
            good_pic_pos: list = []  # 图片中的坐标，后续需要转为 桌面坐标

            index_num: int = 0
            # 处理小图的逻辑
            for good_index in range(7):
                good_list: list = []
                for index in tx:
                    g_h = index.box[0][1]
                    if good_index * 75 < g_h < (good_index + 1) * 75:
                        good_list.append(index)
                cap_pic_pos = [(int(l_b[0]), int(l_b[1]) + index_num * 75),
                               (int(l_b[0]), int(l_b[1]) + (index_num + 1) * 75),
                               (int(r_b[0]), int(r_b[1]) + index_num * 75),
                               (int(r_b[0]), int(r_b[1]) + (index_num + 1) * 75)]
                index_num += 1
                res_list.append(good_list)
                good_pic_pos.append(cap_pic_pos)
            if len(res_list) > 0:
                get_numbers = lambda s: re.findall(r'\d+', s)
                __goods_index: int = 1
                for goods_content, goods_pic_pos in zip(res_list, good_pic_pos):

                    if len(goods_content) == 0:
                        break
                    goods_name: str = goods_content[0].ocr_text
                    __p: str = goods_content[-1].ocr_text

                    if "成交者" in __p:
                        break

                    person: str = "无" if __p.split("竞价者：")[1] in ['一', ""] else __p.split("竞价者：")[1]
                    price_str: str = ""
                    price: int = 0
                    for price_index in goods_content[1:-1]:
                        price_temp: str = price_index.ocr_text
                        price_str += price_temp
                        # print(f"遍历的价格：{price_str}")

                    thousands_list: list = ["锭", "锁", "键"]
                    for thousand_str in thousands_list:
                        if thousand_str in price_str:
                            res_price: list = price_str.split(thousand_str)
                            thousand = int(''.join(map(str, get_numbers(res_price[0])))) * 1000
                            hundred = 0
                            if res_price[1] != "":
                                hundred = int(''.join(map(str, get_numbers(res_price[1]))))
                            price = thousand + hundred
                    if price == 0:
                        price = int(''.join(map(str, get_numbers(price_str))))

                    if price < 10:
                        # 如果出现了价格小于10的，因为起拍价就是10L，小于10就说明是没有识别到“锭”，给他补一下
                        price = price * 1000

                    good_pos: numpy.ndarray = goods_content[-1].box  # 坐标
                    person_pic = cap_pic_all[int(good_pos[0][1]): int(good_pos[3][1]),
                                 int(good_pos[0][0]): int(good_pos[1][0])]
                    is_self = 1 if self.__check_person_self(person_pic) else 0
                    print(f"物品: {goods_name}, 价格: {price} 两, 竞拍人: {person}, 是否加价成功: {is_self}")
                    __goods_find_res[f"goods_{__goods_index}"] = {"goods_pic_pos": goods_pic_pos,
                                                                  "goods_name": goods_name,
                                                                  "goods_price": price,
                                                                  "goods_person": person,
                                                                  "goods_person_is_self": is_self}
                    __goods_index += 1
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"本次识别耗时: {round(elapsed_time, 2)} 秒")
            # cv2.imshow("ss", cap_pic_all)
            # cv2.waitKey()
            return __goods_find_res


if __name__ == '__main__':
    find = FindAuctionMarket()
    pic = cv2.imread("D:\\SoftWare\\Game\\SnailGames\\JiuDancing\\JiuYinScreenPic\\21_34\\21_35_37.png")
    find.find_goods(pic)
