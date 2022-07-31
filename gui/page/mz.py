# -*- coding: utf-8 -*-

# 免责申明


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("Form")
        self.resize(185, 90)
        self.setMinimumSize(QtCore.QSize(185, 90))
        self.setMaximumSize(QtCore.QSize(185, 90))
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(10, 10, 171, 71))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.setWindowTitle("免责申明")
        self.label.setText("<html><head/><body><p>免责申明:<p>本工具仅供学习研究，禁止商<br>业使用，二十四小时删除</p></body></html>")
