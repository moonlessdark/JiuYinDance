import sys
from enum import Enum

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QApplication
from DeskPage.worldMarket import AutoWorldMarket
from DeskPage.skillSettingDialog import SkillSetting
from Utils.loadResources import get_map_goods_point_list, update_map_goods_point_list


class TaskEnum(Enum):
    dance_grey = "团练授业"
    dance_green = "上下左右(绿/红)"
    open_gift = "9点开卡"
    express_transportation = "押镖任务"
    map_goods_get = "地图采集"
    game_pic_screen = "游戏截图"
    xj_secret_scene = "玄机秘境报名"
    world_market = "世界竞拍"
    none_selected = "未选择"


class TaskDayWork(QtWidgets.QWidget):
    """
    每日任务
    """
    def __init__(self):
        super().__init__()

        self.radio_button_dance_grey = QtWidgets.QRadioButton(TaskEnum.dance_grey.value, self)
        self.radio_button_dance_green = QtWidgets.QRadioButton(TaskEnum.dance_green.value, self)
        self.radio_button_open_gift_card = QtWidgets.QRadioButton(TaskEnum.open_gift.value, self)

        _lay_out_dance_widget = QtWidgets.QHBoxLayout(self)
        _lay_out_dance_widget.addWidget(self.radio_button_dance_grey)
        _lay_out_dance_widget.addWidget(self.radio_button_dance_green)
        _lay_out_dance_widget.addWidget(self.radio_button_open_gift_card)

        # 默认把第一个选项勾上
        self.radio_button_dance_grey.setChecked(True)


class TaskActivity(QtWidgets.QWidget):
    """
    活动任务
    """
    def __init__(self):
        super().__init__()

        _label_express_transportation_run_number = QtWidgets.QLabel("执行次数")
        # 输入运行次数，默认1次
        self.input_line_express_transportation = QtWidgets.QLineEdit()
        self.input_line_express_transportation.setText("1")
        self.input_line_express_transportation.setValidator(QIntValidator())  # 设置整数验证器

        push_button_express_transportation = QtWidgets.QPushButton("编辑技能", self)
        self.radio_express_transportation = QtWidgets.QRadioButton(TaskEnum.express_transportation.value, self)

        _lay_out_activity_widget = QtWidgets.QHBoxLayout(self)
        _lay_out_activity_widget.addWidget(_label_express_transportation_run_number)
        _lay_out_activity_widget.addWidget(self.input_line_express_transportation)
        _lay_out_activity_widget.addWidget(self.input_line_express_transportation)
        _lay_out_activity_widget.addWidget(push_button_express_transportation)
        _lay_out_activity_widget.addWidget(self.radio_express_transportation)

        # 默认把第一个按钮勾上
        self.radio_express_transportation.setChecked(True)
        push_button_express_transportation.clicked.connect(self.open_skill_setting)

    def open_skill_setting(self):
        """
        打开技能编辑
        :return:
        """
        _skill = SkillSetting(self)
        if not _skill.isVisible():
            _skill.show()
            _skill.load_skill_table()


