# coding: utf-8
"""
世界竞拍识别。

1. 用“主分割线”定位第一页物品列表区域；
2. 用物品图标模板找出设置了最高价的物品；
3. 跳过已有成交人、跳过竞拍人是自己的物品；
4. 用数字 + 锭/两/文模板拼接当前价格；
5. 用加价按钮、确认出价按钮、二次确认按钮模板完成出价。

价格数字模板很小，v2 增加了按位置去重，避免 0/8、6/9 这类相似数字被重复叠加。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from Core.vision.template import find_all_template, load_template
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.imageTools import deduplicate_points, to_bgr

# (物品显示名, 资源字段名)
_PRODUCT_FIELDS: tuple[tuple[str, str], ...] = (
    ("拓本碎片", "ta_ben"),
    ("若水神典拓本碎片", "ta_ben_ruo_shui_shen_dian"),
    ("冰心诀", "bing_xin_jue"),
    ("五行功法", "wu_xing_xin_fa"),
    ("残阳功诀", "can_yang"),
    ("寒宵诀", "han_xiao_jue"),
    ("心斋秘箓", "xin_zhai_mi_lu"),
    ("无妄神功", "wu_wang_shen_gong"),
    ("毒哈经", "du_ha_jing"),
    ("混元功", "hun_yuan_gong"),
    ("若水神典", "ruo_shui_shen_dian"),
    ("血海刀罡", "xue_hai_dao_gang"),
    ("醉仙箓", "zui_xian_lu"),
    ("魅影剑法", "mei_ying_jian_fa"),
    ("血海魔刀录", "xue_hai_mo_dao_lu"),
    ("焚天令", "fen_tian_ling"),
    ("星河剑律参悟图", "xing_he_jian_lv"),
    ("残破星图", "xing_he_jian_lv_can_po"),
    ("拈花功", "nian_hua_gong"),
    ("打狗八绝", "da_gou_ba_jue"),
    ("太极拳", "tai_ji_quan"),
    ("古朴残卷(绝世高手)", "gu_pu_can_juan_jue_shi_gao_shou"),
    ("五彩环", "wu_cai_huan"),
    ("霸主令", "ba_zhu_ling"),
    ("金银花", "jin_yin_hua"),
    ("叫花鸡", "jiao_hua_ji"),
    ("觉梦丹礼包", "jue_meng_dan"),
)

# (显示字符, 资源字段名)
_NUMBER_FIELDS: tuple[tuple[str, str], ...] = (
    ("1", "price_one"),
    ("2", "price_two"),
    ("3", "price_three"),
    ("4", "price_four"),
    ("5", "price_five"),
    ("6", "price_six"),
    ("7", "price_seven"),
    ("8", "price_eight"),
    ("9", "price_nine"),
    ("0", "price_zero"),
    ("锭", "price_ding"),
    ("两", "price_liang"),
    ("文", "price_wen"),
)

# 每个物品行的高度，用于确定只扫描前 N 个物品
_PRODUCT_ROW_HEIGHT = 73
# 价格数字去重距离，模板宽度约 6 像素
_PRICE_DIGIT_DISTANCE = 3.0


def get_product_names() -> list[str]:
    """返回世界竞拍支持的全部物品名，供设置界面初始化表格。"""
    return [name for name, _field in _PRODUCT_FIELDS]


@dataclass(frozen=True)
class MarketProduct:
    """一条可竞拍物品信息。"""

    product_name: str
    current_price: float
    client_x: float
    client_y: float


def _to_int(text: str) -> int:
    """把模板拼出来的数字安全转换为整数，识别失败时按 0 处理。"""
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


def process_coordinates(data: list[tuple[float, str]]) -> float:
    """
    把横向排列的数字和单位拼成“两”为单位的价格。

    例如：1锭200两 -> 1200；300文 -> 0.3；2两 -> 2。
    """
    if not data:
        return 0.0

    unit_positions: dict[str, float] = {}
    remaining: list[tuple[float, str]] = []
    for x, char in data:
        if char in ("锭", "两", "文"):
            unit_positions[char] = float(x)
        else:
            remaining.append((float(x), char))

    def take_before(unit: str) -> str:
        """取出单位左侧的数字并从剩余列表中移除。"""
        nonlocal remaining
        if unit not in unit_positions:
            return ""
        limit = unit_positions[unit]
        selected = [(x, char) for x, char in remaining if x < limit]
        remaining = [(x, char) for x, char in remaining if x >= limit]
        selected.sort(key=lambda item: item[0])
        return "".join(char for _x, char in selected)

    ding = _to_int(take_before("锭"))
    liang = _to_int(take_before("两"))
    wen = _to_int(take_before("文"))
    return float(ding) * 1000.0 + float(liang) + float(wen) * 0.001


def filter_taben(items: list[MarketProduct]) -> list[MarketProduct]:
    """
    过滤拓本碎片重复识别。

    拓本碎片和若水神典拓本碎片的图标高度相似，同一位置可能同时命中；
    这里按纵坐标距离保留更具体的那一项。
    """
    result: list[MarketProduct] = []
    index = 0
    while index < len(items):
        if (index + 1 < len(items)
                and "拓本碎片" in items[index].product_name
                and "拓本碎片" in items[index + 1].product_name
                and abs(items[index].client_y - items[index + 1].client_y) < 60):
            if items[index + 1].product_name == "拓本碎片":
                result.append(items[index])
            elif items[index].product_name == "拓本碎片":
                result.append(items[index + 1])
            else:
                result.append(items[index])
            index += 2
            continue
        result.append(items[index])
        index += 1
    return result


class FindAuctionMarket:
    """世界竞拍识别。"""

    def __init__(self):
        config = get_resources().market_pic

        self._main_line = load_template(config.main_line)
        self._follow_line = load_template(config.follow_line)
        self._ok = load_template(config.ok)
        self._plus_price_10 = load_template(config.plus_price_10)
        self._plus_price_100 = load_template(config.plus_price_100)
        self._summit_price = load_template(config.summit_price)
        self._bidder_man = load_template(config.bidder_man)

        self._numbers: list[tuple[str, np.ndarray]] = []
        for char, field in _NUMBER_FIELDS:
            template = load_template(getattr(config, field, ""))
            if template is not None:
                self._numbers.append((char, template))

        self._products: list[tuple[str, np.ndarray]] = []
        for name, field in _PRODUCT_FIELDS:
            template = load_template(getattr(config, field, ""))
            if template is not None:
                self._products.append((name, template))

    @staticmethod
    def _find_results(image: np.ndarray, template: Optional[np.ndarray],
                      threshold: float = 0.9) -> list[dict]:
        """在图像中查找模板的所有匹配结果（灰度匹配，与 v1 一致）。"""
        if image is None or template is None or image.size == 0:
            return []
        return find_all_template(
            im_source=image,
            im_template=template,
            threshold=threshold,
            max_cnt=0,
            to_gray=True,
        )

    def _find_area(self, image: np.ndarray, template: Optional[np.ndarray],
                   threshold: float = 0.7) -> Optional[dict]:
        """只取匹配度最高的一项，返回 find_all_template 的原始结果。"""
        results = self._find_results(image, template, threshold)
        if not results:
            return None
        return max(results, key=lambda item: item["confidence"])

    @staticmethod
    def _rect_bounds(result: dict) -> tuple[int, int, int, int]:
        """把匹配矩形转换为 (left, top, right, bottom)。"""
        rectangle = result["rectangle"]
        xs = [point[0] for point in rectangle]
        ys = [point[1] for point in rectangle]
        return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

    @staticmethod
    def _crop(image: np.ndarray, left: int, top: int, right: int, bottom: int) -> Optional[np.ndarray]:
        """安全裁剪，越界时自动收缩到图像范围内。"""
        height, width = image.shape[:2]
        left = max(0, min(int(left), width))
        right = max(left, min(int(right), width))
        top = max(0, min(int(top), height))
        bottom = max(top, min(int(bottom), height))
        if right <= left or bottom <= top:
            return None
        return image[top:bottom, left:right]

    @staticmethod
    def _check_person_self(person_image: np.ndarray) -> bool:
        """检测当前竞拍人是否是自己（角色名显示为绿色）。"""
        image = to_bgr(person_image)
        if image is None:
            return False
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, np.array([35, 50, 100]), np.array([77, 255, 255]))
        return cv2.countNonZero(mask) > 100

    @staticmethod
    def _check_summit_price_clicked(button_image: np.ndarray) -> bool:
        """检测“确认出价”按钮是否高亮可点击（红色）。"""
        image = to_bgr(button_image)
        if image is None:
            return False
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_image, np.array([0, 100, 100]), np.array([10, 255, 255]))
        return cv2.countNonZero(mask) > 100

    def check_in_follow_page(self, image: np.ndarray) -> bool:
        """检测“我的关注”页签是否高亮；不是高亮时应结束竞拍。"""
        result = self._find_area(image, self._follow_line, threshold=0.7)
        return result is not None and float(result["confidence"]) > 0.85

    def find_plus_price(self, image: np.ndarray) -> list[tuple[float, float, float]]:
        """
        查找 10 两 / 100 两加价按钮。

        :return: [(x, y, confidence)]，按横坐标升序；调用方使用第一个即可
        """
        points: list[tuple[float, float, float]] = []
        for template in (self._plus_price_10, self._plus_price_100):
            for result in self._find_results(image, template, threshold=0.7):
                x, y = result["result"]
                points.append((float(x), float(y), float(result["confidence"])))
        points.sort(key=lambda item: item[0])
        return points

    def find_summit_price(self, image: np.ndarray) -> Optional[tuple[float, float]]:
        """
        查找可点击的“确认出价”按钮。

        :return: 按钮中心点 (x, y)；按钮不存在或未高亮时返回 None
        """
        result = self._find_area(image, self._summit_price, threshold=0.7)
        if result is None:
            return None

        left, top, right, bottom = self._rect_bounds(result)
        button_image = self._crop(image, left, top, right, bottom)
        if button_image is None or not self._check_summit_price_clicked(button_image):
            return None
        return float((left + right) / 2.0), float((top + bottom) / 2.0)

    def find_re_summit_price(self, image: np.ndarray) -> list[tuple[float, float, float]]:
        """查找二次确认按钮。"""
        points: list[tuple[float, float, float]] = []
        for result in self._find_results(image, self._ok, threshold=0.7):
            x, y = result["result"]
            points.append((float(x), float(y), float(result["confidence"])))
        points.sort(key=lambda item: item[0])
        return points

    def find_goods_list(self, image: np.ndarray, scan_product_num: int = 7,
                        pass_product_name: Optional[list[str]] = None) -> list[MarketProduct]:
        """
        查询当前页面前 N 个可竞拍物品。

        :param image: 客户区截图
        :param scan_product_num: 只扫描前几个物品，越小越快
        :param pass_product_name: 只检测这些物品（设置了最高价的物品）
        :return: 按纵坐标排序的物品列表
        """
        if pass_product_name is None:
            pass_product_name = []
        if image is None or image.size == 0:
            return []

        # 主分割线定位整个物品列表的左右边界
        main_line = self._find_area(image, self._main_line, threshold=0.7)
        if main_line is None or float(main_line["confidence"]) <= 0.8:
            return []

        line_left, line_top, line_right, line_bottom = self._rect_bounds(main_line)
        scan_height = _PRODUCT_ROW_HEIGHT * max(1, int(scan_product_num))

        # 直接裁剪列表区域，避免 v1 用全图掩膜产生的黑边影响匹配
        roi = self._crop(image,
                         line_left,
                         line_top,
                         line_right,
                         line_bottom + scan_height)
        if roi is None:
            return []

        roi_height, roi_width = roi.shape[:2]
        products: list[MarketProduct] = []

        for product_name, product_template in self._products:
            if product_name not in pass_product_name:
                continue

            for result in self._find_results(roi, product_template, threshold=0.9):
                center_x, center_y = result["result"]
                icon_x, icon_y = int(center_x), int(center_y)

                # 物品下方一行，用于判断成交人和当前竞拍人
                line_image = self._crop(roi,
                                        icon_x - 150,
                                        icon_y + 5,
                                        icon_x + 300,
                                        icon_y + 50)
                if line_image is None:
                    continue

                if self._find_results(line_image, self._bidder_man, threshold=0.9):
                    # 已有成交人，跳过
                    continue
                if self._check_person_self(line_image):
                    # 当前竞拍人是自己，跳过
                    continue

                # 价格在物品中心点右侧、纵向 30 像素内
                price_image = self._crop(roi,
                                         icon_x,
                                         icon_y,
                                         roi_width,
                                         icon_y + 30)
                if price_image is None:
                    continue

                digit_points: list[dict] = []
                for char, number_template in self._numbers:
                    for number_result in self._find_results(price_image, number_template, threshold=0.9):
                        digit_points.append({
                            "result": number_result["result"],
                            "confidence": number_result["confidence"],
                            "text": char,
                        })

                # 相似数字模板可能同时命中同一字形，先按位置去重
                digit_points = deduplicate_points(digit_points, _PRICE_DIGIT_DISTANCE)
                price_data = [(float(item["result"][0]), item["text"]) for item in digit_points]
                current_price = process_coordinates(price_data)

                products.append(MarketProduct(
                    product_name=product_name,
                    current_price=current_price,
                    client_x=float(line_left + center_x),
                    client_y=float(line_top + center_y),
                ))

        products = filter_taben(products)
        products.sort(key=lambda item: (item.client_y, item.client_x))
        return products
