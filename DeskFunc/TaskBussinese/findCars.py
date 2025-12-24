# -*- coding: utf-8 -*-
import time
from collections import namedtuple

import cv2
import numpy as np
from numpy import fromfile

from DeskFunc.TaskBussinese.findSkill import SkillGroup
from Utils.FindWindowsImage import WindowsCapture, WindowsHandle, FindWindowsImageTemplate, PicCapture
from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from Utils.dataClass import FindTruckCarTaskNPC, MapPic, Team, BackpackItem, TruckCarReceiveTask, TruckCarPic, \
    PersonStatusAndBuff
from Utils.loadResources import GetConfig, get_skill_group_list


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
        self._map_pic = None  # 地图

        self._person_buff = None  # 人物状态

        self.windows_cap = WindowsCapture()
        self.windows_find = FindWindowsImageTemplate()
        self.ocr = FindPicOCR()
        self._skill_func = SkillGroup()

        self.hwnd: int = 0

        self._area_map, self._person_name = None, None
        self._skill_obj: dict = get_skill_group_list().get("打怪套路")  # 当前正在使用的技能组

    def get_map_and_person(self, hwnd: int):
        pos, self._area_map, self._person_name = self.ocr.get_person_map(self.windows_cap.capture(hwnd).pic_content)
        # print(f"当前地图是 {self._area_map}, 当前角色是 {self._person_name}")
        return self._area_map

    def get_map_and_pos(self, hwnd: int):
        pos, self._area_map, self._person_name = self.ocr.get_person_map(self.windows_cap.capture(hwnd).pic_content)
        # print(f"当前地图是 {self._area_map}, 当前角色是 {self._person_name}")
        return pos

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

    def _get_map(self) -> MapPic:
        if self._map_pic is None:
            self._map_pic = GetConfig().get_map_pic()
        return self._map_pic

    def _get_pic_team(self) -> Team():
        """
        检查队伍是否创建
        """
        if self._find_team is None:
            self._find_team = self._config.get_team()
        return self._find_team

    def _get_bag_goods(self) -> BackpackItem:
        """
        获取物品背包
        """
        if self._find_tag_goods is None:
            self._find_tag_goods = self._config.get_backpack_item_pic()
        return self._find_tag_goods

    def _get_pic_receive_task(self) -> TruckCarReceiveTask:
        """
        接取任务和押镖的路上
        """
        if self._receive_task is None:
            self._receive_task = self._config.get_track_car()
        return self._receive_task

    def _get_pic_truck_car(self) -> TruckCarPic:
        """
        开始押镖了
        """
        if self._receive_task_road is None:
            self._receive_task_road = self._config.truck_task()
        return self._receive_task_road

    def _get_person_buff(self) -> PersonStatusAndBuff:
        """
        人物右上角BUFF
        :return:
        """
        if self._person_buff is None:
            self._person_buff = self._config.find_person_buff()
        return self._person_buff

    def break_other_truck_car(self, hwnd: int):
        """
        退出不小心点到别人的镖车触发劫镖
        """
        __find_task_car: TruckCarPic = self._get_pic_truck_car()
        __break_car_talk = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__find_task_car.fight_other_truck_car))
        if __break_car_talk is None:
            return False
        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.1)
        SetGhostBoards().click_press_and_release_by_code(27)
        time.sleep(0.2)
        return True

    def break_npc_talk(self, hwnd: int):
        """
        退出和NPC对话的窗口
        """
        __find_task: TruckCarReceiveTask = self._get_pic_receive_task()
        __break_npc_talk = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__find_task.break_npc_talk))
        __receive_task_talk = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__find_task.receive_task_talk))
        if __break_npc_talk is None:
            return False
        elif __receive_task_talk is not None:
            # 如果有接任务的按钮，说明不是点到路上到处走的NPC了
            return True
        WindowsHandle().activate_windows(hwnd)
        time.sleep(0.1)
        SetGhostMouse().move_mouse_to(__break_npc_talk[0], __break_npc_talk[1])
        time.sleep(0.5)
        SetGhostMouse().click_mouse_left_button()
        return True

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
    def check_target_pos_direction(img: PicCapture, target_pos: tuple) -> int:
        """
        检查传入的坐标是否是在屏幕中间的区域
        :return 4象限： 1：左上角，2，右上角，3. 左下角， 4. 右下角
        """
        __img = img
        __w, __h = __img.pic_width, __img.pic_height

        center_x = int(__w * 0.5)  # 屏幕正中间
        center_y = int(__h * 0.5)  # 屏幕正中间
        # print(f"图片的宽高 {__w}_{__h}, 中心坐标是 ({center_x},{center_y}), 目标坐标：{target_pos[0]}_{target_pos[1]}")

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
        task_flag_status = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_task.task_flag_status))
        if task_flag_status is None:
            """
            押镖状态没有了，可能是被
            需要重新接镖。
            有以下原因：
            1、押镖结束
            2、打怪失败
            3、被四害干扰了
            """
            return False
        return True

    def check_task_end(self, hwnd: int) -> bool:
        """
        检测押镖是否结束
        """
        if len(self.ocr.find_ocr_arbitrarily(self.windows_cap.capture(hwnd).pic_content,
                                             ["获得帮派贡献度", "为帮会带来"])) > 0:
            # print("DriverTruckCarFuc: 运镖结束")
            return True
        return False

    def _find_driver_truck_type(self, hwnd: int):
        """
        检查 运镖(驾车) 按钮。
        图片模板的识别速度比文字快，所以这里先找图再找文字
        """
        time.sleep(1)
        __img_car = self.windows_cap.capture(hwnd)
        # 先找图片模板的驾车按钮在不在
        find_task: TruckCarPic = self._get_pic_truck_car()
        cos = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_task.task_star_mode))
        if cos is not None:
            return cos
        return None

    def find_car_in_center_display_v3(self, hwnd: int = None, image: PicCapture = None, display_area: int = 0) -> bool:
        """
        :param hwnd: 句柄
        :param image: 图片
        :param display_area: 0，表示 1，2象限的屏幕中间，用于接镖找车. 1，表示1234象限中间。用于打怪后找车
        """
        if image is not None:
            __h, __w, __content = image.pic_height, image.pic_width, image.pic_content
        else:
            image = self.windows_cap.capture(hwnd)
            __h, __w, __content = image.pic_height, image.pic_width, image.pic_content
        if display_area == 0:
            _v3_new_pic = image.pic_content[1:int(image.pic_height * 0.6),
                          int(image.pic_width * 0.4):int(image.pic_width * 0.6)]
        else:
            _v3_new_pic = image.pic_content[1:int(image.pic_height * 0.6),
                          int(image.pic_width * 0.3):int(image.pic_width * 0.7)]

        __rec = self.ocr.find_truck_car_ocr(_v3_new_pic, "的镖车")
        if __rec is None:
            return False
        return True

    def find_car_pos_in_display_v2(self, hwnd: int, pic_content: np.ndarray) -> tuple or None:
        rec = self.ocr.find_truck_car_ocr(pic_content, "的镖车")
        if rec is not None:
            return rec
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
        pic = self.windows_cap.capture(hwnd)
        # 高度1-300像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.4), int(pic.pic_width * 0.5):int(pic.pic_width)]
        task_monster_fight = self.windows_find.get_image_all_rect(pic_content, self._load_pic(self.__find_task.task_monster_fight))
        if task_monster_fight is not None:
            for xx in task_monster_fight:
                if xx[-1] > 0.8:
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
        pic = self.windows_cap.capture(hwnd)
        # 高度1-30%像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.3), int(pic.pic_width * 0.3):int(pic.pic_width * 0.7)]
        fight_tag_skill: str = self.__find_task.task_monster_target_skil

        task_monster_fight = self.windows_find.get_image_all_rect(pic_content, self._load_pic(fight_tag_skill))
        if task_monster_fight is not None:
            for xx in task_monster_fight:
                if xx[-1] > 0.5:
                    """
                        如果出现了相似度大于0.5的 出现了战投的图标
                        方法2: 如果出现了 进入战斗的图标（进入战斗的文字模板和右上角的NPC标志），那么就说明进入战斗了
                        """
                    # print("进入战斗: 查询到进入战斗的模板")
                    return True
        return False

    def __fight_func(self, hwnd: int):
        """
        打怪啊
        """
        is_skill_tag_status: int = 0  # 是否结束释放按钮， 0,表示 初始化，1 表示 技能条出现中，2表示技能条结束

        if SetGhostMouse().is_mouse_button_pressed(3) is False:
            # print("鼠标右键未按住，开始格挡")
            SetGhostMouse().press_mouse_right_button()

        time.sleep(0.1)
        while 1:
            if self._check_monster_skill_status(hwnd):
                # print("怪要放技能了，进行格挡")
                is_skill_tag_status = 1

                SetGhostBoards().click_press_and_release_by_key_code_hold_time(32, 0.5)
                SetGhostBoards().click_press_and_release_by_key_code_hold_time(32, 0.5)
                time.sleep(2)  # 2秒等待刚好落地
            else:
                if is_skill_tag_status == 1:
                    # 表示放技能的图标已经消失了，
                    # time.sleep(0.5)
                    is_skill_tag_status = 0
            if not self.check_fight_status(hwnd):
                """
                如果怪消失了,右上角没有怪的buff了
                """
                break
            __skill_name: str = self._skill_func.get_skill(skill=self._skill_obj)
            if __skill_name is None:
                continue

            # 如果这个技能是需要选中地面的，那么就把鼠标移动的中心点
            if self._skill_obj[__skill_name].get("need_ground", False):
                pic = self.windows_cap.capture(hwnd)
                pos_content: tuple = (int(pic.pic_width / 2), int(pic.pic_height / 2))
                center_pos_in_screen: tuple = coordinate_change_from_windows(hwnd, pos_content)
                SetGhostMouse().move_mouse_to(center_pos_in_screen[0], center_pos_in_screen[1])

            __skill_key: str = self._skill_obj[__skill_name]["key"]
            SetGhostBoards().click_press_and_release_by_key_name(__skill_key)

            if self._skill_obj[__skill_name].get("need_ground", False):
                time.sleep(0.3)
                SetGhostMouse().click_mouse_left_button()

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

        # 避免异常,先释放一下所有按钮和鼠标
        SetGhostMouse().release_all_mouse_button()
        SetGhostBoards().release_all_key()

        time.sleep(0.5)
        # 按一下tab,锁定一下NPC怪
        SetGhostBoards().click_press_and_release_by_code(9)
        time.sleep(0.2)
        # SetGhostMouse().click_mouse_right_button()  # 按住鼠标右键

        if self.__fight_func(hwnd):
            time.sleep(3)
            return True
        return False


