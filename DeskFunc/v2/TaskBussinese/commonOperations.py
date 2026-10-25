# coding: utf-8
"""
v2 通用操作。

目前包含：
1. 鼠标点击；
2. 物品使用进度条识别；
3. “全部拾取 / 获取全部”按钮识别与点击；
4. 单目标定位/点击的统一入口，供各业务模块复用。

识别统一走 Core.vision 的 ScreenSource + Locator + TargetSpec，
不再使用 FindWindowsImageTemplate 这类旧封装。
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import Optional

from Core.input.ghost import SetGhostMouse
from Core.vision.locator import Locator, MatchResult
from Core.vision.screen import ScreenSource
from Core.vision.target import RatioRect, TargetSpec
from Core.windows.capture import PicCapture
from Core.windows.window import WindowsHandle
from Utils.resourceConfig import get_resources


class CommonOperations:
    """游戏中的通用操作。"""

    def __init__(self):
        resources = get_resources()
        self._config = resources.opt_status
        self._windows_opt = WindowsHandle()
        self._screen = ScreenSource()
        self._locator = Locator(self._screen)

        # 物品使用进度条：先彩色匹配，失败再灰度匹配
        self._loading_bar_color = TargetSpec(
            name="物品使用进度条",
            template=self._config.open_loading,
            roi=RatioRect(x=0.3, y=0.5, width=0.4, height=0.4),
            threshold=0.7,
            to_gray=False,
        )
        self._loading_bar_gray = replace(self._loading_bar_color,
                                         name="物品使用进度条(灰度)",
                                         to_gray=True)

        # “全部拾取”按钮
        self._get_all_button = TargetSpec(
            name="全部拾取按钮",
            template=self._config.get_all_goods,
            threshold=0.85,
            to_gray=False,
        )

    def mouse_click_pos(self, hwnd: int, move_pos: tuple, mouse_type: int = 0) -> bool:
        """
        激活窗口并点击鼠标。

        :param hwnd: 窗口句柄
        :param move_pos: 屏幕坐标 (x, y)
        :param mouse_type: 0-左键 1-右键 2-中键
        :return: 是否完成点击
        """
        if not self._windows_opt.activate_windows(hwnd):
            return False
        x, y = move_pos
        SetGhostMouse().move_mouse_to(int(x), int(y))
        time.sleep(0.1)
        if mouse_type == 1:
            SetGhostMouse().click_mouse_right_button()
        elif mouse_type == 2:
            SetGhostMouse().click_mouse_middle_button()
        else:
            SetGhostMouse().click_mouse_left_button()
        time.sleep(0.3)  # 给游戏窗口响应时间
        return True

    def locate(self, hwnd: int, spec: TargetSpec,
               pic: Optional[PicCapture] = None) -> Optional[MatchResult]:
        """定位单个目标，结果中带屏幕坐标。"""
        return self._locator.locate(hwnd=hwnd, spec=spec, pic=pic)

    def locate_and_click(self, hwnd: int, spec: TargetSpec,
                         mouse_type: int = 0,
                         pic: Optional[PicCapture] = None) -> bool:
        """
        定位目标并点击其中心点。

        :return: True 表示找到并点击成功
        """
        result = self.locate(hwnd=hwnd, spec=spec, pic=pic)
        if result is None or result.screen_point is None:
            return False
        return self.mouse_click_pos(hwnd, result.screen_point, mouse_type)

    def find_open_loading(self, hwnd: int) -> bool:
        """查询物品使用进度条是否出现。"""
        pic = self._screen.capture(hwnd)
        if pic is None:
            return False
        result = self._locator.locate_first(
            hwnd=hwnd,
            specs=(self._loading_bar_color, self._loading_bar_gray),
            pic=pic,
        )
        return result is not None

    def find_get_all_button(self, hwnd: int) -> bool:
        """查找并点击“全部拾取”按钮。"""
        return self.locate_and_click(hwnd=hwnd, spec=self._get_all_button, mouse_type=0)
