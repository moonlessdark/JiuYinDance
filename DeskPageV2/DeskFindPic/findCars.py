
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

        def reply_perspective_target(pic_width: int, target_pos: tuple):
            """
            坐标是否在屏幕中间的位置
            """
            center_x: int = int(pic_width / 2)
            if abs(center_x - target_pos[0]) < 500:
                # 如果坐标和游戏窗口中间的误差在40个像素内，就算通过
                return True
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
                if reply_perspective_target(im.pic_width, rec):
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
            if cos is not None:
                driver_res = coordinate_change_from_windows(hwnd, cos)
                print(f"find car type {driver_res[0]}x{driver_res[1]}")
                return driver_res
            return None

        def check_driver_type_select():
            """
            看看选中类型的按钮出没出现
            """

            car_type = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.task_flags_yellow_car)
            if car_type is not None:
                print(f" 黄旗 {find_task.task_flags_yellow_car}")
                return True
            return False
        while 1:
            while 1:
                time.sleep(1)
                if check_car_status() is False:
                    return False

                """
                看看镖车是不是在屏幕中间
                """
                rec: list = self.__find_car_flag(hwnd)
                if rec is not None:
                    SetGhostMouse().move_mouse_to(rec[0], rec[1])  # 鼠标移动到初始化位置
                    time.sleep(1)
                    #  先点击一次
                    SetGhostMouse().move_mouse_to(rec[0], rec[1] + 50)
                    time.sleep(1)
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(2)
                    while 1:

                        task_car_selected = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.task_car_selected)
                        time.sleep(1)
                        if task_car_selected is None:
                            """
                            如果还是没有出现镖车已经选中成功的标志，就继续往下点击
                            """
                            pos_x, pos_y = SetGhostMouse().get_mouse_x_y()
                            SetGhostMouse().move_mouse_to(pos_x, pos_y + 50)
                            time.sleep(1)
                            SetGhostMouse().click_mouse_left_button()  # 尝试每隔50个像素就点击一次，看看能不能出现车辆被选中的效果
                            time.sleep(2)
                            if check_driver_type_select() is not None:
                                """
                                如果选择了车辆后立即出现了选择 驾车方式 的图标，那么为了避免点击右键失效，先关闭此窗口
                                """
                                print("sss")
                                SetGhostBoards().click_press_and_release_by_code(27)
                                time.sleep(1)
                        else:
                            """
                            如果成功选中了镖车，那么就点击一下鼠标右键，让人物主动靠近
                            """
                            print("car selected")
                            while 1:
                                SetGhostMouse().click_mouse_right_button()
                                print("wait person move")
                                time.sleep(5)  # 让角色走5秒
                                task_star_mode = self.windows.find_windows_coordinate_rect(handle=hwnd, img=find_task.task_star_mode)
                                task_star_mode2 = check_driver_type()
                                if task_star_mode is not None:
                                    print("find truck type")
                                    SetGhostMouse().move_mouse_to(task_star_mode[0], task_star_mode[1])
                                    time.sleep(1)
                                    SetGhostMouse().click_mouse_left_button()
                                    print("Go")
                                    return True
                                elif task_star_mode2 is not None:
                                    print("find truck type 2")
                                    SetGhostMouse().move_mouse_to(task_star_mode2[0], task_star_mode2[1])
                                    time.sleep(1)
                                    SetGhostMouse().click_mouse_left_button()
                                    print("Go2")
                                    return True




if __name__ == '__main__':
    ctypes.windll.shcore.SetProcessDpiAwareness(False)
