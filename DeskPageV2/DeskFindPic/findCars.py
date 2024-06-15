# -*- coding: utf-8 -*-
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
from DeskPageV2.Utils.dataClass import FindTruckCarTaskNPC, Team, TruckCarPic, TruckCarReceiveTask, Goods
from DeskPageV2.Utils.load_res import GetConfig
from DeskPageV2.DeskFindPic.findSkill import SkillGroup


def bitwise_and(image: np.ndarray, mask_position: tuple):
    """
    给图片加个掩膜遮罩，避免干扰
    :param image: 图片
    :param mask_position: # 指定掩膜位置（左上角坐标， 右下角坐标） mask_position = (50, 50, 200, 200)
    """
    if image is not None:
        # 绘制掩膜（矩形）
        # 参数分别为：图像、矩形左上角坐标、矩形右下角坐标、颜色（BGR）、线条粗细
        return cv2.rectangle(image, mask_position[0:2], mask_position[2:4], (0, 255, 0), -1)
    return image


class TruckCar:
    def __init__(self):
        self._config = GetConfig()
        self._find_task_npc = None  # 查询任务NPC
        self._find_team = None  # 查询队伍是否创建
        self._receive_task = None  # 接取押镖任务
        self._receive_task_road = None  # 运镖路上...
        self._find_tag_goods = None  # 物品背包

        self.windows = WindowsCapture()
        self.ocr = FindPicOCR()
        self._skill_func = SkillGroup()

        self.hwnd: int = 0

        self._area_map, self._person_name = None, None
        self._skill_obj: dict = self._config.get_skill_group_list().get("打怪套路")  # 当前正在使用的技能组

    def get_map_and_person(self, hwnd: int):
        _, self._area_map, self._person_name = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)
        # print(f"当前地图是 {self._area_map}, 当前角色是 {self._person_name}")
        return self._area_map

    @staticmethod
    def _load_pic(pic_dir: str):
        """
        加载一下图片
        """
        return cv2.imdecode(fromfile(pic_dir, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def _get_pic_find_task_npc(self) -> FindTruckCarTaskNPC:
        """
        获取查找地图的运镖NPC
        """
        if self._find_task_npc is None:
            self._find_task_npc = self._config.find_track_car_task()
        return self._find_task_npc

    def _get_pic_team(self) -> Team():
        """
        检查队伍是否创建
        """
        if self._find_team is None:
            self._find_team = self._config.get_team()
        return self._find_team

    def _get_bag_goods(self) -> Goods:
        """
        获取物品背包
        """
        if self._find_tag_goods is None:
            self._find_tag_goods = self._config.get_bag_goods()
        return self._find_tag_goods

    def _get_pic_receive_task(self) -> TruckCarReceiveTask:
        """
        接取任务和押镖的路上
        """
        if self._receive_task is None:
            self._receive_task = self._config.get_track_car()
        return self._receive_task

    def _get_pic_truck_car(self):
        """
        开始押镖了
        """
        if self._receive_task_road is None:
            self._receive_task_road = self._config.truck_task()
        return self._receive_task_road

    @staticmethod
    def reply_person_perspective(hwnd: int):
        """
        恢复角色向前的视角
        """
        WindowsHandle().activate_windows(hwnd)
        time.sleep(1)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(38, 0.6)  # 再向上1秒
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(40, 3)  # 先向下到底3秒
        time.sleep(1)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(38, 0.6)  # 再向上1秒
        time.sleep(1)
        SetGhostMouse().move_mouse_wheel(20)  # 拉近镜头
        time.sleep(1)
        SetGhostMouse().move_mouse_wheel(-5)  # 拉远镜头

    @staticmethod
    def reply_person_perspective_up(hwnd: int):
        """
        上移视角，视角拉到远处，用于查找车辆
        """
        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(38, 2)
        time.sleep(0.5)
        SetGhostMouse().move_mouse_wheel(-30)  # 视角拉远一些
        time.sleep(0.5)

    @staticmethod
    def _check_target_pos_is_center(img: PicCapture, target_pos: tuple) -> bool:
        """
        检查传入的坐标是否是在屏幕中间的区域
        """
        __img = img
        __w, __h = __img.pic_width, __img.pic_height

        if int(__w * 0.4) < target_pos[0] < int(__w * 0.60) and target_pos[1] < int(__h * 0.5):
            """
            如果目标在屏幕的上半区域
            """
            # print("镖车处于屏幕的上半区域，符合要求")
            return True
        # "镖车所处的坐标不符合要求")
        return False

    @staticmethod
    def check_target_pos_direction(img: PicCapture, target_pos: tuple) -> int:
        """
        检查传入的坐标是否是在屏幕中间的区域
        :return 4象限： 1：左上角，2，右上角，3. 左下角， 4. 右下角
        """
        __img = img
        __w, __h = __img.pic_width, __img.pic_height

        center_x = int(__w * 0.5)  # 屏幕正中间
        center_y = int(__h * 0.5)  # 屏幕正中间
        # print(f"图片的宽高 {__w}_{__h}, 中心坐标是 ({center_x},{center_y})")

        if target_pos[0] < center_x:
            if target_pos[1] < center_y:
                """
                如果是 宽 小于屏幕中心， 高 也小于屏幕中心。
                返回 象限1， 左上角
                """
                quadrant_pos = 1
            else:
                """
                如果是 宽 小于屏幕中心，高 大于屏幕中心.
                返回 象限3. 左下角
                """
                quadrant_pos = 3
        else:
            if target_pos[1] < center_y:
                """
                如果是 宽 大于屏幕中心， 高 小于屏幕中心。
                返回 象限2， 右上角
                """
                quadrant_pos = 2
            else:
                """
                如果是 宽 大于屏幕中心，高 大于屏幕中心.
                返回 象限4. 右下角
                """
                quadrant_pos = 4
        # print(f"镖车在第 {quadrant_pos} 象限")
        return quadrant_pos

    def _check_task_status(self, hwnd: int) -> bool:
        """
        检测是否接取了任务。
        任务栏的押镖小旗子
        """
        time.sleep(1)
        find_task: TruckCarPic = self._get_pic_truck_car()
        task_flag_status = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                     img=find_task.task_flag_status)
        if task_flag_status is None:
            """
            押镖状态没有了，可能是被
            需要重新接镖。
            有以下原因：
            1、押镖结束
            2、打怪失败
            3、被四害干扰了
            """
            # print("未找到押镖状态")
            return False
        return True

    def _check_task_end(self, hwnd: int) -> bool:
        """
        检测押镖是否结束
        """
        if len(self.ocr.find_ocr_arbitrarily(self.windows.capture(hwnd).pic_content,
                                             ["获得帮派贡献度", "为帮会带来"])) > 0:
            # print("DriverTruckCarFuc: 运镖结束")
            return True
        return False

    def _check_person_move_status(self, hwnd: int, old_pos: int):
        """
        游戏人物是否在移动
        :param old_pos: 旧地图坐标
        """
        pos, _, _ = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)
        if old_pos == pos:
            return False
        return True

    def __find_car_in_display(self, hwnd: int, image: np.ndarray = None):
        """
        查询当前页面是否存在镖车
        """
        if image is not None:
            __content = image
        else:
            __img_car = self.windows.capture(hwnd)
            __h, __w, __content = __img_car.pic_height, __img_car.pic_width, __img_car.pic_content
        __cos_text = self.ocr.find_truck_car_ocr(__content, "的镖车")
        if __cos_text is not None:
            driver_res = coordinate_change_from_windows(hwnd, __cos_text)
            # print(f"DriverTruckCarFuc: 发现了 运镖(驾车) 文字({driver_res[0]},{driver_res[1]})")
            return driver_res
        return None

    def _find_driver_truck_type(self, hwnd: int):
        """
        检查 运镖(驾车) 按钮。
        图片模板的识别速度比文字快，所以这里先找图再找文字
        """
        time.sleep(1)
        __img_car = self.windows.capture(hwnd)
        # 先找图片模板的驾车按钮在不在
        find_task: TruckCarPic = self._get_pic_truck_car()
        cos = self.windows.find_windows_coordinate_rect(hwnd, find_task.task_star_mode)
        if cos is not None:
            return cos

        return None

    def find_car_center_pos_in_display(self, hwnd: int):
        """
        查询小车是不是在屏幕中间
        """
        __cap_display = self.windows.capture(hwnd)
        rec = self.__find_car_in_display(hwnd=hwnd, image=__cap_display.pic_content)
        if rec is not None:
            """
            找到车了，把视角转到这个车aw
            """
            if self._check_target_pos_is_center(__cap_display, rec):
                # print(f"转OK了, 当前坐标是 ({rec[0], rec[1]})")
                return coordinate_change_from_windows(hwnd, rec)
            # print("还没有转到符合条件的地方")
        return None

    def find_car_center_pos_in_display_v2(self, hwnd: int):
        """
        查询小车是不是在屏幕中间
        """
        time.sleep(0.5)
        __im = self.windows.capture(hwnd)
        _rec = self.ocr.find_truck_car_ocr(__im.pic_content, "的镖车")

        if _rec is not None:
            """
            找到车了，把视角转到这个车
            """
            __new_pic = __im.pic_content[int(__im.pic_height * 0.1):int(__im.pic_height * 0.6), int(__im.pic_width * 0.3):int(__im.pic_width * 0.7)]
            __rec = self.ocr.find_truck_car_ocr(__new_pic, "的镖车")

            if __rec is not None:
                # print("镖车大概在屏幕中间了V2版本")
                return coordinate_change_from_windows(hwnd, _rec)
                # print("还没有转到符合条件的地方")
        return None

    def find_car_in_center_display_v3(self, hwnd: int = None, image: PicCapture = None, display_area: int = 0):
        """
        :param hwnd: 句柄
        :param image: 图片
        :param display_area: 0，表示 1，2象限的屏幕中间，用于接镖找车. 1，表示1234象限中间。用于打怪后找车
        """
        if image is not None:
            __h, __w, __content = image.pic_height, image.pic_width, image.pic_content
        else:
            image = self.windows.capture(hwnd)
            __h, __w, __content = image.pic_height, image.pic_width, image.pic_content
        _v3_res = self.__find_car_in_display(hwnd=hwnd, image=__content)
        if _v3_res is None:
            return None
        if display_area == 0:
            _v3_new_pic = image.pic_content[int(image.pic_height * 0.1):int(image.pic_height * 0.6), int(image.pic_width * 0.4):int(image.pic_width * 0.6)]
        else:
            _v3_new_pic = image.pic_content[int(image.pic_height * 0.1):int(image.pic_height * 0.6), int(image.pic_width * 0.3):int(image.pic_width * 0.7)]

        __rec = self.ocr.find_truck_car_ocr(_v3_new_pic, "的镖车")
        if __rec is not None:
            # print("镖车大概在屏幕中间了V3版本")
            return coordinate_change_from_windows(hwnd, __rec)
        return None

    def find_car_pos_in_display(self, hwnd: int):
        """
        查询小车在哪
        """
        self.get_map_and_person(hwnd)
        im = self.windows.capture(hwnd)
        rec = self.ocr.find_truck_car_ocr(im.pic_content, "的镖车")

        if rec is not None:
            """
            找到车了，把视角转到这个车
            """
            # print("屏幕出现镖车了")
            return coordinate_change_from_windows(hwnd, rec)
        # print("还没有转到符合条件的地方")
        return None