class TeamFunc(TruckCar):

    def __init__(self):
        super().__init__()

    def check_team_status(self, hwnd: int):
        """
        检测当前是否为组队
        """
        find_team: Team = self._get_pic_team()
        button_create_team = find_team.create_team
        button_leave_team = find_team.leave_team

        for i in range(5):
            WindowsHandle().activate_windows(hwnd)
            time.sleep(0.2)
            SetGhostBoards().click_press_and_release_by_key_name("o")
            time.sleep(0.5)
            for button in [button_create_team, button_leave_team]:
                flag_status_rec = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(button), threshold=0.85)
                if flag_status_rec is None:
                    continue
                if button == button_create_team:
                    return "Create", flag_status_rec
                return "Leave", flag_status_rec
        return None

    def create_team(self, hwnd: int) -> bool:
        """
        创建队伍
        """
        rec_create = self.check_team_status(hwnd)
        if rec_create is None:
            return False
        _type, _rec = rec_create
        if _type == "Leave":
            # 找到了 Leave 按钮 表示为当前是组队状态
            return True

        if _rec is not None:
            SetGhostMouse().move_mouse_to(_rec[0], _rec[1])
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            SetGhostBoards().click_press_and_release_by_key_name("o")
            return True
        return False

    def add_team_member(self):
        """
        通过队伍成员的申请
        """
        pass

    def close_team(self, hwnd) -> bool:
        """
        解散队伍
        """
        rec_leave = self.check_team_status(hwnd)
        if rec_leave is None:
            return False
        _type, _rec = rec_leave
        if _type == "Create":
            # 找到了 Create 按钮 表示为当前是未组队状态
            SetGhostBoards().click_press_and_release_by_key_name("o")
            return True

        if _rec is not None:
            SetGhostMouse().move_mouse_to(_rec[0], _rec[1])
            time.sleep(0.3)
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            SetGhostBoards().click_press_and_release_by_key_name("o")
            return True
        return False


