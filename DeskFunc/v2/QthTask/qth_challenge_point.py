# coding: utf-8
"""
挑战点兑换书页任务线程。

纯模板匹配，不含 OCR。流程与 v1 保持一致，每一步失败时输出明确原因并停止。

执行策略（提速同时兼顾客户端响应）：
1. 不再用固定 sleep 等界面刷新，改成“点击后轮询等待下一个图标出现”，
   目标一出现就继续，客户端响应慢时自动等到超时；
2. 单步超时后允许重放一次上一步操作，覆盖点击丢失/网络延迟；
   只有幂等步骤（选中、展开类操作）才重放，有兑换副作用的步骤只延长等待；
3. 点击后保留最小间隔，避免客户端丢点击；
4. 找不到“兑换”按钮时，用兑换面板是否还在来区分“点数不足”和“面板被关闭”；
5. 兑换成功后有副作用，不能盲目重放，改成“等确认框关闭再进入下一轮”，
   避免下一轮点击技能书页时被仍在关闭的确认框吃掉，从而误判为点数不足。
"""
import time
from typing import Optional

from Core.vision.target import TargetSpec

from DeskFunc.v2.QthTask.base_task import BaseTaskThread
from DeskFunc.v2.TaskBussinese.challenge_point import ChallengePointExchange


