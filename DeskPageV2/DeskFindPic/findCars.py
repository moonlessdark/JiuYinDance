# encoding = utf-8
import ctypes
import time

import cv2
import numpy as np
from numpy import fromfile

from DeskPageV2.DeskTools.GhostSoft.get_driver_v3 import SetGhostBoards, SetGhostMouse
from DeskPageV2.DeskTools.WindowsSoft.MonitorDisplay import coordinate_change_from_windows, display_windows_detection
from DeskPageV2.DeskTools.WindowsSoft.WindowsCapture import WindowsCapture
from DeskPageV2.DeskTools.WindowsSoft.WindowsHandle import WindowsHandle
from DeskPageV2.DeskTools.WindowsSoft.findOcr import FindPicOCR
from DeskPageV2.DeskTools.WindowsSoft.get_windows import PicCapture
from DeskPageV2.Utils.dataClass import FindTruckCarTaskNPC, Team, TruckCarPic, TruckCarReceiveTask
from DeskPageV2.Utils.load_res import GetConfig


class TruckCar:
    def __init__(self):
        self.__config = GetConfig()
        self.__find_task_npc = None  # 查询任务NPC
        self.__find_team = None  # 查询队伍是否创建
        self.__receive_task = None  # 接取押镖任务
        self.__receive_task_road = None  # 运镖路上...

        self.windows = WindowsCapture()
        self.ocr = FindPicOCR()

        self.hwnd: int = 0
        _, self.__area_map, self.__person_name = self.ocr.get_person_map(self.windows.capture(self.hwnd).pic_content)


    @staticmethod
    def __load_pic(pic_dir: str):
        """
        加载一下图片
        """
        return cv2.imdecode(fromfile(pic_dir, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def __get_pic_find_task_npc(self) -> FindTruckCarTaskNPC:
        """
        获取查找地图的运镖NPC
        """
        if self.__find_task_npc is None:
            self.__find_task_npc = self.__config.find_track_car_task()
        return self.__find_task_npc

    def __get_pic_team(self) -> Team():
        """
        检查队伍是否创建
        """
        if self.__find_team is None:
            self.__find_team = self.__config.get_team()
        return self.__find_team

    def __get_pic_receive_task(self) -> TruckCarReceiveTask:
        """
        接取任务和押镖的路上
        """
        if self.__receive_task is None:
            self.__receive_task = self.__config.get_track_car()
        return self.__receive_task

    def __get_pic_truck_car(self):
        """
        开始押镖了
        """
        if self.__receive_task_road is None:
            self.__receive_task_road = self.__config.truck_task()
        return self.__receive_task_road

    @staticmethod
    def _reply_person_perspective(hwnd):
        """
        恢复角色视角
        """
        WindowsHandle().activate_windows(hwnd)
        SetGhostBoards().click_press_and_release_by_key_code_hold_time(40, 3)
        for ii in range(3):
            SetGhostBoards().click_press_and_release_by_key_code_hold_time(38, 0.2)
            time.sleep(0.2)
        SetGhostBoards().click_press_and_release_by_key_name("w")
        time.sleep(0.5)
        SetGhostMouse().move_mouse_wheel(-10)

    @staticmethod
    def _check_target_pos_is_center(img: PicCapture, target_pos: tuple) -> bool:
        """
        检查传入的坐标是否是在屏幕中间的区域
        """
        __img = img
        __w, __h = __img.pic_width, __img.pic_height
        if int(__w * 0.2) < target_pos[0] < int(__w * 0.8) and target_pos[1] < int(__h * 0.5):
            """
            如果目标在屏幕的上半区域
            """
            print("镖车处于屏幕的上半区域，符合要求")
            return True
        else:
            print("镖车所处的坐标不符合要求")
            return True

    def _check_task_status(self) -> bool:
        """
        检测是否接取了任务。
        任务栏的押镖小旗子
        """
        time.sleep(1)
        find_task: TruckCarPic = self.__get_pic_truck_car()
        task_flag_status = self.windows.find_windows_coordinate_rect(handle=self.hwnd,
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
            print("未找到押镖状态")
            return False
        return True

    def _check_task_end(self) -> bool:
        """
        检测押镖是否结束
        """
        if len(self.ocr.find_ocr_arbitrarily(self.windows.capture(self.hwnd).pic_content,
                                             ["帮会获得运镖积分", "获得帮派贡献度"])) > 0:
            print("DriverTruckCarFuc: 运镖结束")
            return True
        return False

    def _check_person_move_status(self, old_pos: int):
        """
        游戏人物是否在移动
        :param old_pos: 旧地图坐标
        """
        pos, _, _ = self.ocr.get_person_map(self.windows.capture(self.hwnd).pic_content)
        if old_pos == pos:
            return False
        return True

    def _check_transport_truck_status(self, hwnd: int, old_pos: int):
        """
        检查点击了开始 驾车 后，出现了距离太远 或者 当前人物的坐标没有更新.
        如果坐标更新了，那就说明正式开始运镖了
        """
        img = self.windows.capture(hwnd)
        new_pic = img.pic_content[int(img.pic_height * 0.2):int(img.pic_height * 0.6),
                  int(img.pic_width * 0.4):int(img.pic_width * 0.6)]
        cc = self.ocr.find_ocr(image=new_pic, temp_text="你距离NPC太远了")
        if cc is not None:
            return False
        elif self._check_person_move_status(old_pos) is False:
            return False
        return True

    def _find_driver_truck_type(self, hwnd: int):
        """
        检查 运镖(驾车) 按钮
        """
        __hwnd: int = hwnd
        __img_car = self.windows.capture(__hwnd)
        find_task: TruckCarPic = self.__get_pic_truck_car()
        cos = self.ocr.find_ocr(__img_car.pic_content, "驾车")
        cos2 = self.windows.find_windows_coordinate_rect(__hwnd, find_task.task_star_mode)
        if cos is not None:
            driver_res = coordinate_change_from_windows(__hwnd, cos)
            print(f"DriverTruckCarFuc: 发现了 运镖(驾车) 文字({driver_res[0]},{driver_res[1]})")
            return driver_res
        elif cos2 is not None:
            print(f"DriverTruckCarFuc: 发现了 运镖(驾车) 图标({cos2[0]},{cos2[1]})")
            return cos2
        return None

    def _find_car_pos(self, hwnd: int):
        """
        查询小车在哪
        """
        SetGhostBoards().click_press_and_release_by_code(37)  # 视角左转一下
        time.sleep(1)
        im = self.windows.capture(hwnd)
        rec = self.ocr.find_ocr(im.pic_content, f"{self.__person_name}的镖车")
        if rec is not None:
            """
            找到车了，把视角转到这个车
            """
            if self._check_target_pos_is_center(im, rec):
                return coordinate_change_from_windows(hwnd, rec)
        return None

    def fight_monster(self, hwnd):
        """
        运镖打怪
        """

        WindowsHandle().activate_windows(hwnd)
        find_task: TruckCarPic = self.__get_pic_truck_car()

        def check_fight_status():
            """
            检查是否进入了战斗状态。
            避免识别场景过于复杂，在这里进行多重检测
            """

            if len(self.ocr.find_ocr_arbitrarily(self.windows.capture(hwnd).pic_content,
                                                 ["您正在观看风景时", "忽然一道身影一闪而过",
                                                  "马受到惊吓，停滞不前"])) > 0:
                """
                方法1：如果出现了文字 “马受到惊吓，停滞不前” 出现在屏幕上，那么说明即将出现劫镖的怪
                """
                return True
            elif self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.task_monster_fight) is not None:
                """
                方法2: 如果出现了 进入战斗的文字(这里使用的是图片)，那么就说明进入战斗了，可能是劫镖的NPC，也可能是其他
                """
                return True
            return False

        def check_monster_npc_status():
            """
            检测劫镖的NPC是否出现
            """
            fight_tag_list: list = find_task.task_monster_target
            for target in fight_tag_list:
                task_monster_fight = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                               img=target)
                if task_monster_fight is not None:
                    return True
            return False

        def fight():
            """
            打怪，这里是自定义的按钮
            """
            SetGhostMouse().press_mouse_right_button()  # 按住格挡
            time.sleep(0.5)
            while 1:
                SetGhostBoards().click_press_and_release_by_code(81)
                time.sleep(2)
                if len(self.ocr.find_ocr_arbitrarily(self.windows.capture(hwnd).pic_content,
                                                     ["成功攻克劫匪", "完成此次运镖后将额外获得"])) > 0:
                    """
                    如果出现了把怪打死的文字
                    """
                    break
                elif check_monster_npc_status() is False:
                    """
                    如果怪消失了
                    """
                    break
            SetGhostMouse().release_mouse_right_button()  # 放开格挡
            return True

        time.sleep(0.5)
        if check_fight_status():
            """
            如果进入了战斗状态
            """
            while 1:
                if check_monster_npc_status():
                    # 如果怪物出现了
                    if fight():
                        # 如果打怪结束
                        return True
        return False

    def driver_car(self, hwnd):
        """
        开车
        """
        WindowsHandle().activate_windows(hwnd)
        find_task: TruckCarPic = self.__get_pic_truck_car()
        _, area, person = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)

        is_go: bool = False






        def go_truck():
            f_rec: list = self._find_car_pos(hwnd, person)
            if f_rec is not None:
                """
                镖车在屏幕中间的位置
                """
                SetGhostMouse().move_mouse_to(f_rec[0], f_rec[1])  # 鼠标移动到初始化位置
                time.sleep(1)

                while 1:

                    self.fight_monster(hwnd)

                    pos_x, pos_y = SetGhostMouse().get_mouse_x_y()

                    #  先点击一次
                    SetGhostMouse().move_mouse_to(pos_x, pos_y + 50)

                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(3)
                    ress = self._check_driver_type()
                    if ress is not None:
                        """
                        如果已经成功选中车辆
                        """
                        print("找到运镖窗口了")
                        SetGhostBoards().click_press_and_release_by_code(27)
                        time.sleep(1)
                        SetGhostMouse().click_mouse_right_button()
                        time.sleep(1)
                        ress = check_driver_type()
                        if ress is not None:
                            """
                            如果已经选中了
                            """
                            SetGhostBoards().click_press_and_release_by_key_name_hold_time("w",
                                                                                           0.5)  # 往前走一步
                            print("往前走一步")
                        # 点击右键有看看运镖的按钮有没有出现
                        if ress is not None:
                            print("找到车后，等待5秒，等待任务自动往镖车走过去")
                            time.sleep(1)
                            SetGhostMouse().move_mouse_to(ress[0], ress[1])
                            time.sleep(1)
                            SetGhostMouse().click_mouse_left_button()  # 点击一下 驾车 按钮
                            print("尝试再次点击 驾车 按钮")
                            return True



        while 1:
            """
            开始正式押镖了.
            押镖逻辑如下：
            1、接取了任务后，此时会弹出 “驾车” 选项。点击确定，如果成功上车，就开始判断是否出现了劫镖的怪。并进行打怪
            2、如果没有成功上车，就开始找车。
            
            
            if 点击"驾车" 出现 “距离NPC太远”:
                while:
                    开始旋转游戏画面，开始找车，车在屏幕正中间
                    if "找到车"，往前走一步 点击驾车，出现 “距离NPC太远”:
                        continue
                    else:
                        break   
            等待怪的出现，并打怪 
            
            """
            time.sleep(1)
            if check_car_status() is False:
                # 如果没有检测到接镖成功的图标
                print("未在任务栏检测到运镖的图标...")
                continue

            if check_task_end() is True:
                print("运镖结束了")
                return True

            self.fight_monster(hwnd)

            if is_go:
                continue

            while 1:

                print("接镖成功后,尝试直接运镖")
                rec = check_driver_type()
                if rec is not None:

                    self.fight_monster(hwnd)

                    pos_old, _, _ = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)
                    print(f"当前坐标：{pos_old}")
                    SetGhostMouse().move_mouse_to(rec[0], rec[1])
                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.5)
                    print("尝试点击 驾车 按钮")

                    for i in range(5):
                        """
                        循环5秒，看看这个提示是否存在
                        """

                        if self.fight_monster(hwnd):
                            break

                        time.sleep(1)

                        # 截图一下图片区域，只拿上半部分区域(避免读取到右下角的日志)，因为这里只是用于判断，拿到的坐标没有其他用途
                        img = self.windows.capture(hwnd)
                        new_pic = img.pic_content[int(img.pic_height * 0.2):int(img.pic_height * 0.6),
                                  int(img.pic_width * 0.4):int(img.pic_width * 0.6)]

                        cc = self.ocr.find_ocr(image=new_pic, temp_text="你距离NPC太远了")

                        if cc is not None:
                            print("出现了距离太远的文字，无法直接直接押镖")
                            go_truck()
                            is_go = True
                            break

                        elif _check_person_move_status(old_pos=pos_old) is False:
                            print("直接运镖失败，坐标没有移动，开始尝试找车")
                            go_truck()
                            is_go = True
                            break
                        else:
                            is_go = True
                            break
                    print("进行了5次循环")
                    break
                else:
                    go_truck()
                    is_go = True
                    break


