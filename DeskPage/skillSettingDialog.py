from PySide6 import QtWidgets, QtCore

from Utils.loadResources import GetConfig, get_skill_group_list, update_skill_group_list


class SkillSetting(QtWidgets.QDialog):
    """
    技能设置
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._skill_config = GetConfig()

        self.setWindowTitle("设置技能")
        self.setFixedSize(530, 260)
        self._skill_table = QtWidgets.QTableWidget(self)
        self._skill_table.setRowCount(1)
        self._skill_table.setColumnCount(5)
        __widget = QtWidgets.QWidget()
        self._button_add_skill_table_row = QtWidgets.QPushButton("新增")
        self._button_del_skill_table_row = QtWidgets.QPushButton("删除")
        self._button_save_skill_table = QtWidgets.QPushButton("保存")

        self._skill_selected = QtWidgets.QComboBox()  # 当前选中的是什么技能
        self._button_add_skill_group_name = QtWidgets.QPushButton("新增")
        self._button_edit_skill_group_name = QtWidgets.QPushButton("编辑")
        self._button_del_skill_group_name = QtWidgets.QPushButton("删除")

        self._button_add_skill_group_name.setFixedWidth(35)
        self._button_edit_skill_group_name.setFixedWidth(35)
        self._button_del_skill_group_name.setFixedWidth(35)

        __lay_table_ui_button = QtWidgets.QHBoxLayout()
        __lay_table_ui_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        __lay_table_ui_button.addWidget(self._button_add_skill_table_row)
        __lay_table_ui_button.addWidget(self._button_del_skill_table_row)
        __lay_table_ui_button.addWidget(self._button_save_skill_table)
        __lay_table_ui_button.setSpacing(1)

        __lay_table_combox_ui_button = QtWidgets.QHBoxLayout()
        __lay_table_combox_ui_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        __lay_table_combox_ui_button.addWidget(self._skill_selected)
        __lay_table_combox_ui_button.addWidget(self._button_add_skill_group_name)
        __lay_table_combox_ui_button.addWidget(self._button_edit_skill_group_name)
        __lay_table_combox_ui_button.addWidget(self._button_del_skill_group_name)
        __lay_table_combox_ui_button.setSpacing(1)

        __lay_table_ui_button_line = QtWidgets.QHBoxLayout(__widget)
        __lay_table_ui_button_line.addLayout(__lay_table_combox_ui_button)
        # 添加分割线
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setLineWidth(1)  # 设置线条宽度
        # 添加最小高度确保分割线可见
        separator.setMinimumHeight(20)
        __lay_table_ui_button_line.addStretch(1)
        __lay_table_ui_button_line.addWidget(separator)
        __lay_table_ui_button_line.addStretch(1)

        __lay_table_ui_button_line.addLayout(__lay_table_ui_button)
        __lay_table_ui_button_line.setSpacing(1)

        __lay_table_ui = QtWidgets.QVBoxLayout(self)
        __lay_table_ui.addWidget(__widget)
        __lay_table_ui.addWidget(self._skill_table)
        __lay_table_ui.setSpacing(2)
        __lay_table_ui.setContentsMargins(5, 5, 5, 5)

        self._button_add_skill_table_row.clicked.connect(self.add_skill_table_row)
        self._button_del_skill_table_row.clicked.connect(self.del_skill_table_row)
        self._button_save_skill_table.clicked.connect(self.save_skill_table)

        self._skill_selected.currentTextChanged.connect(self._show_table)

        self.load_skill_group()

    def del_skill_table_row(self):
        """
        删除行，需要选中具体的行
        :return:
        """
        selected_row = self._skill_table.currentRow()
        if selected_row == 0 and not self._skill_table.selectedItems():
            QtWidgets.QMessageBox.information(self, '提示', "请选择需要删除的技能")
            return False
        self._skill_table.removeRow(selected_row)
        return True

    def load_skill_group(self):
        """
        加载技能组
        :return:
        """
        skill_group_list: dict = get_skill_group_list()
        self._skill_selected.clear()
        for skill_group in skill_group_list:
            self._skill_selected.addItem(skill_group)

    def add_skill_table_row(self):
        """
        新增行
        如果没有选择制定的行，那么就插入在最后面
        :return:
        """
        selected_row = self._skill_table.currentRow() + 1
        if not self._skill_table.selectedItems():
            selected_row = self._skill_table.rowCount()
        self._skill_table.insertRow(selected_row)

    def _show_table(self, skill_group_name: str):
        """
        显示技能表格
        """
        _skill_obj: dict = get_skill_group_list().get(skill_group_name)  # 当前正在使用的技能组

        self._skill_table.clear()
        self._skill_table.setHorizontalHeaderLabels(['技能名', '技能冷却(秒)', '释放时间(秒)', '释放优先级', '键盘Key'])

        row_index: int = 0
        for skill_name in _skill_obj:
            if self._skill_table.rowCount() < row_index + 1:
                self._skill_table.insertRow(self._skill_table.rowCount())

            # 技能名称
            item = QtWidgets.QTableWidgetItem(str(skill_name).format(row_index, 1))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self._skill_table.setItem(row_index, 0, QtWidgets.QTableWidgetItem(item))

            _skill: dict = _skill_obj.get(skill_name)
            # 技能CD
            if _skill.get("CD") is not None:
                column_index: int = 1
                item = QtWidgets.QTableWidgetItem(str(_skill.get("CD")).format(row_index, column_index))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._skill_table.setItem(row_index, column_index, QtWidgets.QTableWidgetItem(item))

            # 技能释放时间
            if _skill.get("active_cd") is not None:
                column_index: int = 2
                item = QtWidgets.QTableWidgetItem(str(_skill.get("active_cd")).format(row_index, column_index))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._skill_table.setItem(row_index, column_index, QtWidgets.QTableWidgetItem(item))
            # 技能释放优先级
            if _skill.get("level") is not None:
                column_index: int = 3
                item = QtWidgets.QTableWidgetItem(str(_skill.get("level")).format(row_index, column_index))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._skill_table.setItem(row_index, column_index, QtWidgets.QTableWidgetItem(item))
            # 技能释放优先级
            if _skill.get("key") is not None:
                column_index: int = 4
                item = QtWidgets.QTableWidgetItem(str(_skill.get("key")).format(row_index, column_index))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self._skill_table.setItem(row_index, column_index, QtWidgets.QTableWidgetItem(item))
            row_index += 1

    def load_skill_table(self):
        """
        加载文件中的打怪套路设置
        :return:
        """
        skill_group_name: str = self._skill_selected.currentText()
        self._show_table(skill_group_name)

    def save_skill_table(self):
        """
        保存技能设置
        保存/更新的是当前页面渲染的group_name和表格中的内容，其他的内容不要变保留原样
        """
        # 获取当前选中的技能组名称
        current_group_name = self._skill_selected.currentText()

        # 获取原有的所有技能组数据
        all_skill_groups = get_skill_group_list()

        # 构建当前表格中的技能数据
        current_skill_dict = {}
        for row in range(self._skill_table.rowCount()):
            _skill_name: str = ""
            _skill_cd: int = 0
            _skill_active_cd: float = 0.0
            _skill_level: int = 0
            _skill_key: str = ""

            for col in range(self._skill_table.columnCount()):
                item = self._skill_table.item(row, col)
                if item and item.text():  # 检查item是否存在且有文本
                    __content = item.text()
                    if col == 0:
                        _skill_name = __content
                    elif col == 1:
                        _skill_cd = int(__content)
                    elif col == 2:
                        _skill_active_cd = float(__content)
                    elif col == 3:
                        _skill_level = int(__content)
                    elif col == 4:
                        _skill_key = __content

            # 只有当技能名称不为空时才添加
            if _skill_name:
                current_skill_dict[str(_skill_name)] = {
                    "CD": _skill_cd,
                    "active_cd": _skill_active_cd,
                    "level": _skill_level,
                    "key": _skill_key
                }

        # 更新当前技能组的数据
        all_skill_groups[current_group_name] = current_skill_dict

        # 保存所有技能组数据
        update_skill_group_list(_skill_dict=all_skill_groups)
        QtWidgets.QMessageBox.information(self, '提示', "保存成功,请重启脚本!")


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_gui = SkillSetting()
    main_gui.show()
    sys.exit(app.exec())
