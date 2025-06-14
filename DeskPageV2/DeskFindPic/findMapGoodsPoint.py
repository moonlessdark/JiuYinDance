import time

import cv2
import numpy as np
from numpy import fromfile

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import WindowsHandle
from DeskPageV2.DeskTools.WindowsSoft.findOcr import FindPicOCR
from DeskPageV2.DeskTools.WindowsSoft.get_windows import PicCapture, find_area
from DeskPageV2.Utils.dataClass import FindTruckCarTaskNPC, Team, TruckCarPic, TruckCarReceiveTask, Goods, MapPic
from DeskPageV2.Utils.load_res import GetConfig


class FindMapGoodsPointList:

    def __init__(self):
        self._get_point_list: list = GetConfig().get_map_goods_point_list()
        self._map_pic = GetConfig().map_pic()  # 地图
        self._receive_task_road = GetConfig().truck_task()
        self.windows = WindowsCapture()
        self._status_config = GetConfig().get_bag_goods()

    @staticmethod
    def _load_pic(pic_dir: str):
        """
        加载一下图片
        """
        return cv2.imdecode(fromfile(pic_dir, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def plus_map(self, hwnd: int):
        """
        将地图的缩放放到最大
        """

        WindowsHandle().activate_windows(hwnd)
        time.sleep(1)

        __map = self._map_pic

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)
        __rec_pos_plus = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__map.plus_map))
        if __rec_pos_plus is None:
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False
        SetGhostMouse().move_mouse_to(__rec_pos_plus[0], __rec_pos_plus[1])
        time.sleep(0.2)
        SetGhostMouse().press_mouse_left_button()
        time.sleep(1)
        SetGhostMouse().release_mouse_left_button()
        time.sleep(0.1)
        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(1)
        return True

    def search_goods_point(self, x: str, y: str, hwnd: int):
        """
        在地图上查询资源坐标
        """
        __map = self._map_pic

        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)

        """
        X坐标
        """
        __rec_pos_x = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__map.pos_x))
        if __rec_pos_x is None:
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False
        SetGhostMouse().move_mouse_to(__rec_pos_x[0] + 50, __rec_pos_x[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(8, 0.5)
        time.sleep(0.1)

        # 输入x坐标
        for ss in x:
            SetGhostBoards().click_press_and_release_by_key_name(ss)
            time.sleep(0.2)

        """
        Y坐标
        """
        __rec_pos_y = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__map.pos_y))
        if __rec_pos_y is None:
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False
        SetGhostMouse().move_mouse_to(__rec_pos_y[0] + 50, __rec_pos_y[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(8, 0.5)
        time.sleep(0.1)

        # 输入y坐标
        for ss in y:
            SetGhostBoards().click_press_and_release_by_key_name(ss)
            time.sleep(0.2)

        """
        查询并点击搜索结果，自动寻路过去
        """
        while 1:

            __rec_pos_search = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__map.search_pos))
            if __rec_pos_search is None:
                time.sleep(1)
                continue
            time.sleep(1)
            SetGhostMouse().move_mouse_to(__rec_pos_search[0], __rec_pos_search[1])
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            break

        while 1:
            __rec_pos_point = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__map.result_point))
            if __rec_pos_point is None:
                time.sleep(1)
                continue
            time.sleep(1)
            SetGhostMouse().move_mouse_to(__rec_pos_point[0], __rec_pos_point[1])
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            break

        pos = coordinate_change_from_windows(hwnd, (1, 1))
        SetGhostMouse().move_mouse_to(pos[0], pos[1])

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)
        return True

    def find_open_loading(self, hwnd: int):
        """
        查询打开状态
        """
        __rec_goods_bag_open_loading = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(self._status_config.open_loading))
        if __rec_goods_bag_open_loading is not None:
            return True
        return False

    def check_person_move_status(self, hwnd: int):
        """
        检测人物角色行走状态。
        判断逻辑为: 监测右上角的地图坐标是否发生变动，如果每隔2秒监测一次，都是在变化的，那么就是在移动中。
        可以用来判断是否已经到达目的地坐标或者卡地形了
        """

        """
        监测2次坐标是否一致，如果一致则标识当前人物已经停止移动
        """
        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.2)
        _last_ocr_str: str = ""
        for i in range(2):
            pic_w = self.windows.capture(hwnd).pic_width
            x, y = coordinate_change_from_windows(hwnd, (pic_w - 110, 180))
            SetGhostMouse().move_mouse_to(x, y)
            time.sleep(0.5)
            pic = self.windows.capture(hwnd)
            # 高度1-300像素，宽度 画面右侧，查看所有状态栏
            pic_content = pic.pic_content[205:270, pic_w - 240:pic_w - 115]
            # cv2.imshow('find_single_template_result.en.png', pic_content)
            # cv2.waitKey()

            pic_str = FindPicOCR().find_ocr_all(pic_content)
            for pps in pic_str:
                # print(pps.ocr_text)
                if _last_ocr_str == "":
                    _last_ocr_str = pps.ocr_text
                else:
                    if _last_ocr_str == pps.ocr_text:
                        # 如果2次ocr识别的内容相同，说明人物已经停止移动，到了目的地或者卡地形了
                        # 因为OCR识别有误差，所以使用此方法
                        print("人物已经停止移动")
                        return True
            SetGhostMouse().move_mouse_to(x, y + 50)
        print("人物移动中")
        return False

    def click_ok(self, hwnd: int):
        """
        点击确定按钮
        """
        time.sleep(1)
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(self._status_config.get_all_goods))
        if __rec_goods_bag_tag_clickable is not None:
            SetGhostMouse().move_mouse_to(__rec_goods_bag_tag_clickable[0], __rec_goods_bag_tag_clickable[1])
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()
            return True
        return False

    def click_mini_map(self, hwnd: int):
        """
        点击一下小地图的正中央，看看能不能出现进度条
        """
        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.2)
        pic_w = self.windows.capture(hwnd).pic_width
        x, y = coordinate_change_from_windows(hwnd, (pic_w - 110, 120))
        SetGhostMouse().move_mouse_to(x, y)
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.2)