class TeamFunc(TruckCar):

    def __init__(self):
        super().__init__()

    def create_team(self, hwnd, work_status: bool = True):
        """
        创建队伍
        """
        find_team: Team = self.__get_pic_team()
        flag_status = find_team.flag_team_status
        while 1:

            if work_status is False:
                """
                停止任务
                """
                return False

            rec = self.windows.find_windows_coordinate_rect(hwnd, img=self.__load_pic(flag_status))
            if rec is None:
                """
                说明没有队伍，需要创建一下
                """
                print("未检测到队伍，进行创建")
                WindowsHandle().activate_windows(hwnd)
                time.sleep(0.2)
                SetGhostBoards().click_press_and_release_by_key_name("o")
                time.sleep(1)
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
        通过队伍成员
        """
        pass

    def close_team(self):
        """
        解散队伍
        """
        pass


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
        find_npc: FindTruckCarTaskNPC = self.__get_pic_find_task_npc()
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
                print(f"FindTaskNpc: 找到 勤修 图标({qin_xiu_rec[0]},{qin_xiu_rec[1]})")
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
                print(f"FindTaskNpc: 找到 活动列表 图标({qin_xiu_activity_list[0]},{qin_xiu_activity_list[1]})")
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
                print(f"FindTaskNpc: 找到 每日运镖 图标({qin_xiu_truck_task[0]},{qin_xiu_truck_task[1]})")
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

            if self.__area_map == "成都":
                __image_city: str = find_npc.task_point_chengdu
            elif self.__area_map == "燕京":
                __image_city: str = find_npc.task_point_yanjing
            elif self.__area_map == "金陵":
                __image_city: str = find_npc.task_point_jinling
            elif self.__area_map == "苏州":
                __image_city: str = find_npc.task_point_suzhou
            else:
                __image_city: str = find_npc.task_point_chengdu
            qin_xiu_truck_point = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                            img=__image_city)
            if qin_xiu_truck_point is None:
                continue
            else:
                """
                找到了成都
                """
                print(f"FindTaskNpc: 找到 {self.__area_map} 图标({qin_xiu_truck_point[0]},{qin_xiu_truck_point[1]})")
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

            if self.__area_map == "成都":
                __image_city_npc: str = find_npc.task_point_chengdu_npc
            elif self.__area_map == "燕京":
                __image_city_npc: str = find_npc.task_point_yanjing_npc
            elif self.__area_map == "金陵":
                __image_city_npc: str = find_npc.task_point_jinling_npc
            elif self.__area_map == "苏州":
                __image_city_npc: str = find_npc.task_point_suzhou_npc
            else:
                __image_city_npc: str = find_npc.task_point_chengdu_npc
            qin_xiu_truck_point_npc = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                img=__image_city_npc)
            if qin_xiu_truck_point_npc is None:
                continue
            else:
                """
                找到了成都NPC
                """
                print(f"FindTaskNpc: 找到 {self.__area_map} 的NPC图标({qin_xiu_truck_point_npc[0]},{qin_xiu_truck_point_npc[1]})")
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
        find_task: TruckCarReceiveTask = self.__get_pic_receive_task()
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
                print(f"ReceiveTruckTask: 已经找到 接取任务的NPC 图标({truck_npc_receive_task_talk[0]},{truck_npc_receive_task_talk[1]})")

                SetGhostMouse().move_mouse_to(truck_npc_receive_task_talk[0], truck_npc_receive_task_talk[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)

            if self.__area_map == "成都":
                __image_city_npc: str = find_task.task_chengdu_NanGongShiJia
            elif self.__area_map == "燕京":
                __image_city_npc: str = find_task.task_yanjing_JunMaChang
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
                print(f"ReceiveTruckTask: 已经找到 目的地 图标({truck_npc_receive_task_address[0]},{truck_npc_receive_task_address[1]})")

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
                print(f"ReceiveTruckTask: 已经找到 镖车车型 图标({truck_car_type[0]},{truck_car_type[1]})")

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
                print(f"ReceiveTruckTask: 已经找到 接镖 图标({truck_receive_task[0]},{truck_receive_task[1]})")

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
                print(f"ReceiveTruckTask: 已经找到 确认接镖 图标({truck_receive_task_confirm[0]},{truck_receive_task_confirm[1]})")

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

    def transport_truck(self, hwnd: int):
        """
        开始运镖
        """
        transport_pos = self._find_driver_truck_type(hwnd)
        if transport_pos is not None:
            print(f"TransportTaskFunc: 找到了 镖车(驾车) 的坐标({transport_pos[0]},{transport_pos[1]})")
            SetGhostMouse().move_mouse_to(transport_pos[0], transport_pos[1])
            time.sleep(0.5)
            SetGhostMouse().click_mouse_left_button()

            if self.check_person_move_status(hwnd, check_wait_time=2):
                # 等待2秒，看看坐标有没有更新
                print(f"TransportTaskFunc: 成功开始运镖，注意 劫匪NPC 刷新)")
                return True
        return False

    def find_driver_truck_type(self, hwnd: int):
        """
        查询 驾车 按钮有没有出现
        """
        return self._find_driver_truck_type(hwnd)

    def find_car_pos(self, hwnd: int):
        """
        查找镖车的坐标
        """
        return self._find_car_pos(hwnd)

    def check_task_status(self) -> bool:
        """
        检测押镖是否已经在NPC处接了任务
        """
        if self._check_task_status():
            return True
        return False

    def check_task_end(self) -> bool:
        """
        检测押镖是否结束
        """
        if self._check_task_end():
            return True
        return False

    def check_person_move_status(self, hwnd: int, check_wait_time: float):
        """
        检测指定时间的前后，地图坐标是否有更新
        """
        pos, _, _ = self.ocr.get_person_map(self.windows.capture(hwnd).pic_content)
        time.sleep(check_wait_time)
        if self._check_person_move_status(pos) is False:
            return False
        return True
