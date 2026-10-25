# coding: utf-8
"""
清理禁地包裹：识别禁地物品包和打开后产生的材料包。

两类包裹都在背包中，使用右键连续打开；数量角标用局部遮罩挡住，
避免数量变化导致模板匹配失败。

禁地物品包模板带有遮罩副本，不能直接交给 Locator（Locator 只接受模板路径），
因此这里统一使用 WindowsCapture + find_all_template 自行取最高匹配度。
"""
from __future__ import annotations

from typing import Optional

from Core.vision.template import find_all_template, load_template
from Core.windows.capture import WindowsCapture
from Core.windows.geometry import client_to_screen
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.commonOperations import CommonOperations
from DeskFunc.v2.TaskBussinese.imageTools import mask_template_region


class HiddenRealmItems:
    """禁地包裹与材料包的识别。"""

    def __init__(self):
        resources = get_resources()
        backpack = resources.backpack

        self._common = CommonOperations()
        self._capture = WindowsCapture()

        self._red_package = mask_template_region(load_template(backpack.hidden_realm_item_package),
                                                 33, 29, 39, 38)
        self._material_package = load_template(backpack.material_item_package)

    def find_red_item_backpack(self, hwnd: int) -> bool:
        """找到禁地物品包并右键打开。"""
        return self._find_and_right_click(hwnd, self._red_package)

    def find_cailiao_item_backpack(self, hwnd: int) -> bool:
        """找到打开后产生的材料包并右键打开。"""
        return self._find_and_right_click(hwnd, self._material_package)

    def _find_and_right_click(self, hwnd: int, template) -> bool:
        if template is None:
            return False
        position = self._find_best(hwnd, template)
        if position is None:
            return False
        return self._common.mouse_click_pos(hwnd, position, 1)

    def _find_best(self, hwnd: int, template) -> Optional[tuple[int, int]]:
        """取匹配度最高的一项并转换为屏幕坐标。"""
        capture = self._capture.capture(hwnd)
        if capture is None:
            return None
        results = find_all_template(
            im_source=capture.pic_content,
            im_template=template,
            threshold=0.7,
            max_cnt=0,
            to_gray=True,
        )
        if not results:
            return None
        best = max(results, key=lambda item: item["confidence"])
        return client_to_screen(hwnd, best["result"])
