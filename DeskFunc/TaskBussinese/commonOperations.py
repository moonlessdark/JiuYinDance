"""
放一些通用的操作，会有很多地方用到的
目前有:
1、进度条
2、获取全部
"""
import time

import cv2
import numpy as np
from numpy import fromfile

from Utils.FindWindowsImage import WindowsHandle, FindWindowsImageTemplate, WindowsCapture, PicCapture
from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse
from Utils.dataClass import GoodsOptStatus
from Utils.loadResources import GetConfig


class CommonOperations:
    """
    游戏中的一些通用操作，在这里抽出来避免在其他任务中重复实现
    """
    def __init__(self):
        self._config: GoodsOptStatus = GetConfig().get_goods_opt_status()  # 获取物品使用
        self._windows_opt = WindowsHandle()
        self._windows_find = FindWindowsImageTemplate()
        self._ocr = FindPicOCR()
        self._windows_cap = WindowsCapture()

    @staticmethod
    def _load_pic(img_path: str) -> np.ndarray:
        """
        加载图片
        :param img_path:
        :return:
        """
        return cv2.imdecode(fromfile(img_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    def mouse_click_pos(self, hwnd: int, move_pos: tuple, mouse_type: int) -> bool:
        """
        鼠标点击一下
        :param hwnd 句柄
        :param move_pos 需要移动的坐标(必须是经过Windows转换的)
        :param mouse_type 0-左键 1-右键 2-中键
        """
        if not self._windows_opt.activate_windows(hwnd):
            return False
        x, y = move_pos
        SetGhostMouse().move_mouse_to(x, y)
        time.sleep(0.1)
        if mouse_type == 0:
            SetGhostMouse().click_mouse_left_button()
        elif mouse_type == 1:
            SetGhostMouse().click_mouse_right_button()
        elif mouse_type == 2:
            SetGhostMouse().click_mouse_middle_button()
        else:
            # 如果鼠标类型不是0-1-2，那么就默认点击左键
            SetGhostMouse().click_mouse_left_button()
        time.sleep(0.3)  # 点击之后等待一下，给游戏窗口响应时间
        return True

    def _find_loading_bar_by_template(self, image: np.ndarray) -> bool:
        """
        查找进度条：通过模板匹配
        """
        loading_bar_pos: list = self._windows_find.get_windows_image_area(bigger_img=image,
                                                                           smaller_pic=self._load_pic(self._config.open_loading),
                                                                           threshold=0.7,
                                                                           to_gray=True)
        if loading_bar_pos is None:
            return False
        return True

    @staticmethod
    def _find_progress_bar_by_color(roi: np.ndarray) -> bool:
        """
        查找进度条：检测颜色
        """
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([130, 255, 255]))

        # 1. 检查是否存在连续长条
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > h * 3 and w > 80:  # 长条且足够长
                # print("长度 ", w)
                return True
        return  False

    def find_open_loading(self, hwnd: int) -> bool:
        """
        查询进度条是否出现
        """
        # 方法1：结构特征（上下边框）
        cap = self._windows_cap.capture(hwnd)
        cap_content = cap.pic_content[int(cap.pic_height * 0.5):int(cap.pic_height * 0.9),  # 高度范围
                                      int(cap.pic_width * 0.3):int(cap.pic_width * 0.7)]  # 宽度范围
        template_bool: bool = self._find_loading_bar_by_template(cap_content)
        if template_bool:
            return True
        color_bool: bool = self._find_progress_bar_by_color(cap_content)
        if color_bool:
            return True
        return False


    def _find_get_all_button_pic(self, hwnd: int) -> bool:
        """
        查找“获取全部”按钮：通过模板匹配
        """
        get_all_button_pos: tuple = self._windows_find.get_windows_image_rect(hwnd,
                                                                              template_image=self._load_pic(self._config.get_all_goods),
                                                                              threshold=0.85,
                                                                              to_gray= False)
        if get_all_button_pos is None:
            return False
        return self.mouse_click_pos(hwnd, get_all_button_pos, 0)

    def _find_get_all_button_ocr(self, hwnd: int) -> bool:
        """
        查找“获取全部”按钮：通过OCR识别
        """
        cap: PicCapture = self._windows_cap.capture(hwnd)
        if cap is None:
            return False
        get_all_button_pos: list = self._ocr.find_ocr(cap.pic_content, "全部拾取")
        if get_all_button_pos is None:
            return False
        return self.mouse_click_pos(hwnd, tuple(get_all_button_pos), 0)

    def find_get_all_button(self, hwnd: int) -> bool:
        """
        查询“获取全部”按钮是否出现
        """
        # 方法1：模板匹配
        if self._find_get_all_button_pic(hwnd):
            # print("找到了获取全部的模板")
            return True
        # 方法2：OCR识别
        if self._find_get_all_button_ocr(hwnd):
            # print("找到了获取全部的OCR")
            return  True
        return False
        

class ProgressBarDetector:
    def __init__(self, 
                 frame_interval=0.2, 
                 frame_count=3, 
                 blue_hsv_range=([100,50,50], [130,255,255]),
                 timeout=5.0):  # 新增：默认超时时间5秒
        """
        进度条检测器（支持超时+反复初始化）
        :param frame_interval: 帧间隔时间（秒）
        :param frame_count: 检测所需帧数（至少3）
        :param blue_hsv_range: 蓝色HSV范围 ([lower], [upper])
        :param timeout: 单次检测超时时间（秒），超时后自动重置
        """
        # 基础参数
        self.frame_interval = frame_interval
        self.frame_count = frame_count
        self.lower_blue = np.array(blue_hsv_range[0])
        self.upper_blue = np.array(blue_hsv_range[1])
        self.timeout = timeout  # 超时阈值
        
        # 状态变量（初始化）
        self.reset()  # 调用重置函数初始化所有状态变量

    def reset(self):
        """
        手动初始化/重置所有状态变量（核心：支持反复调用）
        调用场景：1. 初始化 2. 检测超时 3. 主动结束检测
        """
        self.prev_masks = []          # 历史mask列表
        self.last_check_time = 0      # 上一次检测时间
        self.detect_start_time = 0    # 单次检测的开始时间（用于超时判断）
        self.is_detecting = False     # 是否正在检测中（避免重复计时）

    def _get_blue_mask(self, roi):
        """生成蓝色过滤后的mask"""
        if roi is None or roi.size == 0:
            return np.array([])
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_blue, self.upper_blue)
        return mask

    def detect(self, roi):
        """
        实时检测进度条（可反复调用，自带超时+自动重置）
        :param roi: 当前帧的ROI区域（BGR格式）
        :return: tuple - (是否检测到进度条, 是否超时)
        """
        # 1. 初始化检测开始时间（首次调用时）
        if not self.is_detecting:
            self.detect_start_time = time.time()
            self.is_detecting = True

        # 2. 超时判断：超过阈值则重置并返回超时
        current_time = time.time()
        if current_time - self.detect_start_time > self.timeout:
            self.reset()  # 超时后自动初始化变量
            return False, True

        # 3. 生成当前帧mask（空ROI直接返回）
        current_mask = self._get_blue_mask(roi)
        if current_mask.size == 0:
            return False, False

        # 4. 控制帧间隔（避免帧采集过快）
        if current_time - self.last_check_time < self.frame_interval:
            return False, False
        self.last_check_time = current_time

        # 5. 更新历史mask（只保留最近frame_count帧）
        self.prev_masks.append(current_mask)
        if len(self.prev_masks) > self.frame_count:
            self.prev_masks.pop(0)

        # 6. 历史帧不足时，暂不判断
        if len(self.prev_masks) < self.frame_count:
            return False, False

        # 7. 分析动态变化规律
        change_pixels = []
        for i in range(1, len(self.prev_masks)):
            # 计算新增蓝色像素（当前帧 - 上一帧）
            diff = cv2.subtract(self.prev_masks[i], self.prev_masks[i-1])
            non_zero = cv2.findNonZero(diff)
            if non_zero is None:
                continue
            x_mean = np.mean(non_zero[:, 0, 0])  # 新增像素的x坐标均值
            change_pixels.append(x_mean)

        # 8. 基础校验：变化点不足则重置
        if len(change_pixels) < 2:
            self.reset()
            return False, False
        
        # 9. 判断进度条特征：单调递增+足够变化量
        is_increasing = all(
            change_pixels[i] >= change_pixels[i-1] - 10 
            for i in range(1, len(change_pixels))
        )
        total_change = change_pixels[-1] - change_pixels[0]
        
        # 10. 检测到进度条：重置状态，返回结果
        if is_increasing and total_change > 20:
            self.reset()  # 初始化变量，为下一次检测做准备
            return True, False
        
        return False, False

