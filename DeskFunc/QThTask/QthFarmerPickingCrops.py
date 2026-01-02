# coding: utf-8
import time

from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex

from DeskFunc.TaskBussinese.findFarmerPlanting import FindFarmerPlanting
from Utils.FindWindowsImage import WindowsHandle, WindowsCapture
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse


class FarmerPickingCropsQth(QThread):
    """
    农夫种植
    """
    sin_out = Signal(str)
    status_bar = Signal(int)
    sin_run_status = Signal(bool)  # 线程执行状态

    def __init__(self):
        super().__init__()

        self.working = True
        self.cond = QWaitCondition()

        self.windows_opt = WindowsHandle()
        self.windows_cap = WindowsCapture()
        self.mutex = QMutex()
        self.windows_handle = 0
        self.scan_product_num = 0

        self.find_farmer = FindFarmerPlanting()
        self.mouse = SetGhostMouse()

    def __del__(self):
        # 线程状态改为和线程终止
        # self.wait()
        self.working = False

    def stop_execute_init(self):
        """
        线程暂停,所有参数重置为null
        :return:
        """
        self.working = False

    def get_param(self, windows_handle: int, scan_product_num):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.windows_handle = windows_handle
        self.scan_product_num = scan_product_num

    def mouse_move_to_center(self, hwnd: int) -> bool:
        pic = self.windows_cap.capture(hwnd)
        if pic is None:
            return False
        pos_content: tuple = (int(pic.pic_width / 2), int(pic.pic_height / 2))
        center_pos_in_screen: tuple = coordinate_change_from_windows(hwnd, pos_content)
        SetGhostMouse().move_mouse_to(center_pos_in_screen[0], center_pos_in_screen[1])
        return True

    def step_1(self) -> bool:
        """
        第一步: 种植农作物
        """

        _execute_code: int = 0

        self.sin_out.emit("正在等待农作物可种植")
        if not self.find_farmer.find_seed_and_use(self.windows_handle):
            self.sin_out.emit("使用种子失败,请人工检查一下")
            time.sleep(1)
            return False
        while 1:

            if not self.working:
                return False

            if not self.find_farmer.find_open_loading(self.windows_handle):
                if _execute_code == 1:
                    self.sin_out.emit("农作物已种植,等待施肥")
                    time.sleep(1)
                    return True
                # self.sin_out.emit("未找到种植进度条,请人工检查一下")
                time.sleep(1)
            else:
                # self.sin_out.emit("农作物种植中...")
                _execute_code = 1

    def step_2(self, crops_pos: tuple) -> bool:
        """
        第二步: 查询农作物位置
        """
        _is_find_crops: bool = False

        if crops_pos == (-1, -1):
            # 表示默认值，需要找一下
            if not self.mouse_move_to_center(self.windows_handle):
                self.sin_out.emit("鼠标移动到屏幕中心失败,请人工检查一下")
                return  _is_find_crops
        else:
            SetGhostMouse().move_mouse_to(crops_pos[0], crops_pos[1])
        self.sin_out.emit("正在寻找农作物位置...")
        for x in range(5):
            if not self.working:
                return False
            time.sleep(0.5)
            if not self.find_farmer.find_crops_pos(self.windows_handle):
                self.sin_out.emit("屏幕正中间未找到农作物,鼠标上移20个像素")
                x, y = SetGhostMouse().get_mouse_x_y()
                SetGhostMouse().move_mouse_to(x, y - 20)
            else:
                _is_find_crops = True
        if not _is_find_crops:
            self.sin_out.emit("未找到农作物位置,请人工检查一下")
        else:
            self.sin_out.emit("农作物位置已找到")
        return _is_find_crops

    def step_3(self):
        """
        第三步: 给农作物施肥
        """
        _use_num: int = 0  # 肥料释放次数，3次和6次的时候检查一下是不是成熟了
        while 1:
            if not self.find_farmer.find_fertilizer_and_use(self.windows_handle):
                self.sin_out.emit("肥料用完了，请补充...")
                return  False
            _use_num += 1
            self.sin_out.emit(f"使用了{_use_num}次肥料")
            _loading_status_code: int = 0  # 初始化，未加载
            # 把鼠标移走，避免干扰
            _f_x, _f_y = coordinate_change_from_windows(self.windows_handle, (5, 5))
            SetGhostMouse().move_mouse_to(_f_x, _f_y)
            while 1:

                if not self.working:
                    break

                if not self.find_farmer.find_open_loading(self.windows_handle):
                    if _loading_status_code == 1:
                        # 为没有找到进度条，但是上一个状态是加载中，那么就表示已经加载了
                        time.sleep(1)
                        if self.find_farmer.find_crops_mature(self.windows_handle):
                            return True
                        else:
                            # 完了一次施肥，但是还没有成熟，需要继续施肥
                            # self.sin_out.emit(f"完了{_use_num}次施肥，但是还没有成熟，需要继续施肥")
                            break
                    continue
                else:
                    _loading_status_code = 1
                    # self.sin_out.emit(f"农作物施肥中，使用了{_use_num}次肥料")
                time.sleep(1)

    def step_4(self, crops_pos: tuple):
        """
        第三步: 采集农作物
        """
        if crops_pos == (-1, -1):
            if not self.mouse_move_to_center(self.windows_handle):
                self.sin_out.emit("鼠标移动到屏幕中心失败,请人工检查一下")
                return  False
        else:
            SetGhostMouse().move_mouse_to(crops_pos[0], crops_pos[1])

        SetGhostMouse().click_mouse_left_button()

        _run_code: int = 0

        while 1:

            if not self.working:
                return False

            if not self.find_farmer.find_open_loading(self.windows_handle):

                if _run_code == 1:
                    time.sleep(1)
                    if not self.find_farmer.click_ok(self.windows_handle):
                        self.sin_out.emit("点击确定收获失败,请人工检查一下")
                        self.working = False
                        return  False
                    self.sin_out.emit("农作物已经采集")
                    return True
            else:
                _run_code = 1
                # self.sin_out.emit("正在获取农作物...")
            time.sleep(1)


    def run(self):
        self.mutex.lock()  # 先加锁

        _pick_up_count: int = 0  # 采集了多少次农作物
        _crops_pos: tuple = (-1, -1)  # 农作物的位置，如果坐标不等于(-1, -1)，说明已经有一个可用的坐标了，则不再进行查询

        self.sin_run_status.emit(True)

        self.sin_out.emit("任务5秒后开始执行")
        time.sleep(5)

        while 1:

            if not self.working:
                break
            self.status_bar.emit(_pick_up_count)

            if _pick_up_count >= self.scan_product_num > 0:
                self.sin_out.emit(f"已经执行{_pick_up_count}, 程序停止")
                break

            if not self.find_farmer.find_fertilizer_backpack(self.windows_handle):
                self.sin_out.emit("打开背包失败,请人工检查一下")
                time.sleep(1)
                break

            if not self.find_farmer.check_fertilizer_in_bag(self.windows_handle):
                self.sin_out.emit("未找到肥料,请购买后再来种植:\n"
                                  "普通作物\n"
                                  "   种子 : 肥料 = 1 : 3\n"
                                  "高级作物\n"
                                  "   种子 : 肥料 = 1 : 6")
                time.sleep(1)
                break

            if not self.find_farmer.check_seed_in_bag(self.windows_handle):
                self.sin_out.emit("未找到种子,请购买后再来种植")
                time.sleep(1)
                break

            if not self.step_1():
                break

            if not self.step_2(_crops_pos):
                break

            # 选中一下农作物
            SetGhostMouse().click_mouse_left_button()
            # 更新一下农作物位置
            x, y = SetGhostMouse().get_mouse_x_y()
            _crops_pos = (x, y)

            if not self.step_3():
                break

            if not self.step_4(_crops_pos):
                break

            _pick_up_count += 1


        self.mutex.unlock()  # 解锁
        self.sin_run_status.emit(False)  # 停止任务
        return None
