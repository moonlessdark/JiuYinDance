"""
模板匹配底层实现。

本次重构重点：
1. 修复原实现把源图 BGR 转成 RGB、模板却保持 BGR 导致的通道错位问题；
2. 统一通道、dtype 和空图校验，异常场景返回空结果而不是直接崩溃；
3. 增加模板文件缓存，避免业务层每一轮识别都从磁盘重新读取模板；
4. 用候选点 + 非极大值抑制（NMS）替代反复 minMaxLoc 全图扫描，减少重复计算；
5. 支持带 alpha 通道的透明模板（按需开启），并保留原有 edge / auto_scale 行为。

对上层保持兼容：find_all_template 的函数签名和返回结构不变。
"""
__version__ = '0.3.0'

import os
from functools import lru_cache
from typing import Optional

import cv2
import numpy as np
from numpy import ndarray

# 模板文件缓存上限。项目内模板数量有限，512 足够覆盖全部资源并留出扩展空间。
_TEMPLATE_CACHE_SIZE = 512
# 单次匹配最多处理多少个候选点，避免低阈值 + 大图时排序耗时失控。
_MAX_CANDIDATES = 5000


def load_template(template_path: str) -> Optional[ndarray]:
    """
    读取模板图片（带进程内缓存）。

    使用 np.fromfile + cv2.imdecode 以兼容含中文的路径。
    返回的 ndarray 是缓存对象，调用方只读使用，禁止原地修改。

    :param template_path: 模板图片绝对路径
    :return: OpenCV 图片；路径为空、文件不存在或解码失败时返回 None
    """
    if not template_path:
        return None
    return _load_template_cached(os.path.normpath(template_path))


@lru_cache(maxsize=_TEMPLATE_CACHE_SIZE)
def _load_template_cached(template_path: str) -> Optional[ndarray]:
    """带缓存的模板读取实现，路径必须是已规范化的绝对路径。"""
    try:
        file_data = np.fromfile(template_path, dtype=np.uint8)
    except (OSError, ValueError):
        return None
    if file_data.size == 0:
        return None
    try:
        return cv2.imdecode(file_data, cv2.IMREAD_UNCHANGED)
    except cv2.error:
        return None


def clear_template_cache():
    """清空模板缓存，主要用于调试或模板文件被外部修改后重新加载。"""
    _load_template_cached.cache_clear()