# ------------------- 游戏脚本实战调用示例 -------------------
if __name__ == "__main__":
    # 1. 初始化检测器（设置超时时间为8秒，适配不同场景）
    detector = ProgressBarDetector(frame_interval=0.2, frame_count=3, timeout=8.0)
    
    # 2. 模拟游戏脚本的循环调用（反复检测）
    while True:
        # 模拟截取游戏画面ROI（替换为你的真实截图逻辑）
        # 示例：用pyautogui截图
        # import pyautogui
        # roi = pyautogui.screenshot(region=(500, 800, 900, 820))  # (x1,y1,x2,y2)
        # roi = cv2.cvtColor(np.array(roi), cv2.COLOR_RGB2BGR)
        
        # 测试用静态图（实际脚本删除此行）
        roi = cv2.imread("game_roi.png")
        
        # 3. 调用检测函数（反复调用）
        has_progress, is_timeout = detector.detect(roi)
        
        # 4. 处理检测结果
        if has_progress:
            print(f"[{time.strftime('%H:%M:%S')}] 检测到进度条！")
            # 执行进度条相关逻辑（如等待进度完成）
            time.sleep(2)  # 模拟等待进度条完成
            # 主动重置检测器（可选，确保下一次检测干净）
            detector.reset()
            break  # 示例：检测到后退出循环，实际脚本可继续
            
        if is_timeout:
            print(f"[{time.strftime('%H:%M:%S')}] 进度条检测超时！")
            # 超时处理逻辑（如重新触发道具使用）
            detector.reset()  # 重置后可再次开始检测
        
        # 脚本循环间隔（避免CPU占用过高）
        time.sleep(0.2)