class TaskOther(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.widget_world_market = AutoWorldMarket()
        self.widget_world_market.raise_()  # 将窗口置于最前（如果需要）

        self.radio_button_game_pic_screen = QtWidgets.QRadioButton(TaskEnum.game_pic_screen.value, self)
        self.radio_button_xj_secret_scene = QtWidgets.QRadioButton(TaskEnum.xj_secret_scene.value, self)

        self.radio_express_auto_buy = QtWidgets.QRadioButton(TaskEnum.world_market.value, self)

        _lay_out_other_widget = QtWidgets.QHBoxLayout(self)
        _lay_out_other_widget.addWidget(self.radio_button_xj_secret_scene)
        _lay_out_other_widget.addWidget(self.radio_button_game_pic_screen)
        _lay_out_other_widget.addWidget(self.radio_express_auto_buy)

        # 默认把第一个按钮勾上
        self.radio_button_xj_secret_scene.setChecked(True)
        self.radio_express_auto_buy.toggled.connect(self.open_world_market)

    def open_world_market(self):
        """
        打开世界竞拍
        :return:
        """

        if self.radio_express_auto_buy.isChecked():
            self.widget_world_market.show()
            self.widget_world_market.load_product_price()

class TaskLifeWork(QtWidgets.QWidget):
    """
    生活技能
    """
    def __init__(self):
        super().__init__()
        _label_goods_point_selected = QtWidgets.QLabel("执行路线 ")
        self.combo_box_goods_point_selected = QtWidgets.QComboBox()
        self.radio_button_map_goods_get = QtWidgets.QRadioButton(TaskEnum.map_goods_get.value, self)

        _lay_out_life_work_widget = QtWidgets.QHBoxLayout(self)
        _lay_out_life_work_widget.addWidget(_label_goods_point_selected)
        _lay_out_life_work_widget.addWidget(self.combo_box_goods_point_selected, QtCore.Qt.AlignmentFlag.AlignLeft)
        _lay_out_life_work_widget.addWidget(self.radio_button_map_goods_get)

        # 默认把第一个按钮勾上
        self.radio_button_map_goods_get.setChecked(True)
        self._update_combox_map_goods_point()

        self.combo_box_goods_point_selected.currentTextChanged.connect(self._update_selected_line_name)

    def _update_combox_map_goods_point(self):
        """
        更新地图路线的下拉框的值
        """
        self.combo_box_goods_point_selected.clear()

        # 数据更新后继续设置一下默认选项
        point_list: list = get_map_goods_point_list()  # 配置文件中的所有路线
        _line_item: list = []
        _line_selected_name: str = ""
        for point_dict in point_list:
            _line_name: str = point_dict.get("line_name")  # 路线名
            _line_selected: bool = point_dict.get("selected")
            _line_item.append(_line_name)
            if _line_selected:
                _line_selected_name = _line_name
        self.combo_box_goods_point_selected.addItems(_line_item)
        if _line_selected_name != "":
            if self.combo_box_goods_point_selected.currentText() != _line_selected_name:
                self.combo_box_goods_point_selected.setCurrentText(_line_selected_name)
        else:
            # 说明配置文件有问题，没有设置默认路径，那么就默认使用第一个
            if len(point_list) > 0:
                pp_dict: dict = point_list[0]
                _line_name: str = pp_dict.get("line_name")  # 路线名
                self.combo_box_goods_point_selected.setCurrentText(_line_selected_name)

    def _update_selected_line_name(self):
        """
        更新默认选择的路线，方便下次进来后加载
        :return:
        """
        _current_name: str = self.combo_box_goods_point_selected.currentText()
        point_list: list = get_map_goods_point_list()  # 配置文件中的所有路线
        _new_point_list: list = []
        for point_dict in point_list:
            new_line_dict: dict = {"line_name": point_dict.get("line_name"),
                                   "map_point": point_dict.get("map_point"),
                                   'selected': False}
            if point_dict.get("line_name") == _current_name:
                new_line_dict['selected'] = True
            _new_point_list.append(new_line_dict)
        update_map_goods_point_list(_new_point_list)


class TaskFunc(QtWidgets.QTabWidget):

    def __init__(self):
        """
        任务功能选择区域
        """
        super().__init__()
        self.task_day_work = TaskDayWork()
        self.addTab(self.task_day_work, "每日任务")
        self.task_activity = TaskActivity()
        self.addTab(self.task_activity, "押镖任务")
        self.task_life_work = TaskLifeWork()
        self.addTab(self.task_life_work, "物资采集")
        self.task_other = TaskOther()
        self.addTab(self.task_other, "其他")

    def get_task_active(self) -> TaskEnum:
        """
        获取当前启用了哪个任务
        :return:
        """

        def find_enum_key_by_value(value: str) -> TaskEnum:
            """
            通过value查询枚举
            :param value:
            :return:
            """
            for member in TaskEnum:
                if member.value == value:
                    return member
            return TaskEnum.none_selected

        _current_widget: QtWidgets.QWidget = self.currentWidget()
        for _radio_widget in _current_widget.findChildren(QtWidgets.QRadioButton):
            if _radio_widget.isChecked():
                _selected_task: TaskEnum = find_enum_key_by_value(_radio_widget.text())
                return _selected_task
        return TaskEnum.none_selected

    def update_radio_enable(self, enable_status: bool):
        """
        将所有按钮，启用或者禁用
        :param enable_status:
        :return:
        """
        for radio_w in self.findChildren(QtWidgets.QRadioButton):
            if enable_status is False:
                radio_w.setEnabled(False)
            else:
                radio_w.setEnabled(True)


if __name__ == '__main__':
    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    w = TaskFunc()
    w.show()
    app.exec()
