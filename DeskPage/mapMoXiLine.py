import os
import sys

from PySide6 import QtWidgets
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QPainter, QPen, QPixmap, QColor, QFont
from PySide6.QtCore import Qt, QPoint

from DeskFunc.TaskBussinese.findMoXiTreasureHuntingLine import MoXiMapLine


class QuadrantChart(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.func_mo_xi = MoXiMapLine()  # 把业务模块引入进来

        self.move_btn_3 = None
        self.move_btn_4 = None
        self.move_btn_1 = None  # 第一象限的按钮
        self.move_btn_2 = None
        self.move_btn_5 = None

        self.setWindowTitle('漠西风涛-挖宝指引')

        screen = QApplication.primaryScreen()
        # 获取屏幕的分辨率
        geometry = screen.geometry()
        width: int = geometry.width()
        height: int = geometry.height()

        print(f"width:{width} - height:{height}")

        # if height > 1440:
        #     # 如果是大于2K分辨率(1440P)的，窗口设置大一点
        #     _set_width: int = 932
        #     _set_height: int = 892
        #     # 地图原点(0,0)的位置
        #     _origin_x, _origin_y = 606, 312
        #     # 4个驿站坐标 马嵬驿、红尘、碧落、黄泉、精绝城
        #     self.sample_points = [
        #         (150, 146),   # 马嵬驿
        #         (-149, 195),  # 红尘
        #         (-242, -400),  # 碧落
        #         (85, -467),  # 黄泉
        #         (-10, -10)  # 精绝城
        #     ]
        if height >= 1440:
            # 如果是大于2K分辨率(1440P)的，窗口设置大一点
            _set_width: int = 928
            _set_height: int = 890
            # 地图原点(0,0)的位置
            _origin_x, _origin_y = 607, 304
            # 4个驿站坐标 马嵬驿、红尘、碧落、黄泉、精绝城
            self.sample_points = [
                (134, 138),   # 马嵬驿
                (-149, 183),  # 红尘
                (-245, -408),  # 碧落
                (82, -475),  # 黄泉
                (-20, -5)  # 精绝城
            ]

            self.button_point = [
                (756, 151),
                (470, 100),
                (371, 693),
                (701, 763),
                (630, 303)
            ]

        else:
            # 不然大概率是1080P分辨率的
            _set_width: int = 728
            _set_height: int = 690
            _origin_x, _origin_y = 476, 238
            # 4个驿站坐标 马嵬驿、红尘、碧落、黄泉、精绝城
            self.sample_points = [
                (105, 108), (-118, 144), (-190, -314), (66, -367), (-15, -3)
            ]
            self.button_point = [
                (590, 115),
                (370, 80),
                (195, 535),
                (553, 588),
                (482, 222)
            ]

        self.setFixedSize(_set_width, _set_height)
        config_file: str = '.\\_internal\\Resources\\ImageTemplate\\PicMoXi\\background.png'
        if not os.path.exists(config_file):
            config_file = ".\\Resources\\ImageTemplate\\PicMoXi\\background.png"
        # 背景图设置（需替换为实际图片路径）
        self.background = QPixmap(config_file).scaled(_set_width-2, _set_height-2,
                                                      Qt.AspectRatioMode.IgnoreAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)

        # 坐标系参数
        self.origin = QPoint(_origin_x, _origin_y)  # 固定原点位置
        self.quadrant_colors = [
            QColor(65, 105, 225),  # 第一象限-皇家蓝
            QColor(220, 20, 60),  # 第二象限-深红
            QColor(255, 140, 0),  # 第三象限-深橙
            QColor(50, 205, 50)  # 第四象限-酸橙绿
        ]

        # 新增功能相关变量
        self.all_lines = []  # 存储所有线条数据
        self.current_points = []  # 当前绘制的点
        self.move_line_index = -1  # 当前移动的线条索引

        # 创建顶部按钮布局
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(0, 40, 0, 0)
        self.setLayout(main_layout)

        # 顶部按钮布局
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # 添加功能按钮
        draw_btn = QPushButton("绘制坐标连线")
        draw_btn.clicked.connect(self.find_mini_map)
        button_layout.addWidget(draw_btn)
        draw_btn.setFixedHeight(30)

        # 移动线条按钮
        self.move_btn_1 = QPushButton(self)
        self.move_btn_1.setText("移动至马嵬驿")
        self.move_btn_1.clicked.connect(self.move_next_line)
        self.move_btn_1.setGeometry(self.button_point[0][0], self.button_point[0][1], 80, 30)

        self.move_btn_2 = QPushButton(self)
        self.move_btn_2.setText("移动至红尘")
        self.move_btn_2.clicked.connect(self.move_next_line)
        self.move_btn_2.setGeometry(self.button_point[1][0], self.button_point[1][1], 80, 30)

        self.move_btn_3 = QPushButton(self)
        self.move_btn_3.setText("移动至碧落")
        self.move_btn_3.clicked.connect(self.move_next_line)
        self.move_btn_3.setGeometry(self.button_point[2][0], self.button_point[2][1], 80, 30)

        self.move_btn_4 = QPushButton(self)
        self.move_btn_4.setText("移动至黄泉")
        self.move_btn_4.clicked.connect(self.move_next_line)
        self.move_btn_4.setGeometry(self.button_point[3][0], self.button_point[3][1], 80, 30)

        self.move_btn_5 = QPushButton(self)
        self.move_btn_5.setText("移动至精绝城")
        self.move_btn_5.clicked.connect(self.move_next_line)
        self.move_btn_5.setGeometry(self.button_point[4][0], self.button_point[4][1], 80, 30)

        # self.move_btn_1.setVisible(False)
        # self.move_btn_2.setVisible(False)
        # self.move_btn_3.setVisible(False)
        # self.move_btn_4.setVisible(False)
        # self.move_btn_5.setVisible(False)

        # 清除所有线条按钮
        clear_btn = QPushButton("清除所有线条")
        clear_btn.clicked.connect(self.clear_all_lines)
        button_layout.addWidget(clear_btn)
        clear_btn.setFixedHeight(30)

        main_layout.addLayout(button_layout)

    def _print_information(self, message_text: str):
        """
        打印一下信息
        :param message_text:
        :return:
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("消息提示")
        msg_box.setText(message_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def find_mini_map(self):
        """
        查询小地图
        :return:
        """
        _res_code, _point = self.func_mo_xi.get_game_windows_mini_map()
        if _res_code == 201:
            self._print_information("没有发现有窗口在漠西风涛地图")
        elif _res_code == 202:
            self._print_information("发现有多个窗口在漠西风涛地图")
        elif _res_code == 203:
            self._print_information("没有发现游戏窗口")
        else:
            _min_point, _max_point = _point[0], _point[1]
            self.draw_special_points([_min_point, _max_point])

    def draw_special_points(self, point_list: list):
        """
        画一下线条
        :param point_list:
        :return:
        """
        # 设置要绘制的坐标点 [(28, 37),(58, 62)]
        points = point_list
        self.current_points = points

        # 计算连线延长至窗口边缘的坐标
        x1, y1 = points[0]
        x2, y2 = points[1]

        # 计算直线方程 y = kx + b
        if x2 != x1:
            k = (y2 - y1) / (x2 - x1)
            b = y1 - k * x1

            # 计算与窗口左右边界的交点
            left_x = -self.origin.x()  # 窗口左边界x坐标(相对于原点)
            left_y = k * left_x + b

            right_x = self.width() - self.origin.x()  # 窗口右边界x坐标(相对于原点)
            right_y = k * right_x + b

            # 如果这个坐标点已经渲染在窗口中了，那么就提示一下
            for line in self.all_lines:
                if line.get("points") == points:
                    self._print_information(f"坐标:{points} 已经存在，请勿重复点击生成线条")
                    return None
            # 保存线条数据
            line_data = {
                'points': points,
                'extended_line': [(left_x, left_y), (right_x, right_y)],
                'moved': False,
                'color': QColor(200, 100, 200)  # 紫色
            }

            self.all_lines.append(line_data)
            self.update()
        # print(f"所有点位: {self.all_lines}")

    def move_next_line(self):
        sender = self.sender()
        move_to_point: tuple = (0, 0)
        if sender == self.move_btn_1:
            # 点击移动到第一象限
            move_to_point = self.sample_points[0]
        elif sender == self.move_btn_2:
            # 移动到第二象限
            move_to_point = self.sample_points[1]
        elif sender == self.move_btn_3:
            # 移动到第三象限
            move_to_point = self.sample_points[2]
        elif sender == self.move_btn_4:
            # 移动到第四象项
            move_to_point = self.sample_points[3]
        elif sender == self.move_btn_5:
            move_to_point = self.sample_points[4]

        # 找到下一条未移动的线条
        for i, line in enumerate(self.all_lines):
            if not line['moved']:
                self.move_line_to_target(i, move_to_point)
                # print(f"所有点位: {self.all_lines}")
                return

        # 如果所有线条都已移动，从第一条开始重新移动
        # if self.all_lines:
        #     self.moveLineToTarget(0)

    def move_line_to_target(self, line_index, move_to_point):
        if line_index < 0 or line_index >= len(self.all_lines):
            return

        line = self.all_lines[line_index]
        target_x, target_y = move_to_point[0], move_to_point[1]

        # 获取原始线条坐标
        x1, y1 = line['extended_line'][0]
        x2, y2 = line['extended_line'][1]

        # 计算直线方程 y = kx + b
        if x2 != x1:
            k = (y2 - y1) / (x2 - x1)
            b = y1 - k * x1

            # 计算需要移动的偏移量，使线条通过目标点
            required_b = target_y - k * target_x
            offset = required_b - b

            # 直接更新原始线条坐标
            line['extended_line'] = [
                (x1, y1 + offset),
                (x2, y2 + offset)
            ]
            line['moved'] = True
            line['color'] = QColor(100, 200, 200)  # 移动后改为青色

            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景图（居中显示）
        painter.drawPixmap(
            (self.width() - self.background.width()) // 2,
            (self.height() - self.background.height()) // 2,
            self.background
        )

        # 绘制坐标轴
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(0, self.origin.y(), self.width(), self.origin.y())  # X轴
        painter.drawLine(self.origin.x(), 0, self.origin.x(), self.height())  # Y轴

        # 绘制像素刻度线（每10像素一个次要刻度，每50像素一个主要刻度）
        self.draw_pixel_ticks(painter)

        # 标记象限区域
        self.draw_quadrant_labels(painter)

        # 绘制示例数据点
        self.draw_sample_points(painter)

        # 绘制所有线条
        self.draw_all_lines(painter)

    def draw_all_lines(self, painter):
        for line in self.all_lines:
            # 绘制原始点
            painter.setPen(QPen(line['color'], 2))
            painter.setBrush(Qt.white)

            for x, y in line['points']:
                px = self.origin.x() + x
                py = self.origin.y() - y
                painter.drawEllipse(px - 5, py - 5, 10, 10)
                painter.drawText(px + 12, py + 5, f"({x},{y})")

            # 绘制延长线
            if 'extended_line' in line:
                painter.setPen(QPen(line['color'], 5, Qt.DashLine))  # 5标识虚线的粗细
                x1, y1 = line['extended_line'][0]
                x2, y2 = line['extended_line'][1]

                px1 = self.origin.x() + x1
                py1 = self.origin.y() - y1
                px2 = self.origin.x() + x2
                py2 = self.origin.y() - y2

                painter.drawLine(px1, py1, px2, py2)

            # 绘制移动后的线
            if 'moved_line' in line:
                painter.setPen(QPen(line['color'], 2, Qt.SolidLine))
                x1, y1 = line['moved_line'][0]
                x2, y2 = line['moved_line'][1]

                px1 = self.origin.x() + x1
                py1 = self.origin.y() - y1
                px2 = self.origin.x() + x2
                py2 = self.origin.y() - y2

                painter.drawLine(px1, py1, px2, py2)

    # 其余原有方法保持不变...
    def draw_pixel_ticks(self, painter):
        painter.setFont(QFont('Arial', 7))
        minor_pen = QPen(QColor(200, 200, 200), 1)
        major_pen = QPen(Qt.darkGray, 1.5)

        # X轴刻度（向右）
        for x in range(self.origin.x(), self.width(), 10):
            if x % 50 == 0:  # 主要刻度
                painter.setPen(major_pen)
                painter.drawLine(x, self.origin.y() - 8, x, self.origin.y() + 8)
                painter.drawText(x - 15, self.origin.y() + 25, str(x - self.origin.x()))
            else:  # 次要刻度
                painter.setPen(minor_pen)
                painter.drawLine(x, self.origin.y() - 4, x, self.origin.y() + 4)

        # X轴刻度（向左）
        for x in range(self.origin.x(), 0, -10):
            if x % 50 == 0:
                painter.setPen(major_pen)
                painter.drawLine(x, self.origin.y() - 8, x, self.origin.y() + 8)
                painter.drawText(x - 15, self.origin.y() + 25, str(x - self.origin.x()))
            else:
                painter.setPen(minor_pen)
                painter.drawLine(x, self.origin.y() - 4, x, self.origin.y() + 4)

        # Y轴刻度（向上）
        for y in range(self.origin.y(), 0, -10):
            if y % 50 == 0:
                painter.setPen(major_pen)
                painter.drawLine(self.origin.x() - 8, y, self.origin.x() + 8, y)
                painter.drawText(self.origin.x() + 10, y + 5, str(self.origin.y() - y))
            else:
                painter.setPen(minor_pen)
                painter.drawLine(self.origin.x() - 4, y, self.origin.x() + 4, y)

        # Y轴刻度（向下）
        for y in range(self.origin.y(), self.height(), 10):
            if y % 50 == 0:
                painter.setPen(major_pen)
                painter.drawLine(self.origin.x() - 8, y, self.origin.x() + 8, y)
                painter.drawText(self.origin.x() + 10, y + 5, str(self.origin.y() - y))
            else:
                painter.setPen(minor_pen)
                painter.drawLine(self.origin.x() - 4, y, self.origin.x() + 4, y)

    def draw_quadrant_labels(self, painter):
        font = QFont('Arial', 14, QFont.Bold)
        painter.setFont(font)

        # 第一象限（右上）
        painter.setPen(self.quadrant_colors[0])
        painter.drawText(self.origin.x() + 20, 30, "马嵬驿(第一象限) (+,+)")

        # 第二象限（左上）
        painter.setPen(self.quadrant_colors[1])
        painter.drawText(20, 30, "红尘(第二象限) (-,+)")

        # 第三象限（左下）
        painter.setPen(self.quadrant_colors[2])
        painter.drawText(20, self.height() - 20, "碧落(第三象限) (-,-)")

        # 第四象限（右下）
        painter.setPen(self.quadrant_colors[3])
        painter.drawText(self.origin.x() + 20, self.height() - 20, "黄泉(第四象限) (+,-)")

    def draw_sample_points(self, painter):
        painter.setFont(QFont('Arial', 9))
        for i, (x, y) in enumerate(self.sample_points):
            px = self.origin.x() + x
            py = self.origin.y() - y  # 转换坐标系

            if i == 4:
                # 绘制数据点
                painter.setPen(QPen(self.quadrant_colors[i - 1 // 1], 2))
            else:
                # 绘制数据点
                painter.setPen(QPen(self.quadrant_colors[i // 1], 2))
            painter.setBrush(Qt.white)
            painter.drawEllipse(px - 5, py - 5, 10, 10)

            # 标注坐标值
            painter.drawText(px + 12, py + 5, f"({x},{y})")

    def clear_all_lines(self):
        self.all_lines = []
        self.current_points = []
        self.move_line_index = -1
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QuadrantChart()
    window.show()
    sys.exit(app.exec())
