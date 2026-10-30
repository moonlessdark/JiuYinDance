# coding: utf-8
"""
v2 菜单栏。

只保留本次迁移需要使用的入口：
1. 打开资源目录；
2. 编辑地图采集路线；
3. 访问项目主页。
"""
import dataclasses
import os
from typing import Callable, Optional

from PySide6 import QtWidgets, QtGui, QtCore

from Core.config.paths import PathUtil
from DeskFunc.v2.TaskBussinese.buffConfig import (
    load_buff_config,
    panel_settings_from_config,
    save_buff_config,
)
from DeskPage.v2.buffPanel import PanelSettings
from DeskPage.v2.buffSettingsDialog import BuffSettingsDialog
from DeskPage.v2.mapPointDialog import MapPointTable
from Utils.resourceConfig import get_resources


class MenuUI(QtWidgets.QMenuBar):
    """顶部菜单栏。"""

    def __init__(self, on_buff_settings_changed:
                 Optional[Callable[[PanelSettings], None]] = None):
        super().__init__()
        self._map_point_dialog: MapPointTable | None = None
        self._on_buff_settings_changed = on_buff_settings_changed

        file_menu = QtWidgets.QMenu("&配置", self)
        about_menu = QtWidgets.QMenu("&帮助", self)
        self.addMenu(file_menu)
        self.addMenu(about_menu)

        action_open_config_file = QtGui.QAction("资源目录", self)
        file_menu.addAction(action_open_config_file)
        action_open_config_file.triggered.connect(self.open_config_file)

        action_buff_settings = QtGui.QAction("BUFF识别设置", self)
        file_menu.addAction(action_buff_settings)
        action_buff_settings.triggered.connect(self.open_buff_settings)

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

    def open_buff_settings(self, _checked: bool = False):
        """打开 BUFF 识别设置，保存后立即应用面板外观。"""
        assets = get_resources().buff_assets
        config = load_buff_config(assets.config_path)
        if not config:
            QtWidgets.QMessageBox.warning(
                self, "BUFF识别设置",
                f"配置文件读取失败：\n{assets.config_path}")
            return

        settings = PanelSettings(**panel_settings_from_config(config))
        dialog = BuffSettingsDialog(
            settings, config, assets.showbuff_dir, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        panel_settings = dialog.panel_settings()
        config["enabled_templates"] = dialog.enabled_templates()
        config["panel"] = dataclasses.asdict(panel_settings)
        config["detect_sensitivity"] = dialog.detect_sensitivity()
        if not save_buff_config(assets.config_path, config):
            QtWidgets.QMessageBox.warning(
                self, "BUFF识别设置",
                f"配置保存失败：\n{assets.config_path}")
            return

        if self._on_buff_settings_changed is not None:
            self._on_buff_settings_changed(panel_settings)

    def open_map_goods_point(self):
        """打开地图采集路线编辑器。"""
        if self._map_point_dialog is None:
            self._map_point_dialog = MapPointTable(self)
            self._map_point_dialog.load_map_goods_point_table()
        self._map_point_dialog.setVisible(True)
        self._map_point_dialog.raise_()
