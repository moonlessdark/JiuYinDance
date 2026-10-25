# coding: utf-8
"""
地图采集路线编辑器。

配置文件 Resources/mapGoodsPointList.json 使用 GBK 编码读写，
这里沿用 Utils.loadResources 中的读写函数，避免中文路线名损坏。
"""
from PySide6 import QtWidgets, QtCore

from Utils.loadResources import get_map_goods_point_list, update_map_goods_point_list


class MapPointTable(QtWidgets.QDialog):
    """设置采集坐标的表格对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置采集坐标")
        self.resize(530, 300)

        self._table_map_goods_point = QtWidgets.QTableWidget(self)
        self._table_map_goods_point.setRowCount(1)
        self._table_map_goods_point.setColumnCount(2)

        self._button_add_map_goods_point_row = QtWidgets.QPushButton("新增")
        self._button_del_map_goods_point_row = QtWidgets.QPushButton("删除")
        self._button_save_map_goods_point_table = QtWidgets.QPushButton("保存")
        self._button_save_map_goods_point_table.setToolTip(
            "首次运行新路线时,需要人工监控。\n"
            "如果出现坐标在点击小地图时没有采集而是向其他方向移动,说明此坐标地形干扰大。"
            "请尝试调整坐标(x或者y轴加减1反复调试)。\n"
            "如果物资旁边有个NPC,在自动采集时很大概率会自动点击到此NPC,这种坐标请跳过。")

        # 下拉框仅用于记录当前选中路线，不显示在界面上
        self._combo_box_goods_point_selected = QtWidgets.QComboBox()
        self._combo_box_goods_point_selected.setVisible(False)

        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        button_layout.addWidget(self._combo_box_goods_point_selected)
        button_layout.addSpacing(250)
        button_layout.addWidget(self._button_add_map_goods_point_row)
        button_layout.addWidget(self._button_del_map_goods_point_row)
        button_layout.addWidget(self._button_save_map_goods_point_table)
        button_layout.setSpacing(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(button_widget)
        layout.addWidget(self._table_map_goods_point)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        self._button_add_map_goods_point_row.clicked.connect(
            self.add_map_goods_point_table_row)
        self._button_del_map_goods_point_row.clicked.connect(
            self.del_map_goods_point_table_row)
        self._button_save_map_goods_point_table.clicked.connect(
            self.save_map_goods_point_table)

        self.init_table()

    def init_table(self):
        self._table_map_goods_point.setHorizontalHeaderItem(
            0, QtWidgets.QTableWidgetItem("路线名"))
        for column in range(1, self._table_map_goods_point.columnCount()):
            self._table_map_goods_point.setHorizontalHeaderItem(
                column, QtWidgets.QTableWidgetItem(f"坐标 {column}"))

        for row in range(self._table_map_goods_point.rowCount()):
            self.set_cell_data(row, 0)
        self.update_button_column()

    def add_new_column(self):
        """在按钮列之前插入新的坐标列。"""
        new_column = self._table_map_goods_point.columnCount()
        self._table_map_goods_point.setColumnCount(new_column + 1)

        for row in range(self._table_map_goods_point.rowCount()):
            self.set_cell_data(row, new_column - 1)

        self.update_button_column()
        for column in range(1, self._table_map_goods_point.columnCount()):
            self._table_map_goods_point.setHorizontalHeaderItem(
                column, QtWidgets.QTableWidgetItem(f"坐标 {column}"))

    def set_cell_data(self, row: int, column: int):
        if column != 0:
            return
        item = QtWidgets.QTableWidgetItem(f"路线{row + 1}")
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._table_map_goods_point.setItem(row, column, item)

    def load_map_goods_point_table(self):
        """把配置文件中的路线加载到表格。"""
        point_list = get_map_goods_point_list()

        row_index = 0
        for point_dict in point_list:
            if self._table_map_goods_point.rowCount() - 1 < row_index:
                self.add_map_goods_point_table_row()

            line_name = point_dict.get("line_name")
            line_points = point_dict.get("map_point") or []

            item = QtWidgets.QTableWidgetItem(line_name)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._table_map_goods_point.setItem(row_index, 0, item)

            for point_index, point in enumerate(line_points):
                if self._table_map_goods_point.columnCount() - 2 == point_index:
                    self.add_new_column()
                point_item = QtWidgets.QTableWidgetItem(point)
                point_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._table_map_goods_point.setItem(
                    row_index, point_index + 1, point_item)
            row_index += 1

        self._update_combox_map_goods_point()

    def del_map_goods_point_table_row(self):
        """删除当前选中的路线行。"""
        selected_row = self._table_map_goods_point.currentRow()
        if selected_row < 0 or not self._table_map_goods_point.selectedItems():
            QtWidgets.QMessageBox.information(self, '提示', "请选择需要删除路线")
            return False
        self._table_map_goods_point.removeRow(selected_row)
        self._update_combox_map_goods_point()
        return True

    def add_map_goods_point_table_row(self):
        """新增一行路线；有选中行时插入到选中行之后。"""
        selected_row = self._table_map_goods_point.currentRow() + 1
        if not self._table_map_goods_point.selectedItems():
            selected_row = self._table_map_goods_point.rowCount()
        self._table_map_goods_point.insertRow(selected_row)

        item = QtWidgets.QTableWidgetItem(f"路线{selected_row + 1}")
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._table_map_goods_point.setItem(selected_row, 0, item)
        self.update_button_column()

    def update_button_column(self):
        """把“添加列”按钮放到最后一列。"""
        last_column = self._table_map_goods_point.columnCount() - 1

        for row in range(self._table_map_goods_point.rowCount()):
            if self._table_map_goods_point.cellWidget(row, last_column - 1):
                self._table_map_goods_point.removeCellWidget(row, last_column - 1)

        for row in range(self._table_map_goods_point.rowCount()):
            button = QtWidgets.QPushButton("添加列")
            button.clicked.connect(self.add_new_column)
            self._table_map_goods_point.setCellWidget(row, last_column, button)

    @staticmethod
    def __show_dialog(tips: str):
        QtWidgets.QMessageBox.information(None, '提示', tips)

    def __check_table_map_point_line_name(self) -> bool:
        """检查路线名是否重复。"""
        line_name_list: list[str] = []
        for row in range(self._table_map_goods_point.rowCount()):
            item = self._table_map_goods_point.item(row, 0)
            if item is None:
                continue
            line_name = item.text()
            if line_name in line_name_list:
                self.__show_dialog(f"路线名: {line_name} 已经存在")
                return False
            line_name_list.append(line_name)
        return True

    def save_map_goods_point_table(self):
        """保存表格内容到配置文件。"""
        if not self.__check_table_map_point_line_name():
            return None

        current_line = self._combo_box_goods_point_selected.currentText()
        map_point_list: list[dict] = []

        for row in range(self._table_map_goods_point.rowCount()):
            line_name = ""
            point_list: list[str] = []
            line_dict: dict = {}

            for column in range(self._table_map_goods_point.columnCount() - 1):
                item = self._table_map_goods_point.item(row, column)
                if item is None:
                    continue
                content = item.text()

                if column == 0:
                    line_name = content
                    line_dict["line_name"] = line_name
                    line_dict["selected"] = current_line == line_name
                    continue

                if content == "":
                    continue

                # 兼容用户输入了错误的分隔符
                for separator in ('.', '，', '。', '/'):
                    content = content.replace(separator, ',')

                if content.count(",") > 1:
                    self.__show_dialog(
                        f"坐标 {content} 输入错误,请按照格式 例如: 100,231 输入到表格中")
                    return None

                point_x, point_y = content.split(",")
                if point_x == "" or point_y == "":
                    self.__show_dialog(
                        f"坐标 {content} 输入错误,请按照格式 例如: 100,231 输入到表格中")
                    return None
                point_list.append(content)

            if not point_list:
                continue

            line_dict["map_point"] = point_list
            map_point_list.append(line_dict)

            if line_name == "":
                self.__show_dialog("路线名不能为空")
                return None

        update_map_goods_point_list(map_point_list)
        self.__show_dialog("保存成功,请重启脚本")
        return None

    def _update_combox_map_goods_point(self):
        """同步路线名下拉框，并恢复配置文件中的选中路线。"""
        line_name_list: list[str] = []
        for row in range(self._table_map_goods_point.rowCount()):
            item = self._table_map_goods_point.item(row, 0)
            if item is None:
                continue
            if item.text() not in line_name_list:
                line_name_list.append(item.text())

        self._combo_box_goods_point_selected.clear()
        self._combo_box_goods_point_selected.addItems(line_name_list)

        for point_dict in get_map_goods_point_list():
            if point_dict.get("selected") is True:
                line_name = point_dict.get("line_name")
                if line_name in line_name_list:
                    self._combo_box_goods_point_selected.setCurrentText(line_name)
