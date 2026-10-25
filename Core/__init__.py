# coding: utf-8
"""
底层能力包。

本包与业务、GUI 完全隔离，不导入 DeskFunc / DeskPage / Utils 中的任何代码，
后续新项目可以直接复制或依赖本包：

- config   路径与运行环境
- windows  Win32 窗口、截图、DPI、坐标映射
- vision   模板匹配、目标描述、定位器、颜色/阈值算法
- input    幽灵键鼠、大漠插件、全局鼠标监听
"""
