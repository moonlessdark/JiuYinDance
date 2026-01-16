"""
模板匹配
颜色匹配
图片掩码
"""
__version__ = '0.2.1'

import cv2
import numpy as np
from numpy import ndarray


def find_all_template(im_source: ndarray, im_template: ndarray,
                      threshold: float = 0.5,
                      max_cnt: int = 0,
                      auto_scale: tuple[float, float, float] = None,
                      edge: bool = False,
                      to_gray: bool = False):
    """
    在im_source中查找im_template的匹配位置，返回指定数量的匹配结果

    Args:
        im_source(string): 源图(大图)，opencv格式的图片
        im_template(string): 需要查找的图片(小图)，opencv格式的图片
        threshold: 阈值，当匹配度小于该阈值的时候，就忽略掉，是一个-1~1之间的值，通常小于0.5，匹配度就相当低了
        max_cnt: 最大匹配数量, 缺省为0, 即不限
        auto_scale: 是否自动缩放im_template来查找匹配，如果为None表示不缩放，如果需要缩放，那么传一个tuple：(min_scale, max_scale, step)，
        其中min_scale和max_scale分别是缩放倍数的下限和上限，都是小数，min_scale介于0~1之间，max_scale大于1, step表示从min尝试到max之间的步长,
        默认为0.1
        to_gray: 是否启用灰度模式
        step是从min_scale开始，逐步尝试到max_scale之间的步长，缺省值为0.1，例如(0.8, 1.6, 0.2)
        edge: 是否做边缘提取后再匹配，缺省为False，如果设置为True，会把源图和模板图，都基于Canny算法提取边缘，然后再做匹配
    Returns:
        匹配结果列表，每个结果包含以下属性：
        result: 匹配区域的中心点
        rectangle: 匹配区域的四角坐标
        confidence: 匹配程度, 是一个-1~1之间的值, 约大表示匹配度越高
    Raises:
        IOError: 读取文件失败
    """
    w, h = im_template.shape[1], im_template.shape[0]
    sw, sh = im_source.shape[1], im_source.shape[0]
    if w > sw or h > sh:
        raise RuntimeError(f"源图片尺寸({sw}x{sh})小于模板图片尺寸({w}x{h})，请检查！")
    """
    OpenCV 默认使用 BGR 顺序：读取图片时采用 Blue-Green-Red 的通道排列
    多数显示系统使用 RGB 顺序：如 matplotlib、网页显示等使用 Red-Green-Blue 排列
    从 BGR 格式转换为 RGB 格式，这样可以确保：
     - 图片颜色显示正确
     - 与大多数显示系统的颜色顺序保持一致
     - 避免颜色失真问题
    """
    im_source = cv2.cvtColor(np.array(im_source), cv2.COLOR_BGR2RGB)
    if to_gray:
        # 如果启用了灰度渲染模式，可以加快匹配速度
        im_template = _to_gray(im_template)
        im_source = _to_gray(im_source)
    if edge:
        # 如果启用边缘计算模式
        im_template = im_template.astype(np.uint8)
        im_source = im_source.astype(np.uint8)
        im_template = cv2.Canny(im_template, 100, 200)
        im_source = cv2.Canny(im_source, 100, 200)
    result = _internal_find(im_source, im_template, max_cnt, threshold)
    if len(result) == 0 and auto_scale is not None:
        # 如果匹配结果为0，并且缩放设置不为None
        scale_min: float = auto_scale[0]  # 最小缩放值
        scale_max: float = auto_scale[1]  # 最大缩放值
        step: float = auto_scale[2] if len(auto_scale) > 2 else 0.1  # 缩放步长
        for scale in np.arange(scale_min, scale_max, step):
            resized = cv2.resize(im_template, (int(w * float(scale)), int(h * float(scale))),
                                 interpolation=cv2.INTER_CUBIC)
            result = _internal_find(im_source, resized, max_cnt, threshold)
            if len(result) > 0:
                # 当结果不为0时，结束匹配
                break
    return result


def _to_gray(image):
    """
    对图片进行灰度处理，用于加快匹配
    但是精度会降低
    """
    channel = 1 if len(image.shape) == 2 else image.shape[2]
    if channel == 1:
        # 如果图片本身就是灰度图片
        image_gray = image
    elif channel == 3:
        # 如果图片是彩色图片
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif channel == 4:
        # 如果图片是带alpha通道的图片
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise RuntimeError(f"查询的图片通道数({channel})不支持进行灰度处理")
    return image_gray


def _internal_find(gray_source, gray_template, max_cnt, threshold):
    """
    模板匹配
    # OpenCV 模板匹配方法比较

    根据提供的代码，其中使用了 `cv2.TM_CCOEFF_NORMED` 进行模板匹配，以下是三种主要方法的适用场景分析：

    ## `cv2.TM_CCOEFF_NORMED`（标准化相关系数匹配）

    - **最佳匹配值**：1（越大越好）
    - **适用场景**：
      - 图像内容相似但光照条件不同的情况
      - 需要对亮度变化具有鲁棒性的匹配
      - UI元素识别、图标匹配等场景
      - 代码中使用的默认方法，适用于大多数常规模板匹配任务

    ## `cv2.TM_SQDIFF`（平方差匹配）

    - **最佳匹配值**：0（越小越好）
    - **适用场景**：
      - 完全相同的图像匹配（理想条件下）
      - 对光照变化敏感的精确匹配
      - 背景单一且对比度高的图像匹配
      - 需要检测完全相同区域的应用

    ## `cv2.TM_CCORR_NORMED`（标准化相关匹配）

    - **最佳匹配值**：1（越大越好）
    - **适用场景**：
      - 图像亮度一致的理想匹配
      - 简单的模式识别任务
      - 对光照变化敏感的匹配需求
      - 与 `TM_CCOEFF_NORMED` 类似但对光照变化不如其鲁棒

    ## 在当前项目中的选择

    代码中选择 `cv2.TM_CCOEFF_NORMED` 是合理的，因为：

    1. **游戏自动化场景**：游戏界面可能存在轻微的光照变化
    2. **UI元素识别**：需要对亮度变化有一定容忍度
    3. **多平台兼容**：不同设备显示可能有亮度差异
    """
    w, h = gray_template.shape[1], gray_template.shape[0]
    sw, sh = gray_source.shape[1], gray_source.shape[0]
    res = cv2.matchTemplate(gray_source, gray_template, cv2.TM_CCOEFF_NORMED)
    result = []
    while True:
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        if max_val < threshold:
            break

        left = top_left[0]
        top = top_left[1]
        middle_point = (left + w / 2, top + h / 2)
        result.append(dict(
            result=middle_point,
            rectangle=(top_left, (left, top + h), (left + w, top), (left + w, top + h)),
            confidence=max_val
        ))
        if max_cnt and len(result) >= max_cnt:
            break
        # 用最小值填充当前结果的周边区域，避免下次找到重叠的结果
        x1 = left - w + 1 if left - w + 1 > 0 else 0
        x2 = left + w - 1 if left + w - 1 < sw else sw
        y1 = top - h + 1 if top - h + 1 > 0 else 0
        y2 = top + h - 1 if top + h - 1 < sh else sh
        res[y1:y2, x1:x2] = -1000
    return result
