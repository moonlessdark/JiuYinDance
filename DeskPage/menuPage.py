import os
import subprocess

from PySide6 import QtWidgets, QtGui, QtCore

from DeskPage.MarkdownViewer import MarkdownViewer
from DeskPage.mapMoXiLine import QuadrantChart
from DeskPage.menu_action_map_point_page import MapPointTable
from DeskPage.skillSettingDialog import SkillSetting


class MenuUI(QtWidgets.QMenuBar):
    def __init__(self):
        super().__init__()

        file_menu = QtWidgets.QMenu("&配置", self)
        tools_menu = QtWidgets.QMenu("&小工具", self)
        about_menu = QtWidgets.QMenu("&帮助", self)

        self.addMenu(file_menu)
        self.addMenu(tools_menu)
        self.addMenu(about_menu)

        action_open_config_file = QtGui.QAction("资源目录", self)
        file_menu.addAction(action_open_config_file)
        action_open_config_file.triggered.connect(self.open_config_file)

        self.action_edit_skill_list = QtGui.QAction("编辑技能", self)
        file_menu.addAction(self.action_edit_skill_list)
        self.action_edit_skill_list.triggered.connect(self.open_skill_setting)

        action_edit_map_goods_point_list = QtGui.QAction("地图采集", self)
        file_menu.addAction(action_edit_map_goods_point_list)
        action_edit_map_goods_point_list.triggered.connect(self.open_map_goods_point)

        action_open_url = QtGui.QAction("访问项目", self)
        about_menu.addAction(action_open_url)
        action_open_url.triggered.connect(self.open_url_project)

        action_open_url_get_fore_ground_window_fail = QtGui.QAction("修复窗口激活失败", self)
        about_menu.addAction(action_open_url_get_fore_ground_window_fail)
        action_open_url_get_fore_ground_window_fail.triggered.connect(self.open_url_get_fore_ground_window_fail)

        action_func_detail = QtGui.QAction("功能说明", self)
        about_menu.addAction(action_func_detail)
        action_func_detail.triggered.connect(self.open_func_detail_widget)

        action_func_download_zip = QtGui.QAction("获取更新", self)
        about_menu.addAction(action_func_download_zip)
        action_func_download_zip.triggered.connect(self.open_func_download_widget)

        action_func_mo_xi_find_goods_line = QtGui.QAction("漠西-挖宝指引", self)
        tools_menu.addAction(action_func_mo_xi_find_goods_line)
        action_func_mo_xi_find_goods_line.triggered.connect(self.open_mo_xi_find_goods_line)
        self.widget_map_liene = None  # 挖宝指引的窗口

    def open_config_file(self):
        """
        打开配置文件
        :return:
        """
        config_file: str = '.\\_internal\\Resources\\'
        if not os.path.exists(config_file):  # 如果主目录+小时+分钟这个文件路径不存在的话
            config_file = ".\\Resources\\"
        QtWidgets.QFileDialog.getOpenFileName(self, "资源文件", config_file,
                                              "Text Files (*.yaml;*.bat;*.png;*.ico;*.dll;*.json;*.*)")

    @staticmethod
    def open_url_get_fore_ground_window_fail(self):
        """
        激活窗口失败
        :param self:
        :return:
        """
        config_file: str = '.\\_internal\\Resources\\fixSwitchWindowsFail.bat'
        if not os.path.exists(config_file):
            config_file = ".\\Resources\\fixSwitchWindowsFail.bat"
        if os.path.exists(config_file):
            subprocess.run(config_file, shell=False)
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://blog.csdn.net/qq_26013403/article/details/129122971"))

    @staticmethod
    def open_url_project():
        """
        打开网页
        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/moonlessdark/JiuYinDance"))

    @staticmethod
    def open_func_download_widget():
        """
        打开网页
        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://pan.baidu.com/s/1RvCMqy9E6AkuDr5WxmSLcg?pwd=n69x"))

    def open_func_detail_widget(self):
        """
        打开功能说明
        """
        new_windows = MarkdownViewer(self)
        new_windows.show()

    def open_map_goods_point(self):
        """
        打开设置地图采集坐标
        """
        dialog_map_liene = MapPointTable(self)
        if not dialog_map_liene.isVisible():
            dialog_map_liene.setVisible(True)
            dialog_map_liene.load_map_goods_point_table()  # 加载一下文件里的内容到表格上

    def open_skill_setting(self):
        """
        打开技能编辑
        :return:
        """
        _skill = SkillSetting(self)
        if not _skill.isVisible():
            _skill.show()
            _skill.load_skill_table()

    def open_mo_xi_find_goods_line(self):
        """
        漠西挖宝-指引
        :return:
        """
        self.widget_map_liene = QuadrantChart()
        self.widget_map_liene.raise_()  # 将窗口置于最前（如果需要）
        self.widget_map_liene.show()