def find_all_template(im_source: ndarray, im_template: ndarray,
                      threshold: float = 0.5,
                      max_cnt: int = 0,
                      auto_scale: tuple[float, float, float] = None,
                      edge: bool = False,
                      to_gray: bool = False,
                      use_alpha_mask: bool = False):
    """
    在 im_source 中查找 im_template 的匹配位置，返回指定数量的匹配结果。

    Args:
        im_source: 源图（大图），OpenCV BGR/BGRA/灰度格式
        im_template: 需要查找的模板（小图），OpenCV BGR/BGRA/灰度格式
        threshold: 匹配阈值，-1~1，越大越严格
        max_cnt: 最大匹配数量，0 表示不限制
        auto_scale: 自动缩放参数 (min_scale, max_scale, step)；
                    只有原始尺寸匹配不到结果时才会尝试
        edge: 是否先做 Canny 边缘提取再匹配
        to_gray: 是否转灰度匹配（速度更快，精度略低）
        use_alpha_mask: 模板含 alpha 通道时，是否按透明区域做掩码匹配；
                        默认关闭以保持旧调用方的阈值语义

    Returns:
        匹配结果列表，每项包含：
        result: 匹配区域中心点 (x, y)
        rectangle: (左上, 左下, 右上, 右下)，与旧版本结构保持一致
        confidence: 匹配度
    """
    source, template, mask = _prepare_images(
        im_source=im_source,
        im_template=im_template,
        to_gray=to_gray,
        edge=edge,
        use_alpha_mask=use_alpha_mask,
    )
    if source is None or template is None:
        return []

    result = _internal_find(source, template, max_cnt, threshold, mask)
    if result or auto_scale is None:
        return result

    # 原始尺寸没有匹配到，按缩放参数逐个尝试
    scale_min, scale_max, step = _parse_auto_scale(auto_scale)
    if step <= 0 or scale_max <= scale_min:
        return result

    template_height, template_width = template.shape[:2]
    source_height, source_width = source.shape[:2]

    for scale in np.arange(scale_min, scale_max, step):
        scale = round(float(scale), 4)
        if scale <= 0:
            continue
        new_width = int(template_width * scale)
        new_height = int(template_height * scale)
        # 缩放后小于 1 像素或大于源图都没有意义
        if new_width < 1 or new_height < 1:
            continue
        if new_width > source_width or new_height > source_height:
            continue
        resized = cv2.resize(template, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        resized_mask = None
        if mask is not None:
            resized_mask = cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
        result = _internal_find(source, resized, max_cnt, threshold, resized_mask)
        if result:
            break
    return result


def _parse_auto_scale(auto_scale: tuple) -> tuple[float, float, float]:
    """
    解析和校验自动缩放参数，避免传入空元组或非法值导致异常。
    """
    if not isinstance(auto_scale, (tuple, list)) or len(auto_scale) < 2:
        return 0.0, 0.0, 0.0
    scale_min = float(auto_scale[0])
    scale_max = float(auto_scale[1])
    step = float(auto_scale[2]) if len(auto_scale) > 2 else 0.1
    return scale_min, scale_max, step


def _prepare_images(im_source: ndarray, im_template: ndarray,
                    to_gray: bool,
                    edge: bool,
                    use_alpha_mask: bool) -> tuple[Optional[ndarray], Optional[ndarray], Optional[ndarray]]:
    """
    统一处理源图和模板的 dtype、通道数，并生成可选的 alpha 掩码。

    :return: (源图, 模板, 掩码)；无法处理时返回 (None, None, None)
    """
    if im_source is None or im_template is None:
        return None, None, None
    if not isinstance(im_source, np.ndarray) or not isinstance(im_template, np.ndarray):
        return None, None, None
    if im_source.size == 0 or im_template.size == 0:
        return None, None, None

    source = _ensure_valid_dtype(np.asarray(im_source))
    template = _ensure_valid_dtype(np.asarray(im_template))

    template_height, template_width = template.shape[:2]
    source_height, source_width = source.shape[:2]
    if template_height > source_height or template_width > source_width:
        # 模板比源图大时不可能匹配，返回空结果由上层决定后续逻辑
        return None, None, None

    mask: Optional[ndarray] = None
    if not to_gray and not edge:
        # 普通彩色匹配必须保证源图和模板通道数一致
        if use_alpha_mask:
            template, mask = _split_alpha_mask(template)
        else:
            template = _ensure_bgr(template)
        source = _ensure_bgr(source)

    if to_gray or edge:
        source = _to_gray(source)
        template = _to_gray(template)
        mask = None

    if edge:
        source = cv2.Canny(source.astype(np.uint8), 100, 200)
        template = cv2.Canny(template.astype(np.uint8), 100, 200)

    return source, template, mask


def _ensure_bgr(image: ndarray) -> ndarray:
    """把灰度图或 BGRA 图统一成 BGR，供彩色模板匹配使用。"""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    channel = image.shape[2]
    if channel == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
    if channel == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def _split_alpha_mask(template: ndarray) -> tuple[ndarray, Optional[ndarray]]:
    """
    将 4 通道模板拆成 3 通道图像和 alpha 掩码。

    :return: (BGR 模板, 掩码或 None)
    """
    if template.ndim != 3 or template.shape[2] != 4:
        return template, None
    alpha = template[:, :, 3]
    # 没有实际透明像素时不需要掩码，避免无谓地切换匹配算法
    if not np.any(alpha < 255):
        return cv2.cvtColor(template, cv2.COLOR_BGRA2BGR), None
    mask = np.where(alpha > 0, 255, 0).astype(np.uint8)
    return cv2.cvtColor(template, cv2.COLOR_BGRA2BGR), mask


def _to_gray(image: ndarray) -> ndarray:
    """
    转换为灰度图。已经是灰度图时直接返回原对象。
    """
    if image.ndim == 2:
        return image
    channel = image.shape[2]
    if channel == 1:
        return image[:, :, 0]
    if channel == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if channel == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise RuntimeError(f"查询的图片通道数({channel})不支持进行灰度处理")


def _ensure_valid_dtype(image: ndarray) -> ndarray:
    """
    确保图像数据类型符合 OpenCV 要求，并统一通道顺序（不改变 BGR 排列）。
    """
    if image.dtype == np.uint8:
        return image
    # float 图片常见于归一化后的数据，直接裁剪到 0~255 避免溢出
    if np.issubdtype(image.dtype, np.floating):
        image = np.nan_to_num(image, nan=0.0, posinf=255.0, neginf=0.0)
        if image.size and float(image.max()) <= 1.0:
            image = image * 255.0
        return np.clip(image, 0, 255).astype(np.uint8)
    return image.astype(np.uint8)


def _is_constant_image(image: ndarray) -> bool:
    """
    判断图片是否为单色常量图。

    多通道图片需要按通道分别计算标准差，否则不同通道之间的颜色差会被误判为
    “有变化”，导致常量模板走错匹配算法。
    """
    if image.ndim == 2:
        return float(np.std(image)) < 1e-6
    channel_std = np.std(image.reshape(-1, image.shape[2]), axis=0)
    return bool(np.all(channel_std < 1e-6))


def _internal_find(source: ndarray, template: ndarray, max_cnt: int, threshold: float,
                   mask: Optional[ndarray] = None) -> list:
    """
    执行模板匹配并做非极大值抑制。

    对普通模板使用 TM_CCOEFF_NORMED（对亮度变化更鲁棒）；
    对带掩码的透明模板使用 TM_CCORR_NORMED + mask（OpenCV 支持该组合）。
    """
    if source is None or template is None:
        return []

    template_height, template_width = template.shape[:2]
    source_height, source_width = source.shape[:2]
    if template_height > source_height or template_width > source_width:
        return []

    # 常量模板在 TM_CCOEFF_NORMED 下会出现 NaN，改用平方差匹配
    method = cv2.TM_CCOEFF_NORMED
    invert_result = False
    if mask is not None:
        method = cv2.TM_CCORR_NORMED
    elif _is_constant_image(template):
        method = cv2.TM_SQDIFF_NORMED
        invert_result = True

    try:
        if mask is not None:
            res = cv2.matchTemplate(source, template, method, mask=mask)
        else:
            res = cv2.matchTemplate(source, template, method)
    except cv2.error:
        return []

    if invert_result:
        # 平方差匹配越小越好，转换为越大越好，便于统一阈值处理
        res = 1.0 - res

    # 掩码匹配在整片同色区域可能出现 inf/nan，统一清理成不可能命中的值
    res = np.nan_to_num(res, nan=-1.0, posinf=-1.0, neginf=-1.0)
    res_height, res_width = res.shape[:2]

    ys, xs = np.where(res >= float(threshold))
    if len(xs) == 0:
        return []

    scores = res[ys, xs]
    # 低阈值时候选可能极多，先按分数保留有限数量，防止排序占用过多时间
    limit = max_cnt * 50 if max_cnt else _MAX_CANDIDATES
    if len(scores) > limit:
        top_index = np.argpartition(scores, -limit)[-limit:]
        xs = xs[top_index]
        ys = ys[top_index]
        scores = scores[top_index]

    order = np.argsort(-scores)
    suppressed = np.zeros((res_height, res_width), dtype=bool)
    result = []

    for index in order:
        left = int(xs[index])
        top = int(ys[index])
        if suppressed[top, left]:
            continue

        confidence = float(scores[index])
        # 与旧版本保持一致：rectangle 顺序为 左上、左下、右上、右下
        result.append(dict(
            result=(left + template_width / 2, top + template_height / 2),
            rectangle=(
                (left, top),
                (left, top + template_height),
                (left + template_width, top),
                (left + template_width, top + template_height),
            ),
            confidence=confidence,
        ))

        if max_cnt and len(result) >= max_cnt:
            break

        # 抑制与当前匹配区域重叠的候选点，避免同一个图标被重复返回
        x1 = max(0, left - template_width + 1)
        x2 = min(res_width, left + template_width)
        y1 = max(0, top - template_height + 1)
        y2 = min(res_height, top + template_height)
        suppressed[y1:y2, x1:x2] = True

    return result
