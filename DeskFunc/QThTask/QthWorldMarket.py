import os
import time

import cv2
from PySide6.QtCore import QThread, Signal, QWaitCondition, QMutex
from DeskFunc.TaskBussinese.findAuctionMarket import FindAuctionMarket
from Utils.FindWindowsImage import WindowsCapture, PicCapture, WindowsHandle
from Utils.ImageUtils.MonitorDisplay import coordinate_change_from_windows
from Utils.KeyMouseDriver.GhostSoft.get_driver_v3 import SetGhostMouse


class WorldMarketGetGoodsQth(QThread):
    """
    世界竞拍,获取商品
    """
    sin_out = Signal(list)
    status_information = Signal(int)
    sin_run_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self.scan_product_num: int = 2
        self.product_sell_price: list = []
        self.pic_save_path = None
        self.working = True
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.windows_cap = WindowsCapture()
        self.windows_handle: int = 0
        self.func = FindAuctionMarket()

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

    def get_param(self, windows_handle: int, product_price_list: list, scan_product_num: int):
        """
        线程用到的参数初始化一下
        :return:
        """
        self.working = True
        self.cond.wakeAll()
        self.windows_handle = windows_handle
        self.product_sell_price = product_price_list
        self.scan_product_num = scan_product_num

    def run(self):
        self.mutex.lock()  # 先加锁
        self.sin_run_status.emit(True)  # 发送消息，人物开始


        while self.working:
            if not self.working:
                break

            cap_img: PicCapture = self.windows_cap.capture(self.windows_handle)
            if cap_img is None:
                self.working = False
                self.sin_out.emit("窗口句柄异常,请重新获取窗口")
                break

            _goods_list = self.func.find_goods_list(image=cap_img.pic_content, scan_product_num=self.scan_product_num)
            for product_line in _goods_list:
                _product_name: str = product_line[1]  # 物品
                _product_current_price: int = product_line[2]  # 当前出价
                _product_pos_in_windows: tuple = coordinate_change_from_windows(self.windows_handle, product_line[3])  # 在游戏窗口内的坐标，使用时需要转换一下

                if not self.working:
                    break

                # [{'product_name': '冰心诀', 'min_price': '1', 'max_price': '2'}, {'product_name': '古朴残卷(绝世高手)', 'min_price': '3', 'max_price': '4'}, {'product_name': '太极拳', 'min_price': '', 'max_price': ''}, {'product_name': '寒宵诀', 'min_price': '', 'max_price': ''}, {'product_name': '心斋秘箓', 'min_price': '', 'max_price': ''}, {'product_name': '打狗八绝', 'min_price': '', 'max_price': ''}, {'product_name': '拈花功', 'min_price': '', 'max_price': ''}, {'product_name': '拓本碎片', 'min_price': '', 'max_price': ''}, {'product_name': '无妄神功', 'min_price': '', 'max_price': ''}, {'product_name': '星河剑律参悟图', 'min_price': '', 'max_price': ''}, {'product_name': '残破星图', 'min_price': '', 'max_price': ''}, {'product_name': '毒哈经', 'min_price': '', 'max_price': ''}, {'product_name': '混元功', 'min_price': '', 'max_price': ''}, {'product_name': '焚天令', 'min_price': '', 'max_price': ''}, {'product_name': '若水神点拓本', 'min_price': '', 'max_price': ''}, {'product_name': '若水神点', 'min_price': '', 'max_price': ''}, {'product_name': '血海刀罡', 'min_price': '', 'max_price': ''}, {'product_name': '血海魔刀录', 'min_price': '', 'max_price': ''}, {'product_name': '醉仙箓', 'min_price': '', 'max_price': ''}, {'product_name': '魅影剑法', 'min_price': '', 'max_price': ''}, {'product_name': '五彩环', 'min_price': '', 'max_price': ''}, {'product_name': '霸主令', 'min_price': '', 'max_price': ''}, {'product_name': '金银花', 'min_price': '', 'max_price': ''}, {'product_name': '觉梦丹礼包', 'min_price': '', 'max_price': ''}, {'product_name': '五行功法', 'min_price': '', 'max_price': ''}, {'product_name': '残阳功诀', 'min_price': '', 'max_price': ''}, {'product_name': '叫花鸡', 'min_price': '', 'max_price': ''}, {'product_name': '若水神点拓本碎片', 'min_price': '', 'max_price': ''}]
                result: list = list(filter(lambda product: product['product_name'] == _product_name, self.product_sell_price))
                if result is None:
                    # 如果没有匹配到产品，说明这个产品设置缺失了，就跳过
                    self.sin_out.emit(f"物品: {_product_name} 未收录到程序中,无法识别")
                    continue
                product_dict: dict = result[0]
                _product_max_price: int = 0 if product_dict.get('max_price') == "" else int(product_dict.get('max_price'))
                _product_min_price: int = 0 if product_dict.get('min_price') == "" else int(product_dict.get('min_price'))
                if _product_max_price == 0:
                    # 如果这个产品没有设置最大竞拍价格，就跳过，说明这个产品不需要竞拍
                    continue
                if _product_min_price == 0:
                    # 如果最小值是0，表示没有设置，那么默认竞拍最后20L,别浪费金额
                    _product_min_price = _product_max_price - 21

                """
                检测物品当前的竞拍价是否在设置表格中的出价范围内
                并且最大出价需要减去待会加价的10L银子
                """
                if not (_product_min_price <= _product_current_price <= _product_max_price - 10):
                    # 不在出价范围内，换下一个
                    continue
                self.sin_out(f"{_product_name} 符合出价条件,当前价格:{_product_current_price}")
                # 既然在出价返回内了，那么开始出价
                if self.windows_handle == 0:
                    self.working = False
                    break

                if not WindowsHandle().activate_windows(self.windows_handle):
                    continue
                SetGhostMouse().move_mouse_to(_product_pos_in_windows[0], _product_pos_in_windows[1])
                SetGhostMouse().click_mouse_left_button()
                time.sleep(0.3)

                """
                开始出价
                """
                _is_plus_success = False  # 加价10L是否成功
                for i in range(2):
                    # 点击右侧的加价按钮
                    market_pic_contents: PicCapture = self.windows_cap.capture(self.windows_handle)
                    __plus_price_pos = self.func.find_plus_price(market_pic_contents.pic_content)
                    __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle, coordinate=__plus_price_pos[0])
                    SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.3)
                    # 判断“确认出价”按钮是否高亮可点击
                    temp_cap_img: PicCapture = self.windows_cap.capture(self.windows_handle)
                    sum_button_rect = self.func.find_summit_price(temp_cap_img.pic_content)
                    if sum_button_rect is None:
                        # 不可点击,可能刚好卡了最后一秒，此物品竞拍结束
                        # 退出本次物品检测，重新刷新页面后再次最新的物品检测
                        continue
                    else:
                        # 把加价的按钮的坐标转一下
                        pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle,
                                                                        coordinate=sum_button_rect)
                        SetGhostMouse().move_mouse_to(pic_pos[0], pic_pos[1])
                        SetGhostMouse().click_mouse_left_button()
                        time.sleep(0.2)
                        _is_plus_success = True
                        break
                if not _is_plus_success:
                    # 加价2次都失败
                    break

                if not self.working:
                    break

                # 二次确认出价
                temp_2_cap_img: PicCapture = self.windows_cap.capture(self.windows_handle)
                re_summit_pic_button_pos = self.func.find_re_summit_price(temp_2_cap_img.pic_content)
                if re_summit_pic_button_pos is not None:
                    __pic_pos: tuple = coordinate_change_from_windows(hwnd=self.windows_handle,
                                                                      coordinate=re_summit_pic_button_pos[0])
                    SetGhostMouse().move_mouse_to(__pic_pos[0], __pic_pos[1])
                    SetGhostMouse().click_mouse_left_button()
                    self.sin_out.emit(f"{_product_name} 加价10两")
                time.sleep(0.2)

                # 出价结束，结束本次产品循环，重新刷新了产品列表后再次进行出价
                break

        self.sin_run_status.emit(False)  # 发送消息，任务结束了
        self.mutex.unlock()
