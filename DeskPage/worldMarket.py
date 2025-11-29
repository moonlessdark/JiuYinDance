import json
import os
import sys
from uu import decode

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                               QPushButton, QHBoxLayout, QMessageBox, QHeaderView, QApplication, QTableWidgetItem,
                               QLineEdit, QLabel, QDialog, QTextEdit)

from DeskFunc.TaskBussinese.findAuctionMarket import FindAuctionMarket


class AutoWorldMarket(QWidget):

    """
    世界竞拍的表格
    """

    def __init__(self):

        super().__init__()

        self.setWindowTitle("世界竞拍价格设置")

        self.list_widget_market = QtWidgets.QTableWidget(0, 3)
        self.list_widget_market.resizeColumnsToContents()  # 自适应列宽

        self.resize(375, 400)
        self.setFixedWidth(375)

        # header = self.list_widget_market.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.setup_table_header_and_width()

        _scan_product_num = QtWidgets.QLabel("每次只扫描前")
        self.scan_product_num_select = QtWidgets.QComboBox()
        self.scan_product_num_select.addItems("1234567")
        self.scan_product_num_select.setCurrentIndex(1)  # 默认选中数量 2
        _scan_product_num_end_str = QtWidgets.QLabel("个物品")
        layout_product_num_select = QHBoxLayout()
        layout_product_num_select.addWidget(_scan_product_num)
        layout_product_num_select.addWidget(self.scan_product_num_select)
        layout_product_num_select.addWidget(_scan_product_num_end_str)
        self.push_button_market_reset_product_price = QtWidgets.QPushButton("重置价格")
        self.push_button_market_save_product_price = QtWidgets.QPushButton("保存价格")

        self.push_button_market_reset_product_price.clicked.connect(self.clear_all_price)
        self.push_button_market_save_product_price.clicked.connect(self.save_product_price_to_json)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.push_button_market_reset_product_price)
        layout_button.addWidget(self.push_button_market_save_product_price)
        layout_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        _lay_out_top = QHBoxLayout()
        _lay_out_top.addLayout(layout_product_num_select)
        _lay_out_top.addLayout(layout_button)

        layout = QVBoxLayout(self)
        layout.addLayout(_lay_out_top)
        layout.addWidget(self.list_widget_market)
        layout.setContentsMargins(5, 5, 5 , 5)

    def setup_table_header_and_width(self):
        """在创建表格时立即设置表头和固定宽度"""
        # 设置表头标签
        headers = ["物品名", "最小竞拍价格", "最大竞拍价格"]
        self.list_widget_market.setHorizontalHeaderLabels(headers)

        # 获取水平表头
        header = self.list_widget_market.horizontalHeader()

        # 设置固定列宽
        self.list_widget_market.setColumnWidth(0, 130)  # 第一列固定200像素
        self.list_widget_market.setColumnWidth(1, 100)  # 第二列固定150像素
        self.list_widget_market.setColumnWidth(2, 100)  # 第二列固定150像素

        # 设置列宽调整模式为固定
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)

        # 可选：禁用用户调整列宽
        header.setSectionsMovable(False)

        # 可选：设置最小和最大宽度限制
        header.setMinimumSectionSize(50)
        header.setMaximumSectionSize(300)

    def add_table(self, product_list: list):
        """
        设置表格
        """
        self.list_widget_market.clearContents()  # 先清理一下
        self.list_widget_market.setRowCount(0)  # 删除所有表格

        for product_dict in product_list:

            row_next: int = self.list_widget_market.rowCount()  # 获取一下当前的row
            self.list_widget_market.setRowCount(row_next + 1)  # 插入下一列,便于存入内容

            # 把物品名放进去
            item = QTableWidgetItem(product_dict["product_name"])
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.list_widget_market.setItem(row_next, 0, item)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)  # 商品名称禁止编辑

            # 把产品起始竞拍价格放进去
            min_prince_input = QtWidgets.QLineEdit()
            min_prince_input.setPlaceholderText("单位为“两”")
            validator = QIntValidator(1, 999999, min_prince_input)
            min_prince_input.setValidator(validator)
            self.list_widget_market.setCellWidget(row_next, 1, min_prince_input)
            if product_dict["min_price"] != "":
                min_prince_input.setText(product_dict["min_price"])


            # 把产品最大价格放进去
            max_prince_input = QtWidgets.QLineEdit()
            max_prince_input.setPlaceholderText("单位为“两”")
            validator = QIntValidator(1, 999999, max_prince_input)
            max_prince_input.setValidator(validator)
            self.list_widget_market.setCellWidget(row_next, 2, max_prince_input)
            if product_dict["max_price"] != "":
                max_prince_input.setText(product_dict["max_price"])

    def get_table_content(self) -> list:
        """
        获取表格中的内容
        """
        _table_content: list = []
        for row in range(self.list_widget_market.rowCount()):
            item_name = self.get_cell_value(row, 0)  # 产品名称
            item_min_price = self.get_cell_value(row, 1)  # 竞拍起始价格
            item_max_price = self.get_cell_value(row, 2)  # 最大竞拍价格
            _price_dict: dict = {
                "product_name": item_name,
                "min_price": item_min_price,
                "max_price": item_max_price
            }
            _table_content.append(_price_dict)
        return _table_content

    def get_cell_value(self, row, col):
        """获取单个单元格的值，支持QTableWidgetItem和QLineEdit"""

        # 首先检查是否为QLineEdit组件
        widget = self.list_widget_market.cellWidget(row, col)
        if widget and isinstance(widget, QLineEdit):
            return widget.text()

        # 如果不是组件，则检查是否为QTableWidgetItem
        item = self.list_widget_market.item(row, col)
        if item is not None:
            return item.text()
        # 如果既不是组件也不是item，返回None
        return None

    def load_product_price(self):
        """
        加载本地的价格配置
        """
        config_file: str = '.\\_internal\\Resources\\'
        if not os.path.exists(config_file):  # 如果主目录+小时+分钟这个文件路径不存在的话
            config_file = ".\\Resources\\"
        config_file = config_file + 'worldMarketPrice.json'
        _file: list = []
        _read_json = None
        with open(config_file, 'r', encoding='utf-8') as file:
            _read_json = file.read()
            if _read_json != "":
                _file = list(json.loads(_read_json))
        _add_product_list: list = []
        _product_list: list = FindAuctionMarket().product_list
        for _p in _product_list:
            _product_name: str = _p[0]  # 产品名

            exists = any(item["product_name"] == _product_name for item in _file)
            if exists:
                continue
            new_product: dict = {
              "product_name": _product_name,
              "min_price": "",
              "max_price": ""
            }
            _add_product_list.append(new_product)
        _file = _file + _add_product_list
        self.add_table(_file)

    def save_product_price_to_json(self):
        config_file: str = '.\\_internal\\Resources\\'
        if not os.path.exists(config_file):  # 如果主目录+小时+分钟这个文件路径不存在的话
            config_file = ".\\Resources\\"
        config_file = config_file + 'worldMarketPrice.json'
        table_data: list = self.get_table_content()
        with open(config_file, 'w', encoding='utf-8') as save_file:
            json.dumps(table_data, ensure_ascii=False, indent=4)
            save_file.write(json.dumps(table_data, ensure_ascii=False, indent=4))
        msg_box = QMessageBox(self)
        msg_box.setText("保存成功!")
        msg_box.setWindowTitle("信息")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.show()

    def clear_all_price(self):
        """
        清理所有价格设置
        """
        for row in range(self.list_widget_market.rowCount()):
            for line_row in range(1, 3):
                widget = self.list_widget_market.cellWidget(row, line_row)
                if widget and isinstance(widget, QLineEdit):
                    widget.setText("")
        msg_box = QMessageBox(self)
        msg_box.setText("价格重置成功!")
        msg_box.setWindowTitle("信息")
        msg_box.setIcon(QMessageBox.Information)

    def show_help(self):
        """
        显示帮助说明
        """

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AutoWorldMarket()
    w.add_table(["星河剑律残破星图", "若水神典拓本碎片", "若水神典","星河剑律残破星图", "若水神典拓本碎片", "若水神典", "若水神典拓本碎片", "若水神典","星河剑律残破星图", ])
    w.show()
    app.exec()
