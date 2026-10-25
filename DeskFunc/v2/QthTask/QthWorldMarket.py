# coding: utf-8
"""
世界竞拍任务线程。

本任务不依赖 OCR，物品名、价格数字、单位、按钮全部由 v2 auctionMarket 模板匹配完成。
"""
import time

from Core.input.ghost import SetGhostMouse
from Core.windows.capture import PicCapture, WindowsCapture
from Core.windows.geometry import client_to_screen
from Core.windows.window import WindowsHandle
from DeskFunc.v2.QthTask.baseTask import BaseTaskThread
from DeskFunc.v2.TaskBussinese.auctionMarket import FindAuctionMarket, MarketProduct


class WorldMarketTask(BaseTaskThread):
    """世界竞拍自动出价任务。"""

    def __init__(self):
        super().__init__()
        self._windows_handle = 0
        self._scan_product_num = 2
        self._product_sell_price: list[dict] = []
        self._product_pass_name_list: list[str] = []
        self._capture = WindowsCapture()
        self._find_market = FindAuctionMarket()

    def get_param(self, windows_handle: int, product_price_list: list[dict],
                  scan_product_num: int):
        """初始化执行参数。"""
        self.working = True
        self._windows_handle = windows_handle
        self._product_sell_price = list(product_price_list)
        self._product_pass_name_list = [
            product["product_name"] for product in product_price_list
            if product.get("max_price") != ""
        ]
        self._scan_product_num = int(scan_product_num)

    def run(self):
        self.mutex.lock()
        try:
            self.sin_run_status.emit(True)

            while self.working:
                capture: PicCapture = self._capture.capture(self._windows_handle)
                if capture is None:
                    self.working = False
                    self.sin_out.emit("窗口句柄异常,请重新获取窗口")
                    break

                goods_list: list[MarketProduct] = self._find_market.find_goods_list(
                    image=capture.pic_content,
                    scan_product_num=self._scan_product_num,
                    pass_product_name=self._product_pass_name_list,
                )

                for goods in goods_list:
                    if not self.working:
                        break

                    setting = next((item for item in self._product_sell_price
                                    if item["product_name"] == goods.product_name), None)
                    if setting is None:
                        self.sin_out.emit(f"物品: {goods.product_name} 未收录到程序中,无法识别")
                        continue

                    max_price = 0 if setting.get("max_price") == "" else int(setting.get("max_price"))
                    min_price = 0 if setting.get("min_price") == "" else int(setting.get("min_price"))
                    if max_price == 0:
                        continue
                    if min_price == 0:
                        # 没有设置最低价时默认只竞拍最后 21 两，避免浪费
                        min_price = max_price - 21

                    if not (min_price <= goods.current_price <= max_price - 10):
                        continue

                    self.sin_out.emit(
                        f"{goods.product_name} 符合出价条件,当前价格:{goods.current_price}")

                    if not WindowsHandle().activate_windows(self._windows_handle):
                        continue

                    product_point = client_to_screen(
                        self._windows_handle, (goods.client_x, goods.client_y))
                    SetGhostMouse().move_mouse_to(product_point[0], product_point[1])
                    SetGhostMouse().click_mouse_left_button()
                    time.sleep(0.3)

                    plus_success = False
                    for _ in range(2):
                        if not self.working:
                            break

                        market_capture = self._capture.capture(self._windows_handle)
                        if market_capture is None:
                            break

                        plus_points = self._find_market.find_plus_price(market_capture.pic_content)
                        if not plus_points:
                            # 加价按钮消失，通常表示竞拍已经结束
                            break

                        plus_point = client_to_screen(
                            self._windows_handle, (plus_points[0][0], plus_points[0][1]))
                        SetGhostMouse().move_mouse_to(plus_point[0], plus_point[1])
                        SetGhostMouse().click_mouse_left_button()
                        time.sleep(0.3)

                        summit_capture = self._capture.capture(self._windows_handle)
                        if summit_capture is None:
                            continue
                        summit_point = self._find_market.find_summit_price(summit_capture.pic_content)
                        if summit_point is None:
                            # 确认按钮不可点击，可能竞拍刚好结束
                            continue

                        summit_screen = client_to_screen(self._windows_handle, summit_point)
                        SetGhostMouse().move_mouse_to(summit_screen[0], summit_screen[1])
                        SetGhostMouse().click_mouse_left_button()
                        time.sleep(0.2)
                        plus_success = True
                        break

                    if not plus_success:
                        # 两次加价都失败，刷新页面后重新扫描
                        break

                    if not self.working:
                        break

                    confirm_capture = self._capture.capture(self._windows_handle)
                    if confirm_capture is None:
                        break
                    re_summit_points = self._find_market.find_re_summit_price(
                        confirm_capture.pic_content)
                    if re_summit_points:
                        re_summit_point = client_to_screen(
                            self._windows_handle,
                            (re_summit_points[0][0], re_summit_points[0][1]))
                        SetGhostMouse().move_mouse_to(re_summit_point[0], re_summit_point[1])
                        SetGhostMouse().click_mouse_left_button()
                        self.sin_out.emit(f"{goods.product_name} 加价10两")
                    time.sleep(0.2)

                    # 一次只处理一个物品，刷新列表后重新扫描
                    break

                # 没有可竞拍物品时避免空转占满 CPU
                time.sleep(0.3)
        finally:
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