class FightMonster(TruckCar):
    """
    打怪啊
    """

    def __init__(self):
        super().__init__()
        self.__find_task = None

    def check_fight_status(self, hwnd: int):
        """
        检查是否进入了战斗状态。
        避免识别场景过于复杂，在这里进行多重检测
        """
        self.__find_task: TruckCarPic = self._get_pic_truck_car()
        pic = self.windows.capture(hwnd)
        # 高度1-300像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.4), int(pic.pic_width * 0.5):int(pic.pic_width)]
        task_monster_fight = find_area(smaller_pic=self._load_pic(self.__find_task.task_monster_fight),
                                       bigger_img=pic_content)
        if task_monster_fight[-1] > 0.5:
            """
                如果出现了相似度大于0.5的 出现了战投的图标
                方法2: 如果出现了 进入战斗的图标（进入战斗的文字模板和右上角的NPC标志），那么就说明进入战斗了
                """
            # print("进入战斗: 查询到进入战斗的模板")
            return True
        return False

    def _check_monster_skill_status(self, hwnd: int):
        """
        检测NPC是不是在放技能
        """
        fight_tag_skill: str = self.__find_task.task_monster_target_skil

        pic = self.windows.capture(hwnd)
        # 高度1-30%像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.3), int(pic.pic_width * 0.3):int(pic.pic_width * 0.7)]
        task_monster_fight = find_area(smaller_pic=self._load_pic(fight_tag_skill), bigger_img=pic_content)
        if task_monster_fight[-1] > 0.5:
            # print(f"检测到NPC要放技能了{task_monster_fight}")
            return True
        # print("NPC没有要放技能")
        return False

    def __fight_func(self, hwnd: int):
        """
        打怪啊
        """
        is_skill_tag_status: int = 0  # 是否结束释放按钮， 0,表示 初始化，1 表示 技能条出现中，2表示技能条结束
        SetGhostMouse().press_mouse_right_button()
        while 1:
            if self._check_monster_skill_status(hwnd):
                # print("怪要放技能了，进行格挡")
                is_skill_tag_status = 1
                continue
                # if is_skill_tag_status:
                #     if SetGhostMouse().is_mouse_button_pressed(3) is False:
                #         print("怪要放技能了，进行格挡")
                #         # 如果当前状态时格挡中
                #         SetGhostMouse().press_mouse_right_button()
                #         continue
            else:
                if is_skill_tag_status == 1:
                    # 表示放技能的图标已经消失了，
                    # print("怪结束放技能了，多格挡2秒")
                    time.sleep(2)
                    is_skill_tag_status = 0
                    # SetGhostMouse().release_mouse_right_button()  # 放开格挡
            if self.check_fight_status(hwnd) is False:
                """
                如果怪消失了,右上角没有怪的buff了
                """
                break
            __skill_name: str = self._skill_func.get_skill(skill=self._skill_obj)
            if __skill_name is None:
                continue
            __skill_key: str = self._skill_obj[__skill_name]["key"]
            SetGhostBoards().click_press_and_release_by_key_name(__skill_key)
            self._skill_obj[__skill_name]["click_time"] = time.time()
            time.sleep(self._skill_obj[__skill_name]["active_cd"])  # 技能按下去后会有个动作，这个动作的持续时间
        if SetGhostMouse().is_mouse_button_pressed(3):
            # print("打怪结束当前是格挡状态，松开格挡")
            # 如果当前状态时格挡中
            SetGhostMouse().release_mouse_right_button()  # 放开格挡
        return True

    def fight_monster(self, hwnd):
        """
        开始打怪
        """

        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.5)
        # 按一下tab,锁定一下NPC怪
        SetGhostBoards().click_press_and_release_by_code(9)

        SetGhostMouse().click_mouse_right_button()  # 按住鼠标右键

        if self.__fight_func(hwnd):
            time.sleep(2)
            return True


