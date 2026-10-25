# coding: utf-8
"""
项目路径解析。

与旧 Utils/projectPath.py 的区别：
1. 不再依赖 sys.path 顺序，直接以本文件位置推导项目根；
2. 不再通过字符串切割 "DeskFunc" 判断根目录，旧方式在目录改名后会失效；
3. 支持 set_project_root() 显式覆盖，便于把 Core 复用到新项目；
4. PyInstaller 打包后以 exe 所在目录为基准，并优先使用 sys._MEIPASS，
   不再依赖启动时的工作目录。
"""
from __future__ import annotations

import os
import sys

_ROOT_OVERRIDE: str | None = None


def set_project_root(root_path: str | None) -> None:
    """
    显式指定项目根目录。

    :param root_path: 项目根绝对路径；传 None 表示恢复自动推导
    """
    global _ROOT_OVERRIDE
    if root_path is None:
        _ROOT_OVERRIDE = None
        return
    _ROOT_OVERRIDE = os.path.normpath(root_path).replace("\\", "/")


def _is_frozen() -> bool:
    """判断当前是否处于 PyInstaller 打包运行状态。"""
    return bool(getattr(sys, "frozen", False))


def _detect_root() -> str:
    """
    推导程序根目录。

    源码运行时：Core/config/paths.py 向上三级就是项目根；
    打包运行时：以可执行文件所在目录为根，不能用 os.getcwd()，
    否则从快捷方式或其它目录启动时会指向错误位置。
    """
    if _is_frozen():
        return os.path.dirname(os.path.realpath(sys.executable)).replace("\\", "/")
    # __file__ 位于 <root>/Core/config/paths.py
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))).replace("\\", "/")


def _detect_resource_root() -> str | None:
    """
    推导打包后的资源目录。

    PyInstaller onedir：sys._MEIPASS 指向 <exe目录>/_internal；
    PyInstaller onefile：sys._MEIPASS 指向临时解压目录。
    """
    if not _is_frozen():
        return None
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return os.path.normpath(meipass).replace("\\", "/")
    return None


class PathUtil:
    """路径处理工具类。"""

    def __init__(self):
        self.rootPath = _ROOT_OVERRIDE or _detect_root()

    def get_root_path(self) -> str:
        """
        获取资源根路径，末尾统一带斜杠。

        源码模式返回项目根；PyInstaller 返回 _MEIPASS
        （onedir 下即 <exe目录>/_internal）。
        """
        if _ROOT_OVERRIDE:
            return "%s/" % _ROOT_OVERRIDE
        resource_root = _detect_resource_root()
        if resource_root:
            return "%s/" % resource_root
        return "%s/" % self.rootPath

    def get_app_dir(self) -> str:
        """
        获取程序自身目录（用于 app_config.ini 等可写配置）。

        源码模式返回项目根，打包后返回 exe 所在目录，
        与启动时的工作目录无关。
        """
        if _ROOT_OVERRIDE:
            return _ROOT_OVERRIDE
        return self.rootPath

    def get_path_from_resources(self, file_name: str) -> str:
        """
        按文件名拼接 Resources 下的路径。

        :param file_name: 资源相对路径，例如 mapGoodsPointList.json
        """
        return "%sResources/%s" % (self.get_root_path(), file_name)

    @staticmethod
    def resource_path(relative_path: str) -> str:
        """生成资源文件目录访问路径（兼容 PyInstaller 打包）。"""
        return os.path.join(PathUtil().get_root_path(), relative_path)