# class FindTaskNPCFunc(TruckCar):
#     """
#     寻找押镖的NPC。
#     根据不同的城市自动寻找。
#     """
#
#     def __init__(self):
#         super().__init__()
#
#         self.city_npc = None
#
#     def find_truck_task_npc(self, hwnd: int):
#         """
#         打开勤修
#         """
#
#         if self.city_npc is not None:
#             # 表示这是第二次进来, 可以简单点
#             __pic = self.windows_cap.capture(hwnd)
#             __cap_pic = bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))
#
#             qin_xiu_truck_point_npc = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(self.city_npc))
#             if qin_xiu_truck_point_npc is not None:
#                 """
#                 找到了押镖NPC
#                 """
#                 # print(f"FindTaskNpc: 找到 {self._area_map} 的NPC图标({qin_xiu_truck_point_npc[0]},{qin_xiu_truck_point_npc[1]})")
#                 SetGhostMouse().move_mouse_to(qin_xiu_truck_point_npc[0], qin_xiu_truck_point_npc[1])
#                 time.sleep(0.5)
#                 SetGhostMouse().click_mouse_left_button()
#                 # SetGhostBoards().click_press_and_release_by_code(27)  # 先去掉关闭寻路的窗口
#                 return True
#             else:
#                 self.city_npc = None
#                 return False
#
#         WindowsHandle().activate_windows(hwnd)
#         find_npc: FindTruckCarTaskNPC = self._get_pic_find_task_npc()
#         self.get_map_and_person(hwnd)
#
#         # time.sleep(0.2)
#         # SetGhostBoards().click_press_and_release_by_key_name("N")
#
#         time.sleep(0.5)
#         qin_xiu_rec = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_npc.bang_hui))
#         if qin_xiu_rec is None:
#             time.sleep(0.2)
#             SetGhostBoards().click_press_and_release_by_key_name("N")
#
#         time.sleep(1)
#         qin_xiu_rec = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_npc.bang_hui))
#         if qin_xiu_rec is None:
#             return False
#
#         SetGhostMouse().move_mouse_to(qin_xiu_rec[0], qin_xiu_rec[1])
#         time.sleep(0.5)
#         SetGhostMouse().click_mouse_left_button()
#
#         while 1:
#
#             time.sleep(0.5)
#
#             if self._area_map == "成都":
#                 __image_city: str = find_npc.task_point_chengdu
#             elif self._area_map == "燕京":
#                 __image_city: str = find_npc.task_point_yanjing
#             elif self._area_map == "金陵":
#                 __image_city: str = find_npc.task_point_jinling
#             elif self._area_map == "苏州":
#                 __image_city: str = find_npc.task_point_suzhou
#             elif self._area_map == "洛阳":
#                 __image_city: str = find_npc.task_point_luoyang
#             else:
#                 __image_city: str = find_npc.task_point_chengdu
#             # qin_xiu_truck_point = self.windows.find_windows_coordinate_rect(handle=hwnd,
#             #                                                                 img=__image_city)
#
#             __pic = self.windows_cap.capture(hwnd)
#             __cap_pic = bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))
#
#             qin_xiu_truck_point = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__image_city))
#
#             if qin_xiu_truck_point is None:
#                 continue
#             else:
#
#                 if self._area_map == "成都":
#                     # 界面打开后，默认就是成都，所以不需要再点击
#                     break
#                 # print(f"FindTaskNpc: 找到 {self._area_map} 图标({qin_xiu_truck_point[0]},{qin_xiu_truck_point[1]})")
#                 SetGhostMouse().move_mouse_to(qin_xiu_truck_point[0], qin_xiu_truck_point[1])
#                 time.sleep(1)
#                 SetGhostMouse().click_mouse_left_button()
#                 break
#
#         while 1:
#
#             time.sleep(0.5)
#
#             if self._area_map == "成都":
#                 __image_city_npc: str = find_npc.task_point_chengdu_npc
#             elif self._area_map == "燕京":
#                 __image_city_npc: str = find_npc.task_point_yanjing_npc
#             elif self._area_map == "金陵":
#                 __image_city_npc: str = find_npc.task_point_jinling_npc
#             elif self._area_map == "苏州":
#                 __image_city_npc: str = find_npc.task_point_suzhou_npc
#             elif self._area_map == "洛阳":
#                 __image_city_npc: str = find_npc.task_point_luoyang_npc
#             else:
#                 __image_city_npc: str = find_npc.task_point_chengdu_npc
#
#             __pic = self.windows_cap.capture(hwnd)
#             __cap_pic = bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))
#
#             qin_xiu_truck_point_npc = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__image_city_npc))
#             if qin_xiu_truck_point_npc is None:
#                 continue
#             else:
#                 """
#                 找到了押镖NPC
#                 """
#
#                 self.city_npc = __image_city_npc
#
#                 # print(f"FindTaskNpc: 找到 {self._area_map} 的NPC图标({qin_xiu_truck_point_npc[0]},{qin_xiu_truck_point_npc[1]})")
#                 SetGhostMouse().move_mouse_to(qin_xiu_truck_point_npc[0], qin_xiu_truck_point_npc[1])
#                 time.sleep(0.5)
#                 SetGhostMouse().click_mouse_left_button()
#                 # SetGhostBoards().click_press_and_release_by_code(27)  # 先去掉关闭寻路的窗口
#                 break
#         return True


