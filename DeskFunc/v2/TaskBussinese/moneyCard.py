# coding: utf-8
"""
9 点开卡（武庆礼卡）的界面识别。

全部依赖模板匹配，不依赖 OCR：
1. 背包页签：已点击 / 未点击两种状态；
2. 礼卡图标：使用局部遮罩挡住数量角标；
3. 打开进度条；
4. “全部拾取”按钮。

旧版调用 FindWindowsImageTemplate 和 GetConfig，v2 改为 Core 的 Locator + find_all_template，
资源路径统一从 Utils.resourceConfig 获取。
"""
from __future__ import annotations

import time
from typing import Optional

from Core.input.ghost import SetGhostBoards
from Core.vision.template import find_all_template, load_template
from Core.vision.target import TargetSpec
from Core.windows.capture import WindowsCapture
from Core.windows.geometry import client_to_screen
from Core.windows.window import WindowsHandle
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.commonOperations import CommonOperations
from DeskFunc.v2.TaskBussinese.imageTools import mask_template_region


class FindGiftCard:
    """9 点开卡用到的界面识别与点击。"""

    def __init__(self):
        resources = get_resources()
        backpack = resources.backpack

        self._windows_opt = WindowsHandle()
        self._windows_cap = WindowsCapture()
        self._common = CommonOperations()

        self._backpack_unclicked = TargetSpec(
            name="背包未点击页签",
            template=backpack.goods_bag_tag_clickable,
            threshold=0.85,
            to_gray=True,
        )
        self._backpack_clicked = TargetSpec(
            name="背包已点击页签",
            template=backpack.goods_bag_tag_clicked,
            threshold=0.85,
            to_gray=True,
        )

        # 礼卡右下角会显示数量，涂掉后再匹配，避免数量变化导致识别失败
        gift_card = load_template(backpack.gift_card)
        self._gift_card = mask_template_region(gift_card, 33, 29, 39, 38)

    def find_backpack(self, hwnd: int) -> bool:
        """
        确保背包处于打开状态。

        :return: True 表示背包可用
        """
        for _ in range(3):
            clicked = self._common.locate(hwnd, self._backpack_clicked)
            unclicked = self._common.locate(hwnd, self._backpack_unclicked)

            if clicked is not None and unclicked is not None:
                # 两个状态同时出现通常说明界面还没完全切换，先点击已点击页签
                return self._common.mouse_click_pos(hwnd, clicked.screen_point, 0)

            if clicked is not None:
                return True

            if unclicked is not None:
                self._common.mouse_click_pos(hwnd, unclicked.screen_point, 0)
                return True

            # 没找到背包页签，按 B 打开背包
            if not self._windows_opt.activate_windows(hwnd):
                return False
            time.sleep(0.2)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
            time.sleep(0.2)
        return False

    def find_gift_card(self, hwnd: int) -> bool:
        """
        找到最靠左的礼卡并右键点击。

        :return: True 表示找到并点击成功
        """
        position = self._find_leftmost_gift_card(hwnd)
        if position is None:
            return False
        return self._common.mouse_click_pos(hwnd, position, 1)

    def click_get_all(self, hwnd: int) -> bool:
        """点击“全部拾取”按钮。"""
        return self._common.find_get_all_button(hwnd)

    def find_open_loading(self, hwnd: int) -> bool:
        """查询开卡进度条。"""
        return self._common.find_open_loading(hwnd)

    def _find_leftmost_gift_card(self, hwnd: int) -> Optional[tuple[int, int]]:
        """在整张客户区截图中查找最靠左的礼卡，返回屏幕坐标。"""
        if self._gift_card is None:
            return None

        capture = self._windows_cap.capture(hwnd)
        if capture is None:
            return None

        results = find_all_template(
            im_source=capture.pic_content,
            im_template=self._gift_card,
            threshold=0.7,
            max_cnt=0,
            to_gray=True,
        )
        if not results:
            return None

        leftmost = min(results, key=lambda item: item["result"][0])
        return client_to_screen(hwnd, leftmost["result"])
