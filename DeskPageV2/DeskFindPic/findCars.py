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
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, PicCapture, find_area
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
    def reply_perspective(hwnd):
        """
        恢复角色视角
        """
        WindowsHandle().activate_windows(hwnd)
        SetGhostBoards().click_press_by_code(38)
        time.sleep(3)
        SetGhostBoards().release_by_code(38)
        for i in range(10):
            SetGhostBoards().click_press_and_release_by_code(40)
        SetGhostBoards().click_press_and_release_by_key_name("w")

    def __find_car_flag(self, hwnd):
        """
        查询小车在哪
        """

        def reply_perspective_target_is_center(pic_width, pic_height,  target_pos: tuple):
            """
            坐标是否在屏幕中间的位置
            """
            center_x: int = int(pic_width / 2)
            center_y: int = int(pic_height * 0.45)
            if abs(target_pos[0] < center_x) < 100 and target_pos[1] < center_y:
                """
                如果镖车的文字处于窗口的上半部分和在中间的100的像素附近
                """
                return True
            print(f"镖车的误差为：{abs(target_pos[0] < center_x)}")
            return False

        while 1:
            SetGhostBoards().click_press_and_release_by_code(37)  # 视角左转一下
            time.sleep(1)
            im = self.windows.capture(hwnd)
            rec = self.ocr.find_ocr(im.pic_content, "的镖车")

            if rec is not None:
                """
                找到车了，把视角转到这个车
                """
                if reply_perspective_target_is_center(im.pic_width, im.pic_height,  rec):
                    return coordinate_change_from_windows(hwnd, rec)
            continue
        return None

    def create_team(self, hwnd):
        """
        创建队伍
        """
        find_team: Team = self.__get_pic_team()
        flag_status = find_team.flag_team_status
        while 1:
            rec = self.windows.find_windows_coordinate_rect(hwnd, img=self.__load_pic(flag_status))
            print("查询队伍ing")
            if rec is None:
                """
                说明没有队伍，需要创建一下
                """
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

    def find_truck_task_npc(self, hwnd):
        """
        打开勤修
        """
        WindowsHandle().activate_windows(hwnd)
        find_npc: FindTruckCarTaskNPC = self.__get_pic_find_task_npc()
        while 1:
            print("查询勤修图标")
            time.sleep(1)
            qin_xiu_rec = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_npc.qin_xiu)
            if qin_xiu_rec is None:
                continue
            else:
                """
                找到了勤修图标
                """
                print(f"查询勤修图标 {qin_xiu_rec[0]} x {qin_xiu_rec[1]}")
                SetGhostMouse().move_mouse_to(qin_xiu_rec[0], qin_xiu_rec[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            qin_xiu_activity_list = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                              img=find_npc.qin_xiu_activity_list)
            if qin_xiu_activity_list is None:
                continue
            else:
                """
                找到活动列表
                """
                SetGhostMouse().move_mouse_to(qin_xiu_activity_list[0], qin_xiu_activity_list[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            qin_xiu_truck_task = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                           img=find_npc.qin_xiu_truck_car_task)
            if qin_xiu_truck_task is None:
                continue
            else:
                """
                找到了每日运镖图标
                """
                SetGhostMouse().move_mouse_to(qin_xiu_truck_task[0], qin_xiu_truck_task[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            qin_xiu_truck_point = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                            img=find_npc.task_point_yanjing)
            if qin_xiu_truck_point is None:
                continue
            else:
                """
                找到了成都
                """
                SetGhostMouse().move_mouse_to(qin_xiu_truck_point[0], qin_xiu_truck_point[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break

        while 1:
            time.sleep(1)
            qin_xiu_truck_point_npc = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                img=find_npc.task_point_yanjing_npc)
            if qin_xiu_truck_point_npc is None:
                continue
            else:
                """
                找到了成都NPC
                """
                SetGhostMouse().move_mouse_to(qin_xiu_truck_point_npc[0], qin_xiu_truck_point_npc[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                SetGhostBoards().click_press_and_release_by_code(27)
                break
        return True

    def receive_task(self, hwnd):
        """
        接取任务
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
                SetGhostMouse().move_mouse_to(truck_npc_receive_task_talk[0], truck_npc_receive_task_talk[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_npc_receive_task_address = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                       img=find_task.task_yanjing_JunMaChang)
            if truck_npc_receive_task_address is None:
                continue
            else:
                """
                选择押镖目的地
                """
                SetGhostMouse().move_mouse_to(truck_npc_receive_task_address[0], truck_npc_receive_task_address[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_car_type = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.car_type_little)
            if truck_npc_receive_task_talk is None:
                continue
            else:
                """
                选择镖车的车型
                """
                SetGhostMouse().move_mouse_to(truck_car_type[0], truck_car_type[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_receive_task = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.receive_task)
            if truck_npc_receive_task_talk is None:
                continue
            else:
                """
                接镖
                """
                SetGhostMouse().move_mouse_to(truck_receive_task[0], truck_receive_task[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        while 1:
            time.sleep(1)
            truck_receive_task_confirm = self.windows.find_windows_coordinate_rect(handle=hwnd,
                                                                                   img=find_task.receive_task_confirm)
            if truck_npc_receive_task_talk is None:
                continue
            else:
                """
                确认接镖
                """
                SetGhostMouse().move_mouse_to(truck_receive_task_confirm[0], truck_receive_task_confirm[1])
                time.sleep(1)
                SetGhostMouse().click_mouse_left_button()
                break
        return True

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

        def check_car_status():

            time.sleep(3)
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
                return False
            else:
                return True

        def check_driver_type():
            """
            检查 驾车方式 是否存在
            """
            __img_car = self.windows.capture(hwnd)
            cos = self.ocr.find_ocr(__img_car.pic_content, "驾车")
            cos2 = self.windows.find_windows_coordinate_rect(hwnd, find_task.task_star_mode)
            if cos is not None:
                driver_res = coordinate_change_from_windows(hwnd, cos)
                print(f"find car type {driver_res[0]},{driver_res[1]}")
                return driver_res
            elif cos2 is not None:
                print(f"find car type {cos2[0]},{cos2[1]}")
                return cos2
            return None

        def check_driver_type_select():
            """
            看看选中类型的按钮出没出现
            """

            car_type = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.task_flags_yellow_car)
            if car_type is not None:
                return True
            return False

        def check_task_end():
            """
            检测押镖是否结束
            """
            if len(self.ocr.find_ocr_arbitrarily(self.windows.capture(hwnd).pic_content,
                                                 ["帮会获得运镖积分", "获得帮派贡献度"])) > 0:
                return True
            return False

        def go_truck(hwnd):
            f_rec: list = self.__find_car_flag(hwnd)
            if f_rec is not None:
                """
                镖车在屏幕中间的位置
                """
                SetGhostMouse().move_mouse_to(f_rec[0], f_rec[1])  # 鼠标移动到初始化位置
                time.sleep(1)

                while 1:

                    pos_x, pos_y = SetGhostMouse().get_mouse_x_y()

                    #  先点击一次
                    SetGhostMouse().move_mouse_to(pos_x, pos_y + 50)

                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(3)
                    ress = check_driver_type()
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

            while 1:

                # 获取一下当前坐标，从右上角获取
                pos_old: int = self.ocr.get_person_pos(self.windows.capture(hwnd).pic_content)
                print(f"当前坐标：{pos_old}")
                print("接镖成功后,尝试直接运镖")
                rec = check_driver_type()
                if rec is not None:
                    SetGhostMouse().move_mouse_to(rec[0], rec[1])
                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.5)
                    print("尝试点击 驾车 按钮")

                    # 截图一下图片区域，只拿上半部分区域(避免读取到右下角的日志)，因为这里只是用于判断，拿到的坐标没有其他用途
                    img = self.windows.capture(hwnd)
                    img = img.pic_content[int(img.pic_height * 0.2):int(img.pic_height * 0.6),
                          int(img.pic_width * 0.4):int(img.pic_width * 0.6)]
                    for i in range(5):
                        """
                        循环5秒，看看这个提示是否存在
                        """
                        pos_new: int = self.ocr.get_person_pos(self.windows.capture(hwnd).pic_content)
                        print(f"当前新坐标：{pos_new}")
                        if self.ocr.find_ocr(image=img, temp_text="你距离NPC太远了") is not None or pos_old == pos_new:
                            print("直接运镖失败，距离镖车太远，开始尝试找车")
                            go_truck(hwnd)
                        else:
                            break
                    print("进行了5次循环")
                else:
                    go_truck(hwnd)
                return True

            #
            #
            #
            # rec: list = self.__find_car_flag(hwnd)
            # if rec is not None:
            #     """
            #     看看镖车是不是在屏幕中间
            #     """
            #     SetGhostMouse().move_mouse_to(rec[0], rec[1])  # 鼠标移动到初始化位置
            #     time.sleep(1)
            #     #  先点击一次
            #     SetGhostMouse().move_mouse_to(rec[0], rec[1] + 50)
            #     time.sleep(1)
            #     SetGhostMouse().click_mouse_left_button()
            #     time.sleep(2)
            #
            #     # 寻找并点击镖车
            #     while 1:
            #
            #         if self.fight_monster(hwnd):
            #             # 看看怪物是否出现,如果打怪结束就跳出循环，重新寻找车辆并驾车
            #             break
            #
            #         task_car_selected = self.windows.find_windows_coordinate_rect(handle=hwnd,
            #                                                                       img=find_task.task_car_selected)
            #         time.sleep(1)
            #         if task_car_selected is None:
            #             """
            #             如果还是没有出现镖车已经选中成功的标志，就继续往下点击
            #             """
            #             pos_x, pos_y = SetGhostMouse().get_mouse_x_y()
            #             SetGhostMouse().move_mouse_to(pos_x, pos_y + 50)
            #             time.sleep(1)
            #             SetGhostMouse().click_mouse_left_button()  # 尝试每隔50个像素就点击一次，看看能不能出现车辆被选中的效果
            #             time.sleep(1)
            #         else:
            #
            #             if self.fight_monster(hwnd):
            #                 # 看看怪物是否出现,如果打怪结束就跳出循环，重新寻找车辆并驾车
            #                 break
            #
            #             if check_driver_type_select() is True:
            #                 print(
            #                     "如果点击了车辆后立即出现了选择 驾车方式 的图标，那么为了避免点击右键失效，先关闭此窗口(此时说明车辆很近，但是不一定能立即驾车)")
            #                 SetGhostBoards().click_press_and_release_by_code(27)
            #                 time.sleep(1)
            #
            #             """
            #             如果成功选中了镖车，那么就点击一下鼠标右键，让人物主动靠近
            #             """
            #             print("镖车已经选中")
            #             SetGhostMouse().click_mouse_right_button()
            #
            #             print("让角色走5秒")
            #             time.sleep(5)
            #
            #             # 选中驾车模式，开始押镖
            #             while 1:
            #
            #                 if self.fight_monster(hwnd):
            #                     # 看看怪物是否出现,如果打怪结束就跳出循环，重新寻找车辆并驾车
            #                     break
            #                 task_star_mode = self.windows.find_windows_coordinate_rect(handle=hwnd,
            #                                                                            img=find_task.task_star_mode)
            #                 task_star_mode2 = check_driver_type()
            #                 if task_star_mode is not None:
            #                     print("find truck type")
            #                     SetGhostMouse().move_mouse_to(task_star_mode[0], task_star_mode[1])
            #                     time.sleep(1)
            #                     SetGhostMouse().click_mouse_left_button()
            #                     print("出发，开始驾车1")
            #                     break
            #                 elif task_star_mode2 is not None:
            #                     print("find truck type 2")
            #                     SetGhostMouse().move_mouse_to(task_star_mode2[0], task_star_mode2[1])
            #                     time.sleep(1)
            #                     SetGhostMouse().click_mouse_left_button()
            #                     print("出发，开始驾车2")
            #                     break
            #             break


if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(False)
