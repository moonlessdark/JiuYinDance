# -*- coding:utf-8 -*-
import re
import time

import cv2
import numpy
import numpy as np

from numpy import fromfile

from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.loadResources import GetConfig
from Utils.FindWindowsImage import FindWindowsImageTemplate, WindowsHandle, WindowsCapture


def filter_taben(data: list) -> list:
    """
    过滤一下拓本碎片
    由于切图的原因，拓本碎片和 若水神典的拓本碎片会重复识别
    """
    result = []
    i = 0

    while i < len(data):
        # 检查当前项和下一项是否满足移除条件
        if (i + 1 < len(data) and
                "拓本碎片" in data[i][1] and
                "拓本碎片" in data[i + 1][1] and
                abs(data[i][0] - data[i + 1][0]) < 60):

            # 根据条件决定保留哪个项
            if data[i + 1][1] == "拓本碎片":
                result.append(data[i])
                i += 2
                continue
            elif data[i][1] == "拓本碎片":
                result.append(data[i + 1])
                i += 2
                continue

        # 不满足移除条件，正常添加当前项
        result.append(data[i])
        i += 1

    return result


def process_coordinates(data: list):
    """
    处理坐标数组，根据'两'的X坐标分割数组
    """
    _ding: float = 0  # 锭的Y轴
    _liang: float = 0  # 两的Y轴
    _wen: float = 0  # 文的Y轴

    data.sort()  # 排序一下
    temp: list = data.copy()
    for x in temp:
        if x[1] == "锭":
            _ding = x[0]
            data.remove(x)
        elif x[1] == "两":
            _liang = x[0]
            data.remove(x)
        elif x[1] == "文":
            _wen = x[0]
            data.remove(x)

    _ding_str: str = ""
    if _ding != 0:
        # 如果锭有值
        temp: list = data.copy()
        for d_left in temp:
            if d_left[0] < _ding:
                _ding_str += d_left[1]
                data.remove(d_left)
    _ding_num: int = int(_ding_str) * 1000 if _ding_str != "" else 0

    _liang_str: str = ""
    if _liang != 0:
        temp = data.copy()
        for l_left in temp:
            if l_left[0] < _liang:
                _liang_str += l_left[1]
                data.remove(l_left)
    _liang_num: int = int(_liang_str) * 1 if _liang_str != "" else 0

    _wen_str: str = ""
    if _wen != 0:
        temp = data.copy()
        for w_left in temp:
            if w_left[0] < _wen:
                _wen_str += w_left[1]
                data.remove(w_left)
    _wen_num: float = int(_wen_str) * 0.001 if _wen_str != "" else 0

    sell_price: float = _ding_num + _liang_num + _wen_num
    # print(f"当前售价: {sell_price} 两")
    return sell_price


