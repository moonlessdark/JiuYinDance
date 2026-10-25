# coding: utf-8
"""
地图物资采集的界面操作。

流程与 v1 一致，但识别统一改为 Core 的 ScreenSource + Locator：
1. 放大地图；
2. 打开地图并输入 X / Y 坐标；
3. 点击搜索结果和地图落点；
4. 通过右上角坐标数字模板判断人物是否停止移动（纯模板匹配，不是 OCR）；
5. 点击采集 / 全部拾取按钮。

坐标数字模板很小，长时间等待按钮时增加了超时和停止回调，
避免任务停止后仍卡死在无限循环里。
"""
from __future__ import annotations

import time
from typing import Callable

from Core.input.ghost import SetGhostBoards, SetGhostMouse
from Core.vision.target import TargetSpec
from Core.windows.capture import WindowsCapture
from Core.windows.geometry import client_to_screen
from Core.windows.window import WindowsHandle
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.commonOperations import CommonOperations
from DeskFunc.v2.TaskBussinese.personPoint import FindPersonPoint

# 等待地图搜索按钮出现的最长时间（秒）
_WAIT_BUTTON_TIMEOUT = 30


def _always_running() -> bool:
    """默认的停止回调，供离线调试时使用。"""
    return True


class FindMapGoodsPoint:
    """地图采集用到的界面识别。"""

    def __init__(self):
        resources = get_resources()
        map_config = resources.map_pic
        status_config = resources.opt_status

        self._windows_opt = WindowsHandle()
        self._windows_cap = WindowsCapture()
        self._common = CommonOperations()
        self._person_point = FindPersonPoint()

        # v1 这些模板都使用默认阈值 0.7、灰度匹配
        self._spec_plus_map = TargetSpec(
            name="地图放大按钮",
            template=map_config.plus_map,
            threshold=0.7,
            to_gray=True,
        )
        self._spec_pos_x = TargetSpec(
            name="地图X坐标输入框",
            template=map_config.pos_x,
            threshold=0.7,
            to_gray=True,
        )
        self._spec_pos_y = TargetSpec(
            name="地图Y坐标输入框",
            template=map_config.pos_y,
            threshold=0.7,
            to_gray=True,
        )
        self._spec_search_pos = TargetSpec(
            name="地图搜索按钮",
            template=map_config.search_pos,
            threshold=0.7,
            to_gray=True,
        )
        self._spec_result_point = TargetSpec(
            name="地图搜索结果点",
            template=map_config.result_point,
            threshold=0.70,
            to_gray=True,
        )
        self._spec_open_loading = TargetSpec(
            name="采集进度条",
            template=status_config.open_loading,
            threshold=0.7,
            to_gray=True,
        )
        self._spec_get_all = TargetSpec(
            name="采集/全部拾取按钮",
            template=status_config.get_all_goods,
            threshold=0.7,
            to_gray=True,
        )

    def plus_map(self, hwnd: int) -> bool:
        """把地图缩放到最大。"""
        self._windows_opt.activate_windows(hwnd)
        time.sleep(1)

        result = self._common.locate(hwnd, self._spec_plus_map)
        if result is None:
            SetGhostBoards().click_press_and_release_by_key_name("M")
            time.sleep(0.5)
            result = self._common.locate(hwnd, self._spec_plus_map)
            print("找到地图了吗？", result)
        if result is None or result.screen_point is None:
            return False

        SetGhostMouse().move_mouse_to(*result.screen_point)
        time.sleep(0.2)
        SetGhostMouse().press_mouse_left_button()
        time.sleep(1)
        SetGhostMouse().release_mouse_left_button()
        time.sleep(0.1)
        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(1)
        return True

    def search_goods_point(self, x: str, y: str, hwnd: int,
                           is_running: Callable[[], bool] = _always_running) -> bool:
        """
        在地图上搜索资源坐标并自动寻路。

        :param x: X 坐标文本
        :param y: Y 坐标文本
        :param hwnd: 窗口句柄
        :param is_running: 停止回调，返回 False 时尽快退出
        :return: True 表示已点击地图落点
        """
        self._windows_opt.activate_windows(hwnd)
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)

        if not self._input_coordinate(hwnd, self._spec_pos_x, str(x)):
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False

        if not self._input_coordinate(hwnd, self._spec_pos_y, str(y)):
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False

        if not self._wait_and_click(hwnd, self._spec_search_pos, is_running):
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False

        if not self._wait_and_click(hwnd, self._spec_result_point, is_running):
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False

        # 鼠标移到右上角，避免遮挡小地图
        capture = self._windows_cap.capture(hwnd)
        if capture is not None:
            point = client_to_screen(hwnd, (capture.pic_width - 110, 180))
            SetGhostMouse().move_mouse_to(point[0], point[1] + 50)

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)
        return True

    def _input_coordinate(self, hwnd: int, spec: TargetSpec, text: str) -> bool:
        """
        点击坐标输入框，清空旧内容并输入新坐标。

        :return: True 表示输入完成
        """
        result = self._common.locate(hwnd, spec)
        if result is None or result.screen_point is None:
            return False

        # 输入框右侧留出距离，避免点到文字中间
        SetGhostMouse().move_mouse_to(result.screen_point[0] + 50, result.screen_point[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.5)
        # 8 = Backspace，长按清空原有坐标
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(8, 0.5)
        time.sleep(0.1)
        for char in text:
            SetGhostBoards().click_press_and_release_by_key_name(char)
            time.sleep(0.2)
        return True

    def _wait_and_click(self, hwnd: int, spec: TargetSpec,
                        is_running: Callable[[], bool]) -> bool:
        """等待模板出现后点击，超时或任务停止时返回 False。"""
        start_time = time.time()
        while time.time() - start_time < _WAIT_BUTTON_TIMEOUT:
            if not is_running():
                return False
            result = self._common.locate(hwnd, spec)
            if result is not None and result.screen_point is not None:
                time.sleep(1)
                self._common.mouse_click_pos(hwnd, result.screen_point, 0)
                time.sleep(1)
                return True
            time.sleep(1)
        return False

    def check_person_move_status(self, hwnd: int) -> bool:
        """
        判断人物是否已经停止移动。

        通过右上角坐标文本是否连续两次一致来判断；识别不到坐标时返回 False，
        避免“空字符串 == 空字符串”导致误判为已停止。

        :return: True 表示已停止移动
        """
        self._windows_opt.activate_windows(hwnd)
        time.sleep(0.2)

        last_text = ""
        for _ in range(2):
            capture = self._windows_cap.capture(hwnd)
            if capture is None:
                return False
            pic_w = capture.pic_width
            point = client_to_screen(hwnd, (pic_w - 110, 180))
            SetGhostMouse().move_mouse_to(point[0], point[1])
            time.sleep(0.5)

            capture = self._windows_cap.capture(hwnd)
            if capture is None:
                return False

            # 右上角坐标区域：高度 205~270，宽度从右往左 240~115
            left = max(0, pic_w - 240)
            right = max(left, pic_w - 115)
            top = 205
            bottom = min(capture.pic_height, 270)
            if bottom <= top or right <= left:
                return False
            crop = capture.pic_content[top:bottom, left:right]

            current_text = self._person_point.find_text(crop)
            if not current_text:
                return False
            if last_text and last_text == current_text:
                return True
            last_text = current_text

            SetGhostMouse().move_mouse_to(point[0], point[1] + 50)
            time.sleep(1)
        return False

    def find_open_loading(self, hwnd: int) -> bool:
        """查询采集进度条。"""
        return self._common.locate(hwnd, self._spec_open_loading) is not None

    def click_ok(self, hwnd: int) -> bool:
        """点击采集/全部拾取按钮。"""
        time.sleep(1)
        return self._common.locate_and_click(hwnd, self._spec_get_all, mouse_type=0)

    def click_mini_map(self, hwnd: int) -> bool:
        """点击小地图中心，触发一次采集状态刷新。"""
        self._windows_opt.activate_windows(hwnd)
        time.sleep(0.2)
        capture = self._windows_cap.capture(hwnd)
        if capture is None:
            return False
        point = client_to_screen(hwnd, (capture.pic_width - 110, 120))
        SetGhostMouse().move_mouse_to(point[0], point[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.2)
        return True