class TeamFunc(TruckCar):

    def __init__(self):
        super().__init__()

    def create_team(self, hwnd, work_status: bool = True):
        """
        创建队伍
        """
        find_team: Team = self._get_pic_team()
        flag_status = find_team.flag_team_status
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            rec = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(flag_status))
            if rec is None:
                """
                说明没有队伍，需要创建一下
                """
                # print("未检测到队伍，进行创建")
                WindowsHandle().activate_windows(hwnd)
                time.sleep(0.2)
                SetGhostBoards().click_press_and_release_by_key_name("o")
                time.sleep(1)

                if self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_team.leave_team) is not None:
                    """
                    如果有离开的按钮,说明当前已经是组队状态
                    """
                    SetGhostBoards().click_press_and_release_by_key_name("o")
                    return True
                rec_create = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_team.create_team)
                if rec_create is not None:
                    SetGhostMouse().move_mouse_to(rec_create[0], rec_create[1])
                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(1)
                    SetGhostBoards().click_press_and_release_by_key_name("o")
            else:
                return True

    def add_team_member(self):
        """
        通过队伍成员的申请
        """
        pass

    def close_team(self, hwnd):
        """
        解散队伍
        """
        find_team: Team = self._get_pic_team()
        flag_status = find_team.leave_team

        WindowsHandle().activate_windows(hwnd)
        SetGhostBoards().click_press_by_key_name("o")
        time.sleep(1)

        if self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_team.create_team) is not None:
            """
            如果有创建的按钮,说明当前已经是非组队状态
            """
            return True

        __rec = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(flag_status))
        if __rec is not None:
            """
            找到了解散队伍的按钮
            """
            time.sleep(0.2)
            SetGhostMouse().move_mouse_to(__rec[0], __rec[1])
            time.sleep(1)
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            SetGhostBoards().click_press_and_release_by_key_name("o")
            time.sleep(1)
            return True
        return False


