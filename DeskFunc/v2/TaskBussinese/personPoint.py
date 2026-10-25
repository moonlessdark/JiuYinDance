# coding: utf-8
"""
人物右上角坐标识别（纯模板匹配，不是 OCR）。

坐标区域由调用方裁剪好后传入，本模块只负责：
1. 用 0-9、逗号、负号模板找出所有数字；
2. 同一数字被多个模板重复命中时按位置去重；
3. 按横坐标从左到右拼接成字符串。

模板尺寸很小（约 9x6），所以去重距离取 3 像素，既能合并重复命中，
又不会把相邻的两个数字误合并。
"""
from __future__ import annotations

import numpy as np

from Core.vision.template import find_all_template, load_template
from Utils.resourceConfig import get_resources

from DeskFunc.v2.TaskBussinese.imageTools import deduplicate_points, to_gray

# (输出字符, 资源字段)
_NUMBER_FIELDS: tuple[tuple[str, str], ...] = (
    ("0", "zero"),
    ("1", "one"),
    ("2", "two"),
    ("3", "three"),
    ("4", "four"),
    ("5", "five"),
    ("6", "six"),
    ("7", "seven"),
    ("8", "eight"),
    ("9", "nine"),
    ("DH", "d"),   # 逗号
    ("FS", "f"),   # 负号
)

_CONFLICT_DISTANCE = 3.0


class FindPersonPoint:
    """识别人物坐标文本。"""

    def __init__(self):
        resources = get_resources()
        point_config = resources.person_point

        self._templates: list[tuple[str, np.ndarray]] = []
        for text, field in _NUMBER_FIELDS:
            template = to_gray(load_template(getattr(point_config, field, "")))
            if template is not None:
                self._templates.append((text, template))

    def find_text(self, image: np.ndarray) -> str:
        """
        识别裁剪后坐标区域中的文本。

        :param image: 坐标区域截图（BGR / BGRA / 灰度均可）
        :return: 例如 "1178,287"；没有识别到内容时返回空字符串
        """
        gray = to_gray(image)
        if gray is None:
            return ""

        points: list[dict] = []
        for text, template in self._templates:
            results = find_all_template(
                im_source=gray,
                im_template=template,
                threshold=0.9,
                max_cnt=0,
                to_gray=True,
            )
            for result in results:
                points.append({
                    "result": result["result"],
                    "confidence": result["confidence"],
                    "text": text,
                })

        points = deduplicate_points(points, _CONFLICT_DISTANCE)
        if not points:
            return ""

        # 坐标文本是横向排列的，按中心点横坐标排序即可
        points.sort(key=lambda item: item["result"][0])
        chars = ["-" if item["text"] == "FS" else "," if item["text"] == "DH" else item["text"]
                 for item in points]

        # 末端偶尔会把坐标后缀识别成负号，直接丢弃
        if chars and chars[-1] == "-":
            chars.pop()
        return "".join(chars)