class FindTaskNPCFunc(TruckCar):
    """
    寻找押镖的NPC（优化版）。
    根据不同的城市自动寻找，提升查找效率和稳定性。
    """

    def __init__(self):
        super().__init__()
        self.city_npc = None
        self.max_retry_attempts = 5  # 最大重试次数
        self.city_name = ""

    def find_truck_task_npc(self, hwnd: int, city_name: str) -> bool:
        """
        查找并点击押镖任务NPC
        优化点：
        1. 添加超时控制，防止无限循环
        2. 简化成都特殊处理逻辑
        3. 统一错误处理
        4. 清理无用代码
        """
        try:
            # 如果已有缓存的NPC图标路径，优先快速查找
            if self.city_npc is not None:
                if self._quick_find_npc(hwnd):
                    return True
                else:
                    # 缓存失效，清除缓存
                    self.city_npc = None

            # 激活窗口并获取地图信息
            WindowsHandle().activate_windows(hwnd)
            find_npc: FindTruckCarTaskNPC = self._get_pic_find_task_npc()
            self.get_map_and_person(hwnd)

            # 查找并点击帮会图标
            if not self._click_bang_hui(hwnd, find_npc):
                return False

            self.city_name = city_name
            # 查找城市任务点图标
            city_image_path = self._get_city_image_path(find_npc, is_npc=False)
            if not self._click_city_point(hwnd, city_image_path):
                return False

            # 查找并点击具体的押镖NPC图标
            npc_image_path = self._get_city_image_path(find_npc, is_npc=True)
            if self._click_npc_point(hwnd, npc_image_path):
                # 缓存NPC图标路径
                self.city_npc = npc_image_path
                return True

            return False

        except Exception as e:
            print(f"查找押镖NPC时发生错误: {e}")
            return False

    def _quick_find_npc(self, hwnd: int) -> bool:
        """快速查找已知NPC"""
        try:
            qin_xiu_truck_point_npc = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._load_pic(self.city_npc),
                threshold=0.8
            )
            if qin_xiu_truck_point_npc is not None:
                SetGhostMouse().move_mouse_to(qin_xiu_truck_point_npc[0], qin_xiu_truck_point_npc[1])
                time.sleep(0.3)
                SetGhostMouse().click_mouse_left_button()
                return True
            return False
        except:
            return False

    def _click_bang_hui(self, hwnd: int, find_npc: FindTruckCarTaskNPC) -> bool:
        """查找并点击帮会图标"""
        attempts = 0
        while attempts < self.max_retry_attempts:
            qin_xiu_rec = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._load_pic(find_npc.bang_hui),
                threshold=0.8
            )

            if qin_xiu_rec is not None:
                SetGhostMouse().move_mouse_to(qin_xiu_rec[0], qin_xiu_rec[1])
                time.sleep(0.3)
                SetGhostMouse().click_mouse_left_button()
                return True

            # 如果没找到，按N键打开NPC面板
            time.sleep(0.2)
            SetGhostBoards().click_press_and_release_by_key_name("N")
            time.sleep(0.5)
            attempts += 1

        return False

    def _get_city_image_path(self, find_npc: FindTruckCarTaskNPC, is_npc: bool) -> str:
        """根据当前地图获取对应城市图标路径"""
        city_mappings = {
            "成都": (find_npc.task_point_chengdu, find_npc.task_point_chengdu_npc),
            "燕京": (find_npc.task_point_yanjing, find_npc.task_point_yanjing_npc),
            "金陵": (find_npc.task_point_jinling, find_npc.task_point_jinling_npc),
            "苏州": (find_npc.task_point_suzhou, find_npc.task_point_suzhou_npc),
            "洛阳": (find_npc.task_point_luoyang, find_npc.task_point_luoyang_npc)
        }

        # 默认使用成都图标
        default_mapping = (find_npc.task_point_chengdu, find_npc.task_point_chengdu_npc)
        city_mapping = city_mappings.get(self.city_name, default_mapping)

        return city_mapping[1] if is_npc else city_mapping[0]

    def _click_city_point(self, hwnd: int, image_path: str) -> bool:
        """点击城市任务点图标"""
        # 成都特殊处理：界面默认打开成都，无需点击
        if self.city_name == "成都":
            return True

        attempts = 0
        while attempts < self.max_retry_attempts:
            __pic = self.windows_cap.capture(hwnd)
            point_rec = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._load_pic(image_path),
                threshold=0.8
            )

            if point_rec is not None:
                SetGhostMouse().move_mouse_to(point_rec[0], point_rec[1])
                time.sleep(0.5)
                SetGhostMouse().click_mouse_left_button()
                return True

            time.sleep(0.5)
            attempts += 1

        return False

    def _click_npc_point(self, hwnd: int, npc_image_path: str) -> bool:
        """点击具体的押镖NPC图标"""
        attempts = 0
        while attempts < self.max_retry_attempts:
            __pic = self.windows_cap.capture(hwnd)
            bitwise_and(__pic.pic_content, (0, 0, __pic.pic_width, int(__pic.pic_height * 0.4)))

            npc_rec = self.windows_find.get_windows_image_rect(
                hwnd,
                read_image=self._load_pic(npc_image_path),
                threshold=0.8
            )

            if npc_rec is not None:
                SetGhostMouse().move_mouse_to(npc_rec[0], npc_rec[1])
                time.sleep(0.3)
                SetGhostMouse().click_mouse_left_button()
                return True

            time.sleep(0.5)
            attempts += 1

        return False



