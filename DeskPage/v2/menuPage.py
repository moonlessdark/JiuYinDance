# coding: utf-8
"""
v2 菜单栏。

只保留本次迁移需要使用的入口：
1. 打开资源目录；
2. 编辑地图采集路线；
3. 访问项目主页。
"""
import os

from PySide6 import QtWidgets, QtGui, QtCore

from Core.config.paths import PathUtil
from DeskPage.v2.mapPointDialog import MapPointTable


class MenuUI(QtWidgets.QMenuBar):
    """顶部菜单栏。"""

    def __init__(self):
        super().__init__()
        self._map_point_dialog: MapPointTable | None = None

        file_menu = QtWidgets.QMenu("&配置", self)
        about_menu = QtWidgets.QMenu("&帮助", self)
        self.addMenu(file_menu)
        self.addMenu(about_menu)

        action_open_config_file = QtGui.QAction("资源目录", self)
        file_menu.addAction(action_open_config_file)
        action_open_config_file.triggered.connect(self.open_config_file)

        action_edit_map_goods_point = QtGui.QAction("地图采集", self)
        file_menu.addAction(action_edit_map_goods_point)
        action_edit_map_goods_point.triggered.connect(self.open_map_goods_point)

        action_open_url = QtGui.QAction("访问项目", self)
        about_menu.addAction(action_open_url)
        action_open_url.triggered.connect(self.open_url_project)

    def open_config_file(self, _checked: bool = False):
        """打开资源目录。"""
        resource_dir = PathUtil().get_root_path() + "Resources/"
        if not os.path.exists(resource_dir):
            resource_dir = "."
        QtWidgets.QFileDialog.getOpenFileName(
            self, "资源文件", resource_dir,
            "Text Files (*.yaml;*.bat;*.png;*.ico;*.dll;*.json;*.*)")

    def open_url_project(self, _checked: bool = False):
        """打开项目主页。"""
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/moonlessdark/JiuYinDance"))

    def open_map_goods_point(self):
        """打开地图采集路线编辑器。"""
        if self._map_point_dialog is None:
            self._map_point_dialog = MapPointTable(self)
            self._map_point_dialog.load_map_goods_point_table()
        self._map_point_dialog.setVisible(True)
        self._map_point_dialog.raise_()
