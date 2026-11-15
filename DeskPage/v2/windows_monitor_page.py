# coding: utf-8
"""
游戏窗口展示与选择。

每行固定 3 个窗口自动换行，窗口过多时出现滚动条，避免主界面被撑宽。
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QGridLayout, QScrollArea, QWidget
from PySide6 import QtWidgets

_COLUMNS_PER_ROW = 3
_CHECKBOX_HEIGHT = 26
_MAX_SCROLL_HEIGHT = 86


class MonitorWindowsPage(QWidget):
    """窗口复选框容器。"""

    def __init__(self, items: list = None):
        super().__init__()
        self._checkboxes: list[QCheckBox] = []

        self._grid_layout = QGridLayout(self)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(6)
        self._grid_layout.setVerticalSpacing(2)
        # 水平方向不设对齐，让布局占满可用宽度，首尾伸缩列才能把内容推到中间
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # 首尾各留一个可伸缩列，让复选框整体水平居中
        self._grid_layout.setColumnStretch(0, 1)
        self._grid_layout.setColumnStretch(_COLUMNS_PER_ROW + 1, 1)

        if items:
            self.update_checkboxes(items)

    def clear_checkboxes(self):
        for checkbox in self._checkboxes:
            self._grid_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self._checkboxes.clear()

    def update_checkboxes(self, items: list):
        self.clear_checkboxes()
        for index, item in enumerate(items):
            checkbox = QCheckBox(str(item), self)
            checkbox.setChecked(True)
            row = index // _COLUMNS_PER_ROW
            column = index % _COLUMNS_PER_ROW + 1
            self._grid_layout.addWidget(checkbox, row, column)
            self._checkboxes.append(checkbox)

    def get_checked(self) -> list[str]:
        return [checkbox.text() for checkbox in self._checkboxes if checkbox.isChecked()]

    def get_row_count(self) -> int:
        if not self._checkboxes:
            return 0
        return (len(self._checkboxes) + _COLUMNS_PER_ROW - 1) // _COLUMNS_PER_ROW

    def set_enabled_all(self, enabled: bool):
        for checkbox in self._checkboxes:
            checkbox.setEnabled(enabled)


class WindowsButton(QWidget):
    """获取窗口、测试窗口、开始执行。"""

    def __init__(self):
        super().__init__()

        self.push_button_get_windows = QtWidgets.QPushButton("获取窗口", self)
        self.push_button_test_windows = QtWidgets.QPushButton("测试窗口", self)
        self.push_button_run_windows = QtWidgets.QPushButton("开始执行", self)
        self.push_button_run_windows.setFixedHeight(40)
        self.push_button_test_windows.setFixedHeight(40)
        self.push_button_get_windows.setFixedHeight(40)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.push_button_get_windows)
        button_layout.addWidget(self.push_button_test_windows)
        button_layout.addWidget(self.push_button_run_windows)

        self.__tips_label_game_windows_is_None = QtWidgets.QLabel("未发现游戏窗口")

        self._monitor_page = MonitorWindowsPage()
        self._monitor_scroll = QScrollArea(self)
        self._monitor_scroll.setWidgetResizable(True)
        self._monitor_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._monitor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._monitor_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._monitor_scroll.setWidget(self._monitor_page)
        self._monitor_scroll.hide()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addLayout(button_layout)
        layout.addWidget(self._monitor_scroll)
        layout.addWidget(self.__tips_label_game_windows_is_None,
                         alignment=Qt.AlignmentFlag.AlignCenter)

    def get_windows(self, hwnd_list: list):
        """渲染窗口列表。"""
        game_windows = list(hwnd_list)
        if not game_windows:
            self._monitor_page.clear_checkboxes()
            self._monitor_scroll.hide()
            self.__tips_label_game_windows_is_None.show()
            return

        self._monitor_page.update_checkboxes(game_windows)
        rows = self._monitor_page.get_row_count()
        scroll_height = min(rows * _CHECKBOX_HEIGHT + 8, _MAX_SCROLL_HEIGHT)
        self._monitor_scroll.setFixedHeight(scroll_height)
        self._monitor_scroll.show()
        self.__tips_label_game_windows_is_None.hide()

    def get_windows_checked(self) -> list[str]:
        return self._monitor_page.get_checked()

    def set_windows_enabled(self, enabled: bool):
        self._monitor_page.set_enabled_all(enabled)


if __name__ == "__main__":
    app = QApplication([])
    window = WindowsButton()
    window.get_windows([f"窗口:{index + 1}" for index in range(8)])
    window.show()
    app.exec()
