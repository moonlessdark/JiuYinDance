# coding: utf-8
"""
BUFF 识别配置读取与模板启用规则。

配置文件 Resources/ImageTemplate/PicBuff/buff_config.json 采用三级结构：
    模版类型（内功/武学） -> 模版名称（如“峨眉会意功”） -> BUFF 图标信息

设置界面只改写 enabled_templates 和 panel 两组配置，识别线程每次启动
都会重新读取配置，因此模板勾选在下次开始监控时生效。
"""
from __future__ import annotations

import json

TEMPLATE_CATEGORIES = ("内功", "武学")

# 面板外观默认值
DEFAULT_PANEL_SETTINGS = {
    "icon_size": 62,
    "layout_mode": "rows",
    "show_attr_label": False,
    "background_alpha": 0,
}


def load_buff_config(path: str) -> dict:
    """读取配置；文件不存在或格式错误时返回空字典。"""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def save_buff_config(path: str, config: dict) -> bool:
    """把配置写回 JSON，成功返回 True；中文不转义，保持可读。"""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except OSError as error:
        print(f"BUFF 配置保存失败：{error}")
        return False
    return True


def enabled_template_map(config: dict) -> dict[str, set[str]] | None:
    """
    解析 enabled_templates 配置。

    :return: 模版类型 -> 启用的模版名称集合；缺失或格式错误时返回 None（全部启用）
    """
    raw = config.get("enabled_templates")
    if not isinstance(raw, dict):
        return None
    result: dict[str, set[str]] = {}
    for category, names in raw.items():
        if isinstance(names, (list, tuple, set)):
            result[str(category)] = {str(name) for name in names}
    return result


def is_template_enabled(enabled_map: dict[str, set[str]] | None,
                        category: str, template_name: str) -> bool:
    """
    判断某个模版名称是否启用。

    - enabled_templates 缺失时全部启用；
    - 某类型没有出现在配置里时，该类型下全部启用；
    - 某类型配置了空列表，表示该类型一个都不启用。
    """
    if enabled_map is None:
        return True
    if category not in enabled_map:
        return True
    return template_name in enabled_map[category]


def panel_settings_from_config(config: dict) -> dict:
    """从配置中取出面板外观字段，并补齐默认值和类型。"""
    raw = config.get("panel")
    if not isinstance(raw, dict):
        raw = {}
    return {
        "icon_size": int(raw.get("icon_size",
                                 DEFAULT_PANEL_SETTINGS["icon_size"])),
        "layout_mode": str(raw.get("layout_mode",
                                   DEFAULT_PANEL_SETTINGS["layout_mode"])),
        "show_attr_label": bool(raw.get("show_attr_label",
                                        DEFAULT_PANEL_SETTINGS["show_attr_label"])),
        "background_alpha": int(raw.get("background_alpha",
                                        DEFAULT_PANEL_SETTINGS["background_alpha"])),
    }
