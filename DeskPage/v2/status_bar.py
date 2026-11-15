# coding: utf-8
"""
底部状态栏：左侧时间、中间跑马灯、右侧执行次数。
"""
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar


class StatusBarProcess(QtWidgets.QStatusBar):
    """底部状态栏。"""

    def __init__(self):
        super().__init__()

        self.status_bar_label_left = QtWidgets.QLabel(
            QtCore.QTime.currentTime().toString('HH:mm:ss'))
        self.progress_time = QtCore.QTimer(self)
        self.progress_time.timeout.connect(self.update_time)
        self.progress_time.start(1000)
        self.addWidget(self.status_bar_label_left, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setInvertedAppearance(False)
        self.progress_bar.setOrientation(Qt.Orientation.Horizontal)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet(
            "QProgressBar::chunk { background-color: #05B8CC; }")
        self.addWidget(self.progress_bar, stretch=3)

        self.status_bar_label_right = QtWidgets.QLabel()
        self.update_execute_num(0)
        self.status_bar_label_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.addWidget(self.status_bar_label_right, stretch=1)

        self.setContentsMargins(8, 0, 0, 0)

    def update_time(self):
        self.status_bar_label_left.setText(
            QtCore.QTime.currentTime().toString('HH:mm:ss'))

    def update_execute_num(self, e_num: int):
        """右下角显示识别/执行次数。"""
        self.status_bar_label_right.setText(f"一共识别了 {e_num} 轮")

    def run_status(self, status: bool):
        """任务执行时显示跑马灯。"""
        self.progress_bar.setVisible(status)
