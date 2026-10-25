# coding: utf-8
"""
世界竞拍价格设置窗口。

只负责展示/保存价格配置，物品清单来自 v2 auctionMarket 的模板字段定义，
不在界面层加载图片模板。
"""
import json
import os
import sys

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from Core.config.paths import PathUtil
from DeskFunc.v2.TaskBussinese.auctionMarket import get_product_names


class AutoWorldMarket(QWidget):
    """世界竞拍价格表格。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("世界竞拍价格设置")

        self.list_widget_market = QtWidgets.QTableWidget(0, 3)
        self.list_widget_market.resizeColumnsToContents()
        self.resize(375, 400)
        self.setFixedWidth(375)

        self.setup_table_header_and_width()

        label_scan_num = QtWidgets.QLabel("每次只扫描前")
        self.scan_product_num_select = QtWidgets.QComboBox()
        self.scan_product_num_select.addItems([str(index) for index in range(1, 8)])
        self.scan_product_num_select.setCurrentIndex(1)
        label_scan_num_end = QtWidgets.QLabel("个物品")

        layout_product_num_select = QHBoxLayout()
        layout_product_num_select.addWidget(label_scan_num)
        layout_product_num_select.addWidget(self.scan_product_num_select)
        layout_product_num_select.addWidget(label_scan_num_end)

        self.push_button_market_reset_product_price = QtWidgets.QPushButton("重置价格")
        self.push_button_market_save_product_price = QtWidgets.QPushButton("保存价格")
        self.push_button_market_reset_product_price.clicked.connect(self.clear_all_price)
        self.push_button_market_save_product_price.clicked.connect(
            self.save_product_price_to_json)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.push_button_market_reset_product_price)
        layout_button.addWidget(self.push_button_market_save_product_price)
        layout_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        layout_top = QHBoxLayout()
        layout_top.addLayout(layout_product_num_select)
        layout_top.addLayout(layout_button)

        layout = QVBoxLayout(self)
        layout.addLayout(layout_top)
        layout.addWidget(self.list_widget_market)
        layout.setContentsMargins(5, 5, 5, 5)

    def setup_table_header_and_width(self):
        headers = ["物品名", "最小竞拍价格", "最大竞拍价格"]
        self.list_widget_market.setHorizontalHeaderLabels(headers)

        header = self.list_widget_market.horizontalHeader()
        self.list_widget_market.setColumnWidth(0, 130)
        self.list_widget_market.setColumnWidth(1, 100)
        self.list_widget_market.setColumnWidth(2, 100)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionsMovable(False)
        header.setMinimumSectionSize(50)
        header.setMaximumSectionSize(300)

    def add_table(self, product_list: list[dict]):
        """用价格配置填充表格。"""
        self.list_widget_market.clearContents()
        self.list_widget_market.setRowCount(0)

        for product_dict in product_list:
            row = self.list_widget_market.rowCount()
            self.list_widget_market.setRowCount(row + 1)

            item = QTableWidgetItem(product_dict["product_name"])
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.list_widget_market.setItem(row, 0, item)

            min_price_input = QtWidgets.QLineEdit()
            min_price_input.setPlaceholderText("单位为“两”")
            min_price_input.setValidator(QIntValidator(1, 999999, min_price_input))
            self.list_widget_market.setCellWidget(row, 1, min_price_input)
            if product_dict["min_price"] != "":
                min_price_input.setText(product_dict["min_price"])

            max_price_input = QtWidgets.QLineEdit()
            max_price_input.setPlaceholderText("单位为“两”")
            max_price_input.setValidator(QIntValidator(1, 999999, max_price_input))
            self.list_widget_market.setCellWidget(row, 2, max_price_input)
            if product_dict["max_price"] != "":
                max_price_input.setText(product_dict["max_price"])

    def get_table_content(self) -> list[dict]:
        """读取表格中的价格配置。"""
        table_content: list[dict] = []
        for row in range(self.list_widget_market.rowCount()):
            table_content.append({
                "product_name": self.get_cell_value(row, 0),
                "min_price": self.get_cell_value(row, 1),
                "max_price": self.get_cell_value(row, 2),
            })
        return table_content

    def get_cell_value(self, row: int, col: int):
        """兼容 QLineEdit 和 QTableWidgetItem 两种单元格。"""
        widget = self.list_widget_market.cellWidget(row, col)
        if widget and isinstance(widget, QLineEdit):
            return widget.text()
        item = self.list_widget_market.item(row, col)
        return item.text() if item is not None else None

    @staticmethod
    def _price_file_path() -> str:
        return PathUtil().get_path_from_resources("worldMarketPrice.json")

    def load_product_price(self):
        """加载本地价格配置，并补齐新增物品。"""
        config_file = self._price_file_path()
        saved_list: list[dict] = []
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as file:
                content = file.read()
                if content.strip():
                    saved_list = list(json.loads(content))

        existing_names = {item.get("product_name") for item in saved_list}
        missing_products = [
            {"product_name": name, "min_price": "", "max_price": ""}
            for name in get_product_names()
            if name not in existing_names
        ]
        self.add_table(saved_list + missing_products)

    def save_product_price_to_json(self):
        """保存价格配置到本地。"""
        table_data = self.get_table_content()
        with open(self._price_file_path(), 'w', encoding='utf-8') as save_file:
            save_file.write(json.dumps(table_data, ensure_ascii=False, indent=4))

        msg_box = QMessageBox(self)
        msg_box.setText("保存成功!")
        msg_box.setWindowTitle("信息")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()

    def clear_all_price(self):
        """清空表格中的价格输入，不删除本地文件。"""
        for row in range(self.list_widget_market.rowCount()):
            for column in range(1, 3):
                widget = self.list_widget_market.cellWidget(row, column)
                if widget and isinstance(widget, QLineEdit):
                    widget.setText("")

        msg_box = QMessageBox(self)
        msg_box.setText("价格重置成功!")
        msg_box.setWindowTitle("信息")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AutoWorldMarket()
    window.load_product_price()
    window.show()
    app.exec()
