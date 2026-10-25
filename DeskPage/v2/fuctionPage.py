# coding: utf-8
"""
v2 任务选择界面。

只保留本次迁移的六个功能：
1. 团练授业
2. 上下左右(绿/红)
3. 9点开卡
4. 地图采集
5. 世界竞拍
6. 挑战点兑换书页
7. 清理禁地包裹

任务分发按单选框文本匹配 TaskEnum.value，新增任务时保持两边一致。
"""
import sys
from enum import Enum

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication

from DeskPage.v2.worldMarket import AutoWorldMarket
from Utils.loadResources import get_map_goods_point_list, update_map_goods_point_list


class TaskEnum(Enum):
    dance_grey = "团练授业"
    dance_green = "上下左右(绿/红)"
    open_gift = "9点开卡"
    map_goods_get = "地图采集"
    world_market = "世界竞拍"
    challenge_point_2_book = "挑战点兑换书页"
    get_all_goods = "清理禁地包裹"
    none_selected = "未选择"


class TaskDayWork(QtWidgets.QWidget):
    """每日任务页。"""

    def __init__(self):
        super().__init__()

        self.radio_button_dance_grey = QtWidgets.QRadioButton(TaskEnum.dance_grey.value, self)
        self.radio_button_dance_green = QtWidgets.QRadioButton(TaskEnum.dance_green.value, self)
        self.radio_button_open_gift_card = QtWidgets.QRadioButton(TaskEnum.open_gift.value, self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.radio_button_dance_grey)
        layout.addWidget(self.radio_button_dance_green)
        layout.addWidget(self.radio_button_open_gift_card)

        self.radio_button_dance_grey.setChecked(True)


class TaskLifeWork(QtWidgets.QWidget):
    """物资采集页。"""

    def __init__(self):
        super().__init__()

        label_line = QtWidgets.QLabel("执行路线 ")
        self.combo_box_goods_point_selected = QtWidgets.QComboBox()
        self.radio_button_map_goods_get = QtWidgets.QRadioButton(TaskEnum.map_goods_get.value, self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(label_line)
        layout.addWidget(self.combo_box_goods_point_selected, QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.radio_button_map_goods_get)

        self.radio_button_map_goods_get.setChecked(True)
        self._update_combox_map_goods_point()
        self.combo_box_goods_point_selected.currentTextChanged.connect(
            self._update_selected_line_name)

    def _update_combox_map_goods_point(self):
        """从配置文件加载所有路线，并恢复上次选中的路线。"""
        self.combo_box_goods_point_selected.clear()
        point_list = get_map_goods_point_list()
        line_items: list[str] = []
        selected_name = ""
        for point_dict in point_list:
            line_name = point_dict.get("line_name")
            if line_name is None:
                continue
            line_items.append(line_name)
            if point_dict.get("selected"):
                selected_name = line_name

        self.combo_box_goods_point_selected.addItems(line_items)
        if selected_name and self.combo_box_goods_point_selected.currentText() != selected_name:
            self.combo_box_goods_point_selected.setCurrentText(selected_name)

    def _update_selected_line_name(self, _current_name: str = ""):
        """把当前下拉框选中的路线写回配置文件。"""
        current_name = self.combo_box_goods_point_selected.currentText()
        if not current_name:
            return

        point_list = get_map_goods_point_list()
        new_point_list: list[dict] = []
        for point_dict in point_list:
            new_point_list.append({
                "line_name": point_dict.get("line_name"),
                "map_point": point_dict.get("map_point"),
                "selected": point_dict.get("line_name") == current_name,
            })
        update_map_goods_point_list(new_point_list)


class TaskOther(QtWidgets.QWidget):
    """其他任务页。"""

    def __init__(self):
        super().__init__()

        self.widget_world_market = AutoWorldMarket()
        self.radio_button_world_market = QtWidgets.QRadioButton(TaskEnum.world_market.value, self)
        self.radio_button_challenge_point = QtWidgets.QRadioButton(
            TaskEnum.challenge_point_2_book.value, self)
        self.radio_button_get_all_goods = QtWidgets.QRadioButton(
            TaskEnum.get_all_goods.value, self)

        line_1 = QtWidgets.QHBoxLayout()
        line_1.addWidget(self.radio_button_world_market)

        line_2 = QtWidgets.QHBoxLayout()

        line_2.addWidget(self.radio_button_challenge_point)
        line_2.addWidget(self.radio_button_get_all_goods)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(line_1)
        layout.addLayout(line_2)

        # 默认选中挑战点兑换，避免启动时自动弹出世界竞拍价格窗口
        self.radio_button_challenge_point.setChecked(True)
        self.radio_button_world_market.toggled.connect(self.open_world_market)

    def open_world_market(self, _checked: bool = False):
        """打开世界竞拍价格设置窗口。"""
        if not self.radio_button_world_market.isChecked():
            return
        self.widget_world_market.show()
        self.widget_world_market.raise_()
        self.widget_world_market.load_product_price()


class TaskFunc(QtWidgets.QTabWidget):
    """任务功能选择区域。"""

    def __init__(self):
        super().__init__()
        self.task_day_work = TaskDayWork()
        self.addTab(self.task_day_work, "每日任务")

        self.task_life_work = TaskLifeWork()
        self.addTab(self.task_life_work, "物资采集")

        self.task_other = TaskOther()
        self.addTab(self.task_other, "其他")

    def get_task_active(self) -> TaskEnum:
        """获取当前页签中勾选的任务。"""

        def find_enum_by_value(value: str) -> TaskEnum:
            for member in TaskEnum:
                if member.value == value:
                    return member
            return TaskEnum.none_selected

        current_widget = self.currentWidget()
        for radio in current_widget.findChildren(QtWidgets.QRadioButton):
            if radio.isChecked():
                return find_enum_by_value(radio.text())
        return TaskEnum.none_selected

    def update_radio_enable(self, enable_status: bool):
        """任务执行期间禁用所有任务单选框。"""
        for radio in self.findChildren(QtWidgets.QRadioButton):
            radio.setEnabled(enable_status)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TaskFunc()
    window.show()
    app.exec()