class FindAuctionMarket:
    """
    世界竞拍
    """

    def __init__(self):
        self.__f = FindPicOCR()

        self.find_pic = FindWindowsImageTemplate()

        __market_config = GetConfig()
        self.__market_pic = __market_config.get_market_pic()

        self.__market_pic_main_line = cv2.imdecode(fromfile(self.__market_pic.main_line, dtype=np.uint8),
                                                   cv2.IMREAD_UNCHANGED)
        self.__market_pic_follow_line = cv2.imdecode(fromfile(self.__market_pic.follow_line, dtype=np.uint8),
                                                     cv2.IMREAD_UNCHANGED)
        self.__market_pic_ok = cv2.imdecode(fromfile(self.__market_pic.ok, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        self.__market_pic_plus_price = cv2.imdecode(fromfile(self.__market_pic.plus_price_10, dtype=np.uint8),
                                                    cv2.IMREAD_UNCHANGED)
        self.__market_pic_plus_price_100 = cv2.imdecode(fromfile(self.__market_pic.plus_price_100, dtype=np.uint8),
                                                        cv2.IMREAD_UNCHANGED)
        self.__market_pic_summit_price = cv2.imdecode(fromfile(self.__market_pic.summit_price, dtype=np.uint8),
                                                      cv2.IMREAD_UNCHANGED)
        self.__market_bidding_man = cv2.imdecode(fromfile(self.__market_pic.bidding_man, dtype=np.uint8),
                                                      cv2.IMREAD_UNCHANGED)
        self.__market_bidder_man = cv2.imdecode(fromfile(self.__market_pic.bidder_man, dtype=np.uint8),
                                                 cv2.IMREAD_UNCHANGED)

        """
        判断钱
        """
        self.number_list: list = [
            ["1", cv2.imdecode(fromfile(self.__market_pic.price_one, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["2", cv2.imdecode(fromfile(self.__market_pic.price_two, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["3", cv2.imdecode(fromfile(self.__market_pic.price_three, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["4", cv2.imdecode(fromfile(self.__market_pic.price_four, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["5", cv2.imdecode(fromfile(self.__market_pic.price_five, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["6", cv2.imdecode(fromfile(self.__market_pic.price_six, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["7", cv2.imdecode(fromfile(self.__market_pic.price_seven, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["8", cv2.imdecode(fromfile(self.__market_pic.price_eight, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["9", cv2.imdecode(fromfile(self.__market_pic.price_nine, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["0", cv2.imdecode(fromfile(self.__market_pic.price_zero, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["锭", cv2.imdecode(fromfile(self.__market_pic.price_ding, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["两", cv2.imdecode(fromfile(self.__market_pic.price_liang, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["文", cv2.imdecode(fromfile(self.__market_pic.price_wen, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
        ]

        # 银子小图标，右侧的就是具体的金额
        self.yin_ding = cv2.imdecode(fromfile(self.__market_pic.price_tag, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

        """
        物品列表
        """
        self.product_list: list = [
            # 拓本碎片
            ["拓本碎片", cv2.imdecode(fromfile(self.__market_pic.ta_ben, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["若水神典拓本碎片", cv2.imdecode(fromfile(self.__market_pic.ta_ben_ruo_shui_shen_dian, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            # 内功残卷
            ["冰心诀", cv2.imdecode(fromfile(self.__market_pic.bing_xin_jue, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["五行功法", cv2.imdecode(fromfile(self.__market_pic.wu_xing_xin_fa, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["残阳功诀", cv2.imdecode(fromfile(self.__market_pic.can_yang, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["寒宵诀", cv2.imdecode(fromfile(self.__market_pic.han_xiao_jue, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["心斋秘箓", cv2.imdecode(fromfile(self.__market_pic.xin_zhai_mi_lu, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["无妄神功", cv2.imdecode(fromfile(self.__market_pic.wu_wang_shen_gong, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["毒哈经", cv2.imdecode(fromfile(self.__market_pic.du_ha_jing, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["混元功", cv2.imdecode(fromfile(self.__market_pic.hun_yuan_gong, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["若水神典", cv2.imdecode(fromfile(self.__market_pic.ruo_shui_shen_dian, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["血海刀罡", cv2.imdecode(fromfile(self.__market_pic.xue_hai_dao_gang, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["醉仙箓", cv2.imdecode(fromfile(self.__market_pic.zui_xian_lu, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            # 古朴武学残卷
            ["魅影剑法", cv2.imdecode(fromfile(self.__market_pic.mei_ying_jian_fa, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["血海魔刀录", cv2.imdecode(fromfile(self.__market_pic.xue_hai_mo_dao_lu, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["焚天令", cv2.imdecode(fromfile(self.__market_pic.fen_tian_ling, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["星河剑律参悟图", cv2.imdecode(fromfile(self.__market_pic.xing_he_jian_lv, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["残破星图", cv2.imdecode(fromfile(self.__market_pic.xing_he_jian_lv_can_po, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["拈花功", cv2.imdecode(fromfile(self.__market_pic.nian_hua_gong, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["打狗八绝", cv2.imdecode(fromfile(self.__market_pic.da_gou_ba_jue, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["太极拳", cv2.imdecode(fromfile(self.__market_pic.tai_ji_quan, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["古朴残卷(绝世高手)", cv2.imdecode(fromfile(self.__market_pic.gu_pu_can_juan_jue_shi_gao_shou, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            # 道具
            ["五彩环", cv2.imdecode(fromfile(self.__market_pic.wu_cai_huan, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["霸主令", cv2.imdecode(fromfile(self.__market_pic.ba_zhu_ling, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["金银花", cv2.imdecode(fromfile(self.__market_pic.jin_yin_hua, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["叫花鸡", cv2.imdecode(fromfile(self.__market_pic.jiao_hua_ji, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
            ["觉梦丹礼包", cv2.imdecode(fromfile(self.__market_pic.jue_meng_dan, dtype=np.uint8), cv2.IMREAD_UNCHANGED)],
        ]

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
        :param button_image:
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

    def check_in_follow_page(self, image: np.ndarray) -> bool:
        """
        检测 我的关注 是不是 高亮的，如果不是高亮的就需要结束竞拍
        """
        __follow_list_res = self.find_pic.get_image_all_rect(image, self.__market_pic_follow_line)
        if __follow_list_res[-1] > 0.85:
            return True
        return False

    def find_plus_price(self, image: np.ndarray):
        """
        寻找加钱的按钮
        只能加 10 或者 100
        """
        __market_pic_plus_price = self.__market_pic_plus_price
        __market_pic_plus_price_100 = self.__market_pic_plus_price_100
        __res_10 = self.find_pic.get_image_all_rect(image, __market_pic_plus_price)
        __res_100 = self.find_pic.get_image_all_rect(image, __market_pic_plus_price_100)

        if int(__res_10[0][0]) < int(__res_100[0][0]):
            return __res_10
        return __res_100

    def find_summit_price(self, image: np.ndarray):
        """
        判断确认出价按钮是否可点击
        """
        __market_pic_summit_price = self.__market_pic_summit_price
        __summit_price = self.find_pic.find_area(image, __market_pic_summit_price)
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
        __summit_price = self.find_pic.get_image_all_rect(image, __market_pic_re_summit_price)
        if __summit_price is not None:
            return __summit_price
        return None

    def find_goods_list(self, image: np.ndarray, scan_product_num: int = 7) -> list:
        """
        查询物品列表
        """

        start_time = time.time()

        __market_pic_main_line = self.__market_pic_main_line
        bigger = image
        res = self.find_pic.find_area(bigger, __market_pic_main_line)

        __goods_find_res: dict = {}
        _prodict_list: list = []

        if res[-1] > 0.8:

            l_t: tuple = res[0]  # 左上
            l_b: tuple = res[1]  # 左下
            r_t: tuple = res[2]  # 右上
            r_b: tuple = res[3]  # 右下
            # cap_pic_all = bigger[int(l_b[1]): int(l_b[1]) + 550, int(l_b[0]): int(r_b[0])]

            scan_product_heigh: int = int(73 * scan_product_num)  # 每个物品的宽度*物品数量，监控的越少速读越快

            # 创建一下掩码
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            # 使用cv2.fillPoly()填充多边形区域为白色，这里我们用四个点定义一个矩形区域
            # 注意：fillPoly的点列表必须是二维的，且每个点是一个列表的形式[[[x1, y1], [x2, y2], ...]] 点位顺序是 左上、右上、右下、左下
            cv2.fillConvexPoly(mask, np.array([(l_t[0], l_t[1]), (r_t[0], r_t[1]), (r_b[0], r_b[1] + scan_product_heigh), (l_b[0], l_b[1] + scan_product_heigh)], dtype=np.int32), 255)

            # 应用掩码到原图
            cap_pic_all = cv2.bitwise_and(image, image, mask=mask)

            for product in self.product_list:
                _product_name: str = product[0]  # 物品名称
                _product_image: np.ndarray = product[1]  # 物品图标

                _product_rect: list = self.find_pic.get_image_all_rect(cap_pic_all, _product_image, threshold=0.9, edge=False)

                if _product_rect is None:
                    # 没有匹配到，跳过下一个
                    continue

                """
                把金额那一行截图出来,那么就可以把对应的当前出价查询出来
                """
                for product_line in _product_rect:

                    l_b_m: float = product_line[0]
                    r_b_m: float = product_line[1]

                    # 先把个产品的这一列内容都给截图出来
                    cap_pic_product_line_content = cap_pic_all[int(r_b_m) + 5: int(r_b_m) + 50, int(l_b_m) - 150: int(l_b_m) + 300]

                    """
                    如果当前商品已经有成交人了，就跳过
                    """
                    _bidder_man_rect: list = self.find_pic.get_image_all_rect(cap_pic_product_line_content, self.__market_bidder_man, threshold=0.9)
                    if _bidder_man_rect is not None:
                        continue

                    """
                    如果当前竞拍人是自己的话，就跳过
                    """
                    if self.__check_person_self(cap_pic_product_line_content):
                        continue

                    """
                    既然都符合条件，那么把价格算一下
                    """
                    cap_pic_all_new = cap_pic_all[int(r_b_m): int(r_b_m) + 30, int(l_b_m):]
                    _money_obj: list = []
                    for m in self.number_list:
                        num: str = m[0]
                        num_pic: np.ndarray = m[1]
                        _num_rect: list = self.find_pic.get_image_all_rect(cap_pic_all_new, num_pic, threshold=0.9)
                        if _num_rect is None:
                            continue

                        for rect in _num_rect:
                            _money_obj.append([rect[0], num])
                    _price: float = process_coordinates(_money_obj)  # 算一下当前产品的价格
                    _prodict_list.append([int(product_line[1]), _product_name, _price, product_line])
        _prodict_list = filter_taben(_prodict_list)
        _prodict_list.sort()
        end_time = time.time()
        # print(f"识别列表：{_prodict_list}，识别耗时: {end_time - start_time}秒")
        return _prodict_list


if __name__ == '__main__':
    find = FindAuctionMarket()
    pic = cv2.imdecode(fromfile(
        "D:\\SoftWare\\Developed\\Projected\\JiuYinDance\\dist\\JiuDancing\\JiuYinScreenPic\\14_24\\14_24_39.png",
        dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    find.find_goods_list(pic)
