# coding: utf-8
"""
挑战点兑换书页。

全流程都是模板匹配，没有 OCR：
1. 检查技能书页、兑换窗口是否存在；
2. 依次点击夺魄书页、兑换按钮、背包书页、回收栏、结果预览；
3. 点击确认兑换和二次确认。
"""
from __future__ import annotations

from Core.vision.target import TargetSpec
from Core.windows.capture import WindowsCapture
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.commonOperations import CommonOperations


class ChallengePointExchange:
    """挑战点兑换书页的界面操作。"""

    def __init__(self):
        config = get_resources().challenge_point_2_lucky_money
        self._common = CommonOperations()
        self._capture = WindowsCapture()

        # 兑换相关按钮都比较小，统一使用 0.9 的严格阈值
        self._spec_shop_book = TargetSpec(
            name="夺魄书页",
            template=config.challenge_point_shop_book,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_book_page = TargetSpec(
            name="技能书页",
            template=config.challenge_point_book_page,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_exchange_button = TargetSpec(
            name="书页兑换按钮",
            template=config.challenge_point_exchange_button,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_backpack_item = TargetSpec(
            name="背包中的书页",
            template=config.backpack_item_pic,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_recycle_box = TargetSpec(
            name="回收物品存放栏",
            template=config.recycle_box,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_recycle_result = TargetSpec(
            name="兑换结果预览",
            template=config.recycle_box_result,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_exchange_ok = TargetSpec(
            name="确定兑换",
            template=config.exchange_ok,
            threshold=0.9,
            to_gray=True,
        )
        self._spec_exchange_re_ok = TargetSpec(
            name="二次确认兑换",
            template=config.exchange_re_ok,
            threshold=0.9,
            to_gray=True,
        )

    def check_pic_template_exist(self, hwnd: int) -> int:
        """
        检查兑换所需的关键界面是否存在。

        :return: -1 未找到技能书页；-2 未找到兑换窗口；0 正常
        """
        pic = self._capture.capture(hwnd)
        if pic is None:
            return -2
        book_page = self._common.locate(hwnd, self._spec_book_page, pic=pic)
        recycle_box = self._common.locate(hwnd, self._spec_recycle_box, pic=pic)
        if book_page is None:
            return -1
        if recycle_box is None:
            return -2
        return 0

    def find_change_point_shop_book(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_shop_book)

    def find_change_point_book_page(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_book_page)

    def find_change_point_exchange_button(self, hwnd: int) -> bool:
        """
        查找技能书页的兑换按钮。

        与 v1 保持一致：按钮不存在时返回 True。该按钮属于可选步骤，
        找不到时任务应继续执行，而不是直接停止。
        """
        result = self._common.locate(hwnd, self._spec_exchange_button)
        if result is None or result.screen_point is None:
            return True
        return self._common.mouse_click_pos(hwnd, result.screen_point, 0)

    def find_backpack_item_pic(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_backpack_item)

    def find_recycle_box(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_recycle_box)

    def find_recycle_box_result(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_recycle_result)

    def find_exchange_ok(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_exchange_ok)

    def find_exchange_re_ok(self, hwnd: int) -> bool:
        return self._common.locate_and_click(hwnd, self._spec_exchange_re_ok)