class FindTaskNPCFunc(TruckCar):
    """
    寻找押镖的NPC。
    根据不同的城市自动寻找。
    """

    def __init__(self):
        super().__init__()

    def find_truck_task_npc(self, hwnd: int, work_status: bool = True):
        """
        打开勤修
        """
        WindowsHandle().activate_windows(hwnd)
        find_npc: FindTruckCarTaskNPC = self._get_pic_find_task_npc()
        self.get_map_and_person(hwnd)
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            time.sleep(1)
            qin_xiu_rec = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_npc.qin_xiu)
            if qin_xiu_rec is None:
                continue
            else:
                """
                找到了勤修图标
                """
                # print(f"FindTaskNpc: 找到 勤修 图标({qin_xiu_rec[0]},{qin_xiu_rec[1]})")
                SetGhostMouse().move_mouse_to(qin_xiu_rec[0], qin_xiu_rec[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            time.sleep(1)
            qin_xiu_activity_list = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                              img=find_npc.qin_xiu_activity_list)
            if qin_xiu_activity_list is None:
                continue
            else:
                """
                找到活动列表
                """
                # print(f"FindTaskNpc: 找到 活动列表 图标({qin_xiu_activity_list[0]},{qin_xiu_activity_list[1]})")
                SetGhostMouse().move_mouse_to(qin_xiu_activity_list[0], qin_xiu_activity_list[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            time.sleep(1)
            qin_xiu_truck_task = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                           img=find_npc.qin_xiu_truck_car_task)
            if qin_xiu_truck_task is None:
                continue
            else:
                """
                找到了每日运镖图标
                """
                # print(f"FindTaskNpc: 找到 每日运镖 图标({qin_xiu_truck_task[0]},{qin_xiu_truck_task[1]})")
                SetGhostMouse().move_mouse_to(qin_xiu_truck_task[0], qin_xiu_truck_task[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            time.sleep(1)

            if self._area_map == "成都":
                __image_city: str = find_npc.task_point_chengdu
            elif self._area_map == "燕京":
                __image_city: str = find_npc.task_point_yanjing
            elif self._area_map == "金陵":
                __image_city: str = find_npc.task_point_jinling
            elif self._area_map == "苏州":
                __image_city: str = find_npc.task_point_suzhou
            elif self._area_map == "洛阳":
                __image_city: str = find_npc.task_point_luoyang
            else:
                __image_city: str = find_npc.task_point_chengdu
            # qin_xiu_truck_point = self.windows.find_windows_coordinate_rect(handle=hwnd,
            #                                                                 img=__image_city)

            __pic = self.windows.capture(hwnd)
            __cap_pic = bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))

            qin_xiu_truck_point = self.windows.find_windows_coordinate_rect_img(handle=hwnd, img=__image_city,
                                                                                origin_img=__cap_pic)

            if qin_xiu_truck_point is None:
                continue
            else:
                """
                找到了成都
                """
                # print(f"FindTaskNpc: 找到 {self._area_map} 图标({qin_xiu_truck_point[0]},{qin_xiu_truck_point[1]})")
                SetGhostMouse().move_mouse_to(qin_xiu_truck_point[0], qin_xiu_truck_point[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break

        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            time.sleep(1)

            if self._area_map == "成都":
                __image_city_npc: str = find_npc.task_point_chengdu_npc
            elif self._area_map == "燕京":
                __image_city_npc: str = find_npc.task_point_yanjing_npc
            elif self._area_map == "金陵":
                __image_city_npc: str = find_npc.task_point_jinling_npc
            elif self._area_map == "苏州":
                __image_city_npc: str = find_npc.task_point_suzhou_npc
            elif self._area_map == "洛阳":
                __image_city_npc: str = find_npc.task_point_luoyang_npc
            else:
                __image_city_npc: str = find_npc.task_point_chengdu_npc

            __pic = self.windows.capture(hwnd)
            __cap_pic = bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))

            qin_xiu_truck_point_npc = self.windows.find_windows_coordinate_rect_img(handle=hwnd, img=__image_city_npc,
                                                                                    origin_img=__cap_pic)
            if qin_xiu_truck_point_npc is None:
                continue
            else:
                """
                找到了押镖NPC
                """
                # print(f"FindTaskNpc: 找到 {self._area_map} 的NPC图标({qin_xiu_truck_point_npc[0]},{qin_xiu_truck_point_npc[1]})")
                SetGhostMouse().move_mouse_to(qin_xiu_truck_point_npc[0], qin_xiu_truck_point_npc[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                SetGhostBoards().click_press_and_release_by_code(27)
                break
        return True


class ReceiveTruckTask(TruckCar):
    """
    接取押镖任务
    """

    def __init__(self):
        super().__init__()

    def receive_task(self, hwnd: int):
        """
        接取任务,
        暂时只实现了成都和燕京
        """
        WindowsHandle().activate_windows(hwnd)
        find_task: TruckCarReceiveTask = self._get_pic_receive_task()
        self.get_map_and_person(hwnd)
        while 1:
            time.sleep(1)
            truck_npc_receive_task_talk = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                    img=find_task.receive_task_talk)
            if truck_npc_receive_task_talk is None:
                continue
            else:
                """
                已经点开了NPC
                """
                # print(f"ReceiveTruckTask: 已经找到 接取任务的NPC 图标({truck_npc_receive_task_talk[0]},{truck_npc_receive_task_talk[1]})")

                SetGhostMouse().move_mouse_to(truck_npc_receive_task_talk[0], truck_npc_receive_task_talk[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)

            if self._area_map == "成都":
                __image_city_npc: str = find_task.task_chengdu_NanGongShiJia
            elif self._area_map == "燕京":
                __image_city_npc: str = find_task.task_yanjing_JunMaChang
            elif self._area_map == "金陵":
                __image_city_npc: str = find_task.task_jinlin_HuangJiaLieChang
            elif self._area_map == "苏州":
                __image_city_npc: str = find_task.task_suzhou_CaiShiChang
            elif self._area_map == "洛阳":
                __image_city_npc: str = find_task.task_luoyang_YanMenShiJia
            else:
                __image_city_npc: str = find_task.task_chengdu_NanGongShiJia

            truck_npc_receive_task_address = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                       img=__image_city_npc)
            if truck_npc_receive_task_address is None:
                continue
            else:
                """
                选择押镖目的地
                """
                # print(f"ReceiveTruckTask: 已经找到 目的地 图标({truck_npc_receive_task_address[0]},{truck_npc_receive_task_address[1]})")

                SetGhostMouse().move_mouse_to(truck_npc_receive_task_address[0], truck_npc_receive_task_address[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_car_type = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.car_type_little)
            if truck_car_type is None:
                continue
            else:
                """
                选择镖车的车型
                """
                # print(f"ReceiveTruckTask: 已经找到 镖车车型 图标({truck_car_type[0]},{truck_car_type[1]})")

                SetGhostMouse().move_mouse_to(truck_car_type[0], truck_car_type[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)

            truck_receive_task = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.receive_task)
            if truck_receive_task is None:
                continue
            else:
                """
                接镖
                """
                # print(f"ReceiveTruckTask: 已经找到 接镖 图标({truck_receive_task[0]},{truck_receive_task[1]})")

                SetGhostMouse().move_mouse_to(truck_receive_task[0], truck_receive_task[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_receive_task_confirm = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                   img=find_task.receive_task_confirm)
            if truck_receive_task_confirm is None:
                continue
            else:
                """
                确认接镖
                """
                # print(f"ReceiveTruckTask: 已经找到 确认接镖 图标({truck_receive_task_confirm[0]},{truck_receive_task_confirm[1]})")

                SetGhostMouse().move_mouse_to(truck_receive_task_confirm[0], truck_receive_task_confirm[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        return True


class TransportTaskFunc(TruckCar):
    """
    接完任务后寻找镖车，并点击 “驾车” 开始运输
    期间可能会出现 劫镖NPC
    """

    def __init__(self):
        super().__init__()

    def transport_truck(self, hwnd: int) -> bool:
        """
        开始运镖
        """
        transport_pos = self._find_driver_truck_type(hwnd)
        if transport_pos is not None:
            # print(f"TransportTaskFunc: 找到了 镖车(驾车) 的坐标({transport_pos[0]},{transport_pos[1]})")
            SetGhostMouse().move_mouse_to(transport_pos[0], transport_pos[1])
            time.sleep(0.1)
            SetGhostMouse().click_mouse_left_button()

            time.sleep(0.5)
            find_pic = self.windows.capture(hwnd)
            find_pics = find_pic.pic_content[int(find_pic.pic_height * 0.1):int(find_pic.pic_height * 0.5),
                        int(find_pic.pic_width * 0.3):int(find_pic.pic_width * 0.7)]
            if self.ocr.find_ocr(find_pics, "距离NPC太远") is not None:
                """
                如果出现距离NPC太远了，说明开车失败了
                """
                # print("TransportTaskFunc: 出现“距离NPC太远”的提示")
                return False
            # 鼠标离镖车远一点
            pos = coordinate_change_from_windows(hwnd, (100, 100))
            SetGhostMouse().move_mouse_to(pos[0], pos[1])
            return True
        # print(f"TransportTaskFunc: 未找到镖车的 “驾车” 按钮")
        return False

    def find_truck_car_in_display(self, hwnd: int) -> bool:
        """
        查找镖车释放在屏幕中
        """
        # 看看镖车在不在
        res_car = self.find_car_pos_in_display(hwnd)
        if res_car is not None:
            return True
        return False

    def find_car_pos_in_display_quadrant(self, hwnd: int) -> int:
        """
        查找镖车在第几象限
        :return 0 表示没找到镖车，1-4表示1-4象限
        """
        __res_car = self.find_car_pos_in_display(hwnd)
        if __res_car is None:
            return 0
        cap = self.windows.capture(hwnd)
        __car_quadrant: int = self.check_target_pos_direction(cap, target_pos=__res_car)
        return __car_quadrant

    def find_truck_car_center_pos(self, hwnd: int, find_count: int = 10, is_break: bool = False) -> tuple or None:
        """
        保持镖车在屏幕中间
        """
        for i in range(find_count):
            time.sleep(1)

            if is_break:
                # 强行终止
                break

            # 看看镖车在不在
            res_car = self.find_car_pos_in_display(hwnd)
            if res_car is not None:
                # 如果镖车在，那么就看看在不在中间
                while 1:

                    if is_break:
                        # 强行终止
                        break
                    res_center_car = self.find_car_center_pos_in_display(hwnd)
                    if res_center_car is not None:
                        # 在中间
                        # print("镖车在屏幕中间位置")
                        return res_center_car
                    # print("镖车在屏幕上，但是不在中间位置")
                    __res_car = self.find_car_pos_in_display(hwnd)
                    if __res_car is None:
                        return None
                    cap = self.windows.capture(hwnd)
                    __car_quadrant: int = self.check_target_pos_direction(cap, target_pos=__res_car)
                    # print(f"镖车在屏幕的第 {__car_quadrant} 象限")
                    if __car_quadrant == 1:
                        """a
                        如果在第一象限，但是不符合规则；那么就向 左侧 转一下
                        """
                        SetGhostBoards().click_press_and_release_by_key_code_hold_time(37, 0.1)
                    elif __car_quadrant == 2:
                        """
                        如果在第二象限，但是不符合规则；那么就向 右侧 转一下
                        """
                        SetGhostBoards().click_press_and_release_by_key_code_hold_time(39, 0.1)
                    elif __car_quadrant == 3:
                        """
                        如果在第三象限，就转一个大的，转到第一象限去
                        """
                        SetGhostBoards().click_press_and_release_by_key_code_hold_time(37, 0.4)
                    elif __car_quadrant == 4:
                        """
                        如果在第四象限，就转一个大的，转到第二象限去
                        """
                        SetGhostBoards().click_press_and_release_by_key_code_hold_time(39, 0.4)
            WindowsHandle().activate_windows(hwnd)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(37, 0.5)
            time.sleep(0.5)
            # print("镖车不在在屏幕上，转个45度")
        return None

    def find_driver_truck_type(self, hwnd: int):
        """
        查询 驾车 按钮有没有出现
        """
        return self._find_driver_truck_type(hwnd)

    def check_task_status(self, hwnd: int) -> bool:
        """
        检测押镖是否已经在NPC处接了任务
        """
        return self._check_task_status(hwnd)

    def check_task_end(self, hwnd: int) -> bool:
        """
        检测押镖是否结束
        """
        if self._check_task_end(hwnd):
            return True
        return False

    def check_person_move_status(self, hwnd: int, check_wait_time: float):
        """
        检测指定时间的前后，地图坐标是否有更新
        """
        pos, _, _ = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)
        time.sleep(check_wait_time)
        if self._check_person_move_status(hwnd, pos) is False:
            return False
        return True


class UserGoods(TruckCar):
    """
    使用物品
    """
    def __init__(self):
        super().__init__()

    def open_bag(self, hwnd: int):
        """
        打开物品背包
        """
        __bag: Goods = self._get_bag_goods()
        __goods_bag_tag_clickable = __bag.goods_bag_tag_clickable  # 没有点击
        __goods_bag_tag_clicked = __bag.goods_bag_tag_clicked  # 已经点击

        WindowsHandle().activate_windows(hwnd)
        time.sleep(1)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
        time.sleep(1)

        __rec_goods_bag_tag_clicked = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__goods_bag_tag_clicked))
        __rec_goods_bag_tag_clickable = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__goods_bag_tag_clickable))

        __rec_bag = __rec_goods_bag_tag_clicked if __rec_goods_bag_tag_clicked is not None else __rec_goods_bag_tag_clickable if __rec_goods_bag_tag_clickable is not None else None

        if __rec_bag is not None:
            time.sleep(1)
            SetGhostMouse().move_mouse_to(__rec_bag[0], __rec_bag[1])
            SetGhostMouse().click_mouse_left_button()
            return True
        return False

    def use_yu_feng_shen_shui(self, hwnd):
        """
        使用御风神水
        """

        __bag: Goods = self._get_bag_goods()
        __yf_goods = __bag.run_goods
        __yf_goods_ready = __bag.run_goods_ready
        __yf_goods_buff = __bag.run_goods_buff

        pic = self.windows.capture(hwnd)
        # 高度1-300像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.4), int(pic.pic_width * 0.5):int(pic.pic_width)]
        __yf_buff_status = find_area(smaller_pic=self._load_pic(__yf_goods_buff), bigger_img=pic_content)
        if __yf_buff_status[-1] > 0.5:
            return True

        self.open_bag(hwnd)

        time.sleep(1)
        __rec_yf_goods = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__yf_goods))
        if __rec_yf_goods is not None:
            """
            如果找到了御风神水
            """
            time.sleep(1)
            SetGhostMouse().move_mouse_to(__rec_yf_goods[0], __rec_yf_goods[1])
            time.sleep(1)
            SetGhostMouse().click_mouse_right_button()
            for i in range(10):
                # 等待10秒
                time.sleep(1)
                __rec_yf_goods_ready = self.windows.find_windows_coordinate_rect(hwnd, img=self._load_pic(__yf_goods_ready))

                if __rec_yf_goods_ready is not None or self.ocr.find_ocr(image=self.windows.capture(hwnd).pic_content, temp_text="不断跑动跳跃"):
                    SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
                    return True
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
        return False