class ChallengePointTask(BaseTaskThread):
    """挑战点兑换书页任务。"""

    START_DELAY = 3.0  # 启动等待，给玩家确认任务选择的时间
    POLL_INTERVAL = 0.1  # 单步轮询间隔
    STEP_TIMEOUT = 1.6  # 单步首次等待超时
    RETRY_TIMEOUT = 1.0  # 重放上一步后的等待超时
    CLICK_REACT_DELAY = 0.15  # 点击后留给客户端的响应时间
    CLICK_MIN_INTERVAL = 0.2  # 两次点击之间的最小间隔
    MAX_SHOP_BOOK_RETRY = 3  # 连续点击夺魄书页的最大次数
    MAX_BOOK_SELECT_RETRY = 3  # 点击技能书页并等待兑换按钮的最大尝试次数
    DIALOG_CLOSE_TIMEOUT = 2.5  # 等待兑换确认框关闭的超时
    ROUND_SETTLE_DELAY = 0.3  # 确认框关闭后，留给面板恢复状态的额外时间

    def __init__(self):
        super().__init__()
        self._hwnd = 0
        self._exchange = ChallengePointExchange()
        self._last_click_time = 0.0

    def init_task_param(self, hwnd: int):
        """初始化执行参数。"""
        self._hwnd = hwnd
        self._last_click_time = 0.0
        self.working = True

    def _sleep_working(self, seconds: float) -> bool:
        """可被停止打断的等待，返回 False 表示任务已被停止。"""
        deadline = time.monotonic() + seconds
        while self.working:
            remain = deadline - time.monotonic()
            if remain <= 0:
                return True
            time.sleep(min(self.POLL_INTERVAL, remain))
        return False

    def _click_match(self, match) -> bool:
        """点击匹配结果，并保证两次点击之间有最小间隔。"""
        clicked = self._exchange.click_match(self._hwnd, match, react_delay=self.CLICK_REACT_DELAY)
        elapsed = time.monotonic() - self._last_click_time
        if elapsed < self.CLICK_MIN_INTERVAL:
            time.sleep(self.CLICK_MIN_INTERVAL - elapsed)
        self._last_click_time = time.monotonic()
        return clicked

    def _wait_and_click(self, spec: TargetSpec, timeout: float) -> bool:
        """轮询等待目标出现并点击，命中返回 True。"""
        deadline = time.monotonic() + timeout
        while self.working:
            pic = self._exchange.capture(self._hwnd)
            if pic is not None:
                match = self._exchange.locate_target(self._hwnd, spec, pic=pic)
                if match is not None and match.screen_point is not None:
                    # 点击失败（例如窗口激活失败）时不认为完成，继续等到超时
                    if self._click_match(match):
                        return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(self.POLL_INTERVAL)
        return False

    def _wait_target(self, spec: TargetSpec, timeout: float) -> bool:
        """
        轮询等待目标出现，只做识别不做点击。

        用于确认某个图标已经渲染（例如回收栏），省掉一次点击的移动与响应等待。

        :return: True 表示超时前识别到目标
        """
        deadline = time.monotonic() + timeout
        while self.working:
            pic = self._exchange.capture(self._hwnd)
            if pic is not None and self._exchange.locate_target(
                    self._hwnd, spec, pic=pic) is not None:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(self.POLL_INTERVAL)
        return False

    def _wait_next(self, spec: TargetSpec, prev_spec: Optional[TargetSpec] = None) -> bool:
        """
        等待下一个目标出现并点击。

        首次超时后重放一次上一步（仅限幂等步骤），再等待一次，
        覆盖“点击丢失”或“客户端尚未响应”的情况。
        上一步图标已经消失、无法重放时，仍然多等一轮，避免误判失败。

        :param spec: 当前要等待的目标
        :param prev_spec: 上一步操作的目标；None 表示不允许重放
        """
        if self._wait_and_click(spec, self.STEP_TIMEOUT):
            return True
        if not self.working:
            return False
        if prev_spec is not None:
            self.sin_out.emit(f"窗口:{self._hwnd} 未发现'{spec.name}'，重试上一步")
            self._wait_and_click(prev_spec, self.RETRY_TIMEOUT)
        return self._wait_and_click(spec, self.RETRY_TIMEOUT)

    def _panel_intact(self) -> bool:
        """确认兑换面板还在（技能书页或回收栏仍可见）。"""
        pic = self._exchange.capture(self._hwnd)
        if pic is None:
            return False
        if self._exchange.locate_target(self._hwnd, self._exchange.spec_book_page, pic=pic):
            return True
        return self._exchange.locate_target(
            self._hwnd, self._exchange.spec_recycle_box, pic=pic) is not None

    def _wait_dialog_closed(self, timeout: float) -> bool:
        """
        等待兑换的二次确认框关闭（“二次确认兑换”按钮消失）。

        调用前刚点击过二次确认，所以按钮一定处于可见状态；按钮消失即代表兑换已生效、
        面板已恢复。兑换刚结束时若立刻开始下一轮，技能书页的点击可能被仍在关闭的
        确认框吃掉。

        :return: True 表示确认框已消失；False 表示等待超时
        """
        deadline = time.monotonic() + timeout
        while self.working:
            pic = self._exchange.capture(self._hwnd)
            if pic is not None and self._exchange.locate_target(
                    self._hwnd, self._exchange.spec_exchange_re_ok, pic=pic) is None:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(self.POLL_INTERVAL)
        return False

    def _select_book_and_exchange(self) -> str:
        """
        点击技能书页，等待并点击“兑换”按钮，同时用按钮是否出现判断兑换点数是否足够。

        兑换刚结束时客户端可能还在处理关闭动画，第一次点击技能书页会被吞掉，
        表现为“点击了书页但兑换按钮不出现”。因此这里允许重复点击书页
        （选中操作，重复点击无副作用），多次尝试后按钮仍不出现才判定点数不足。

        :return: ok 已点击兑换按钮；insufficient 点数不足；panel_lost 兑换面板丢失；
                 book_missing 未找到技能书页；stopped 任务被停止
        """
        for attempt in range(1, self.MAX_BOOK_SELECT_RETRY + 1):
            if not self._wait_and_click(self._exchange.spec_book_page, self.STEP_TIMEOUT):
                if not self.working:
                    return "stopped"
                return "book_missing"
            self.sin_out.emit(f"窗口:{self._hwnd} 已获取技能书页")

            if self._wait_and_click(self._exchange.spec_exchange_button, self.STEP_TIMEOUT):
                return "ok"
            if not self.working:
                return "stopped"

            if attempt < self.MAX_BOOK_SELECT_RETRY:
                self.sin_out.emit(
                    f"窗口:{self._hwnd} 未发现兑换按钮，第{attempt + 1}次重试点击技能书页")
                if not self._sleep_working(self.CLICK_REACT_DELAY):
                    return "stopped"

        # 多次选中书页后按钮仍未出现，用兑换面板是否仍在，区分“点数不足”和“面板被关闭”
        if not self._panel_intact():
            return "panel_lost"
        return "insufficient"

    def run(self):
        self.mutex.lock()
        exchange_count = 0
        shop_book_retry = 0
        try:
            self.sin_run_status.emit(True)
            self.sin_out.emit("3秒后执行开始执行...")
            if not self._sleep_working(self.START_DELAY):
                return None

            while self.working:
                self.status_bar.emit(exchange_count)

                check_code = self._exchange.check_pic_template_exist(self._hwnd)
                if check_code != 0:
                    if check_code == -1:
                        # 未发现技能书页：先点击左侧的夺魄书页展开列表
                        if shop_book_retry >= self.MAX_SHOP_BOOK_RETRY:
                            self.sin_out.emit(
                                f"窗口:{self._hwnd} 多次点击夺魄书页后仍未出现技能书页，程序停止")
                            self.working = False
                        elif not self._wait_and_click(self._exchange.spec_shop_book,
                                                      self.STEP_TIMEOUT):
                            self.sin_out.emit(
                                f"窗口:{self._hwnd} 未发现'夺魄的书页'，"
                                "请先打开'夺魄'的技能书页页面")
                            self.working = False
                        else:
                            shop_book_retry += 1
                    elif check_code == -2:
                        self.sin_out.emit(
                            f"窗口:{self._hwnd} 未找到兑换窗口,请先点击NPC打开兑换窗口")
                        self.working = False
                    else:
                        self.sin_out.emit(f"窗口:{self._hwnd} 其他错误:{check_code}，程序停止")
                        self.working = False
                    continue

                shop_book_retry = 0

                # 第一步+第二步：点击技能书页，等待兑换按钮，同时判断点数是否足够
                select_status = self._select_book_and_exchange()
                if select_status == "stopped":
                    break
                if select_status == "book_missing":
                    self.sin_out.emit(
                        f"窗口:{self._hwnd} 未找到技能书页（{self._exchange.last_hit_mode}）")
                    self.working = False
                    break
                if select_status == "panel_lost":
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换窗口")
                    self.working = False
                    break
                if select_status == "insufficient":
                    self.sin_out.emit(
                        f"窗口:{self._hwnd} 兑换点数不足，任务结束（本次已兑换 {exchange_count} 次）")
                    break

                # 第三步：背包中的书页（上一步点击兑换按钮属于选择操作，重复点击无副作用）
                if not self._wait_next(self._exchange.spec_backpack_item,
                                       prev_spec=self._exchange.spec_exchange_button):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到背包中的夺魄书页")
                    self.working = False
                    break

                # 第四步：回收栏（上一步点击背包书页，不重放，避免重复放入物品）
                if not self._wait_and_click(self._exchange.spec_recycle_box,
                                            self.STEP_TIMEOUT + self.RETRY_TIMEOUT):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换窗口")
                    self.working = False
                    break

                # 第五步：兑换结果预览（点击回收栏后图标会自动渲染，只需确认出现，
                # 不再点击一次，省掉鼠标移动和点击响应约 0.5 秒）
                if not self._wait_target(self._exchange.spec_recycle_result,
                                         self.STEP_TIMEOUT + self.RETRY_TIMEOUT):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到兑换结果")
                    self.working = False
                    break

                # 第六步：确认兑换（打开二次确认框，可重放）
                if not self._wait_next(self._exchange.spec_exchange_ok,
                                       prev_spec=self._exchange.spec_recycle_result):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到确认兑换")
                    self.working = False
                    break

                # 第七步：二次确认（真正执行兑换，失败只等待识别，不重放点击）
                if not self._wait_and_click(self._exchange.spec_exchange_re_ok,
                                            self.STEP_TIMEOUT + self.RETRY_TIMEOUT):
                    self.sin_out.emit(f"窗口:{self._hwnd} 未找到二次确认兑换")
                    self.working = False
                    break

                # 确认框关闭才说明兑换真正生效；没关闭说明点击可能被吞，此时框仍在，
                # 补点一次二次确认是安全的（框已关闭时不会匹配到按钮，也就不会重复兑换）
                if not self._wait_dialog_closed(self.DIALOG_CLOSE_TIMEOUT):
                    self.sin_out.emit(f"窗口:{self._hwnd} 兑换确认框未关闭，重试二次确认")
                    self._wait_and_click(self._exchange.spec_exchange_re_ok, self.STEP_TIMEOUT)
                    self._wait_dialog_closed(self.DIALOG_CLOSE_TIMEOUT)

                self.sin_out.emit(f"窗口:{self._hwnd} 幸运币兑换成功")
                exchange_count += 1
                # 等面板恢复后再进入下一轮，避免下一轮点击技能书页被关闭动画吃掉
                if not self._sleep_working(self.ROUND_SETTLE_DELAY):
                    break
        finally:
            self.sin_run_status.emit(False)
            self.mutex.unlock()
        return None
