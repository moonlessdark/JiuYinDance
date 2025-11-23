import sys

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (QWidget, QVBoxLayout,
                               QPushButton, QHBoxLayout, QMessageBox, QHeaderView, QApplication, QTableWidgetItem,
                               QLineEdit)


class AutoWorldMarket(QWidget):

    """
    世界竞拍的表格
    """

    def __init__(self):

        super().__init__()

        self.setWindowTitle("世界竞拍")

        self.list_widget_market = QtWidgets.QTableWidget(1, 2)
        self.list_widget_market.resizeColumnsToContents()  # 自适应列宽
        # 设置水平表头标签
        headers = ["物品名", "最大竞拍价格"]
        self.list_widget_market.setHorizontalHeaderLabels(headers)

        self.resize(310, 300)
        self.setFixedWidth(310)


        # header = self.list_widget_market.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.setup_table_header_and_width()

        self.push_button_market_get_goods_list = QtWidgets.QPushButton("获取物品")
        self.push_button_market_run_buy = QtWidgets.QPushButton("开始运行")

        self.push_button_market_run_buy.clicked.connect(self.get_table_content)

        layout_button = QHBoxLayout()
        layout_button.addWidget(self.push_button_market_get_goods_list)
        layout_button.addWidget(self.push_button_market_run_buy)
        layout_button.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout = QVBoxLayout(self)
        layout.addLayout(layout_button)
        layout.addWidget(self.list_widget_market)
        layout.setContentsMargins(5, 5, 5 , 5)

    def setup_table_header_and_width(self):
        """在创建表格时立即设置表头和固定宽度"""
        # 设置表头标签
        headers = ["物品名", "最大竞拍价格"]
        self.list_widget_market.setHorizontalHeaderLabels(headers)

        # 获取水平表头
        header = self.list_widget_market.horizontalHeader()

        # 设置固定列宽
        self.list_widget_market.setColumnWidth(0, 130)  # 第一列固定200像素
        self.list_widget_market.setColumnWidth(1, 130)  # 第二列固定150像素

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

        for product_index in range(len(product_list)):
            self.list_widget_market.setRowCount(product_index+1)  # 加一列，便于放入内容
            # 把物品名放进去
            item = QTableWidgetItem(product_list[product_index])
            self.list_widget_market.setItem(product_index, 0, item)

            # 把产品最大价格放进去
            max_prince_input = QtWidgets.QLineEdit()
            max_prince_input.setPlaceholderText("单位为“两”")
            validator = QIntValidator(1, 999999, max_prince_input)
            max_prince_input.setValidator(validator)
            self.list_widget_market.setCellWidget(product_index, 1, max_prince_input)


    def get_table_content(self) -> list:
        _table_content: list = []
        for row in range(self.list_widget_market.rowCount()):
            item_name = self.get_cell_value(row, 0)
            item_price = self.get_cell_value(row, 1)

            if None in [item_name, item_price]:
                continue
            _table_content.append([item_name, item_price])
        print(_table_content)
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AutoWorldMarket()
    w.add_table(["星河剑律残破星图", "若水神典拓本碎片", "若水神典","星河剑律残破星图", "若水神典拓本碎片", "若水神典", "若水神典拓本碎片", "若水神典","星河剑律残破星图", ])
    w.show()
    app.exec()