class ReceiveTruckTask(TruckCar):
    """
    接取押镖任务
    """

    def __init__(self):
        super().__init__()
        self.find_task: TruckCarReceiveTask = self._get_pic_receive_task()


    def is_talk_npc(self, hwnd: int):
        """
        是否已经与NPC对话
        """

        time.sleep(1)
        truck_npc_receive_task_talk = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(self.find_task.receive_task_talk),  threshold=0.85)
        if truck_npc_receive_task_talk is None:
            return None
        return truck_npc_receive_task_talk

    def day_task(self, hwnd: int) -> int:
        """
        尝试接取每日任务
        """

        # 看看是否已经与NPC对话
        truck_npc_receive_task_talk = self.is_talk_npc(hwnd)
        if truck_npc_receive_task_talk is None:
            return -1

        find_day_task = self._get_pic_truck_car()
        step_1 = find_day_task.day_task_step_1
        step_2 = find_day_task.day_task_step_2
        step_3 = find_day_task.day_task_step_3

        for pic in [step_1, step_2, step_3]:
            pic_rec = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(pic), threshold=0.85)
            if pic_rec is None:
                # print(f"没有找到 {pic}")
                return 0
            WindowsHandle().activate_windows(hwnd)
            SetGhostMouse().move_mouse_to(pic_rec[0], pic_rec[1])
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1.5)
        return 1

    def receive_task(self, hwnd: int, npc_city: str) -> bool:
        """
        接取任务,
        暂时只实现了成都和燕京
        """

        # 看看是否已经与NPC对话
        truck_npc_receive_task_talk = self.is_talk_npc(hwnd)
        if truck_npc_receive_task_talk is None:
            return False
        else:
            """
            已经点开了NPC
            """
            WindowsHandle().activate_windows(hwnd)
            SetGhostMouse().move_mouse_to(truck_npc_receive_task_talk[0], truck_npc_receive_task_talk[1])
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()

        find_task: TruckCarReceiveTask = self._get_pic_receive_task()
        while 1:
            time.sleep(1)

            if npc_city == "成都":
                __image_city_npc: str = find_task.task_chengdu_NanGongShiJia
            elif npc_city == "燕京":
                __image_city_npc: str = find_task.task_yanjing_JunMaChang
            elif npc_city == "金陵":
                __image_city_npc: str = find_task.task_jinlin_HuangJiaLieChang
            elif npc_city == "苏州":
                __image_city_npc: str = find_task.task_suzhou_CaiShiChang
            elif npc_city == "洛阳":
                __image_city_npc: str = find_task.task_luoyang_YanMenShiJia
            else:
                __image_city_npc: str = find_task.task_chengdu_NanGongShiJia

            print(f"当前押镖地点为 {__image_city_npc}")
            truck_npc_receive_task_address = self.windows_find.get_windows_image_rect(hwnd,
                                                                                      read_image=self._load_pic(__image_city_npc))
            if truck_npc_receive_task_address is None:
                # print(f"没有找到 {__image_city_npc}")
                continue
            else:
                """
                选择押镖目的地
                """
                SetGhostMouse().move_mouse_to(truck_npc_receive_task_address[0], truck_npc_receive_task_address[1])
                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_car_type = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_task.car_type_little))
            if truck_car_type is None:
                continue
            else:
                """
                选择镖车的车型
                """
                SetGhostMouse().move_mouse_to(truck_car_type[0], truck_car_type[1])
                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)

            truck_receive_task = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(find_task.receive_task))
            if truck_receive_task is None:
                continue
            else:
                """
                接镖
                """
                SetGhostMouse().move_mouse_to(truck_receive_task[0], truck_receive_task[1])
                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_receive_task_confirm = self.windows_find.get_windows_image_rect(hwnd,
                                                                                       read_image=self._load_pic(find_task.receive_task_confirm))
            if truck_receive_task_confirm is None:
                continue
            else:
                """
                确认接镖
                """
                SetGhostMouse().move_mouse_to(truck_receive_task_confirm[0], truck_receive_task_confirm[1])
                time.sleep(0.2)
                SetGhostMouse().click_mouse_left_button()
                break
        time.sleep(0.5)
        __find_task: TruckCarReceiveTask = self._get_pic_receive_task()
        __break_npc_talk = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__find_task.break_npc_talk))
        if __break_npc_talk is not None:
            SetGhostBoards().click_press_and_release_by_code(27)
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

            find_pic = self.windows_cap.capture(hwnd)
            find_pics = find_pic.pic_content[int(find_pic.pic_height * 0.1):int(find_pic.pic_height * 0.5),
                        int(find_pic.pic_width * 0.3):int(find_pic.pic_width * 0.7)]
            if self.ocr.find_ocr(find_pics, "距离NPC太远") is not None:
                """
                如果出现距离NPC太远了，说明开车失败了
                """
                # print("TransportTaskFunc: 出现“距离NPC太远”的提示")
                return False
            # 鼠标离镖车远一点
            pos = coordinate_change_from_windows(hwnd, (1, 1))
            SetGhostMouse().move_mouse_to(pos[0], pos[1])
            return True
        # print(f"TransportTaskFunc: 未找到镖车的 “驾车” 按钮")
        return False

    def find_truck_car_center_pos_v2(self, hwnd: int, display_area: int) -> tuple or None:
        """
        :param hwnd:
        :param display_area: 0 接镖后的查询，1：打怪后的查询
        """
        time.sleep(0.5)
        __cap = self.windows_cap.capture(hwnd)
        res_car = self.find_car_pos_in_display_v2(hwnd, __cap.pic_content)  # 拿出坐标
        if res_car is None:
            # 没有找到镖车，先顺时针旋转45度，等待下次再进来
            WindowsHandle().activate_windows(hwnd)
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(37, 0.4)
            return None
        res_center_car_bool: bool = self.find_car_in_center_display_v3(image=__cap,
                                                                       display_area=display_area)  # 检测图片是否在中间
        if res_center_car_bool is False:
            # cap = self.windows.capture(hwnd)
            __car_quadrant: int = self.check_target_pos_direction(__cap, target_pos=res_car)
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
            return None
        return coordinate_change_from_windows(hwnd, res_car)

    def check_task_status(self, hwnd: int) -> bool:
        """
        检测押镖是否已经在NPC处接了任务
        """
        return self._check_task_status(hwnd)

    """
    寻找镖车，并上车
    """

    def driver_truck_car(self, hwnd: int, map_name: str) -> bool:
        """
        寻找镖车，并上车
        :param hwnd: 句柄
        :param map_name: 地图名称，用于判断要不要走2步
        """
        if map_name in ["金陵", "洛阳", "燕京"]:
            if not self.driver_truck_car_v3(hwnd, map_name):
                return False
        if not self.transport_truck(hwnd):
            return False
        return True

    def driver_truck_car_v2(self, hwnd: int, car_area_type: int) -> bool:

        time.sleep(2)
        if self.transport_truck(hwnd):
            # 找到车了
            return True

        __res_center_pos = self.find_truck_car_center_pos_v2(hwnd, car_area_type)
        if __res_center_pos is None:
            return False
        SetGhostMouse().move_mouse_to(__res_center_pos[0], __res_center_pos[1])  # 鼠标移动到初始化位置
        time.sleep(0.5)

        for i in range(5):
            pos = SetGhostMouse().get_mouse_x_y()
            #  先下移50个像素点击一次
            SetGhostMouse().move_mouse_to(pos[0], pos[1] + 50)
            time.sleep(0.2)
            SetGhostMouse().click_mouse_left_button()
            time.sleep(0.5)

            self.break_other_truck_car(hwnd)  # 不小心点到劫镖了，就退出一下
            self.break_npc_talk(hwnd)

            if self.transport_truck(hwnd) is False:
                # 没有没有找到车辆
                continue
            return True
        return False

    def driver_truck_car_v3(self, hwnd: int, map_name: str) -> bool:
        """
        不找车，直接在地图输入坐标前往
        """

        if self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(self._get_pic_truck_car().task_star_mode)) is None:
            return False

        __map = self._get_map()

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)
        __rec_pos_x = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__map.pos_x))
        if __rec_pos_x is None:
            SetGhostBoards().click_press_and_release_by_key_name("M")
            return False
        SetGhostMouse().move_mouse_to(__rec_pos_x[0] + 50, __rec_pos_x[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.5)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(8, 0.5)
        time.sleep(0.1)

        if map_name == "燕京":
            SetGhostBoards().click_press_and_release_by_key_name("5")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("9")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("1")
        elif map_name == "洛阳":
            SetGhostBoards().click_press_and_release_by_key_name("9")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("2")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("5")
        elif map_name == "金陵":
            SetGhostBoards().click_press_and_release_by_key_name("1")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("4")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("2")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("5")

        __rec_pos_y = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__map.pos_y))
        if __rec_pos_y is None:
            return False
        SetGhostMouse().move_mouse_to(__rec_pos_y[0] + 50, __rec_pos_y[1])
        time.sleep(0.2)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.1)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(8, 0.5)
        time.sleep(0.1)

        if map_name == "燕京":
            SetGhostBoards().click_press_and_release_by_key_name("2")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("1")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("7")
        elif map_name == "洛阳":
            SetGhostBoards().click_press_and_release_by_key_name("7")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("9")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("9")
        elif map_name == "金陵":
            SetGhostBoards().click_press_and_release_by_key_name("7")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("3")
            time.sleep(0.1)
            SetGhostBoards().click_press_and_release_by_key_name("0n")

        while 1:

            __rec_pos_search = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__map.search_pos))
            if __rec_pos_search is None:
                time.sleep(1)
                continue
            SetGhostMouse().move_mouse_to(__rec_pos_search[0], __rec_pos_search[1])
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            break

        while 1:
            __rec_pos_point = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__map.result_point))
            if __rec_pos_point is None:
                time.sleep(1)
                continue
            SetGhostMouse().move_mouse_to(__rec_pos_point[0], __rec_pos_point[1])
            SetGhostMouse().click_mouse_left_button()
            time.sleep(1)
            break

        pos = coordinate_change_from_windows(hwnd, (1, 1))
        SetGhostMouse().move_mouse_to(pos[0], pos[1])

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)

        return True

    def plus_map(self, hwnd: int):
        """
        将地图的缩放放到最大
        """
        __map = self._get_map()

        SetGhostBoards().click_press_and_release_by_key_name("M")
        time.sleep(0.5)
        __rec_pos_plus = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__map.plus_map))
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
        return True

    def click_truck_car_in_display_center(self, hwnd: int):
        """
        点一下屏幕中间，让押镖的按钮出现
        """

        __cap_pic = self.windows_cap.capture(hwnd)
        __w, __h = __cap_pic.pic_width, __cap_pic.pic_height

        __center_x = int(__w * 0.5)  # 屏幕正中间
        __center_y = int(__h * 0.5)  # 屏幕正中间

        pos = coordinate_change_from_windows(hwnd, (__center_x, __center_y))
        SetGhostMouse().move_mouse_to(pos[0], pos[1])
        time.sleep(0.5)
        SetGhostMouse().click_mouse_left_button()
        time.sleep(0.5)

        pos = coordinate_change_from_windows(hwnd, (1, 1))
        SetGhostMouse().move_mouse_to(pos[0], pos[1])

        if self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(self._get_pic_truck_car().task_star_mode)) is not None:
            return True
        return False


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
        __bag: BackpackItem = self._get_bag_goods()
        __goods_bag_tag_clickable = __bag.goods_bag_tag_clickable  # 没有点击
        __goods_bag_tag_clicked = __bag.goods_bag_tag_clicked  # 已经点击

        WindowsHandle().activate_windows(hwnd)
        time.sleep(1)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
        time.sleep(1)

        __rec_goods_bag_tag_clicked = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__goods_bag_tag_clicked))
        __rec_goods_bag_tag_clickable = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__goods_bag_tag_clickable))

        __rec_bag = __rec_goods_bag_tag_clicked if __rec_goods_bag_tag_clicked is not None else __rec_goods_bag_tag_clickable if __rec_goods_bag_tag_clickable is not None else None

        if __rec_bag is not None:
            time.sleep(0.5)
            SetGhostMouse().move_mouse_to(__rec_bag[0], __rec_bag[1])
            SetGhostMouse().click_mouse_left_button()
            return True
        return False

    def use_yu_feng_shen_shui(self, hwnd):
        """
        使用御风神水
        """

        __bag: BackpackItem = self._get_bag_goods()
        __yf_goods = __bag.run_goods
        _person_buff: PersonStatusAndBuff = self._get_person_buff()
        __yf_goods_ready = _person_buff.run_goods_ready
        __yf_goods_buff = _person_buff.run_goods_buff

        pic = self.windows_cap.capture(hwnd)
        # 高度1-300像素，宽度 画面右侧，查看所有状态栏
        pic_content = pic.pic_content[1:int(pic.pic_height * 0.4), int(pic.pic_width * 0.5):int(pic.pic_width)]
        __yf_buff_status = self.windows_find.get_image_all_rect(pic_content, self._load_pic(__yf_goods_buff))
        if __yf_buff_status is not None:
            for _ss in __yf_buff_status:
                # 看看当前状态有没有御风
                if _ss[-1] > 0.7:
                    return True

        self.open_bag(hwnd)

        time.sleep(1)
        __rec_yf_goods = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__yf_goods))
        if __rec_yf_goods is not None:
            """
            如果找到了御风神水
            """
            SetGhostMouse().move_mouse_to(__rec_yf_goods[0], __rec_yf_goods[1])
            time.sleep(1)
            SetGhostMouse().click_mouse_right_button()
            for i in range(10):
                # 等待10秒
                time.sleep(1)
                __rec_yf_goods_ready = self.windows_find.get_windows_image_rect(hwnd, read_image=self._load_pic(__yf_goods_ready))

                if __rec_yf_goods_ready is not None or self.ocr.find_ocr(image=self.windows_cap.capture(hwnd).pic_content,
                                                                         temp_text="不断跑动跳跃"):
                    SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
                    return True
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(66, 0.3)
        return False
