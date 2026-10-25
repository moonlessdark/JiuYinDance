import cv2
import numpy as np
from collections import Counter, namedtuple

# 定义颜色信息的命名元组
# rgb: 颜色
# count: 颜色出现的次数
# percentage: 颜色出现的百分比
ColorInfo = namedtuple('ColorInfo', ['rgb', 'count', 'percentage'])


def analyze_image_colors(image: np.ndarray, top_n=10, tolerance=0) -> list[ColorInfo]:
    """
    分析图像的主要颜色
    获取图像中像素数量最多的前N种颜色（根据容差值智能选择算法）
    :param image 图片
    :param top_n 拿最前面的N个颜色
    :param tolerance 颜色容差值，相邻的N个颜色，都算作同一个颜色
                     默认为0，表示精准查询，不考虑容差值
    """
    # OpenCV默认使用BGR格式，转换为RGB
    # 根据通道数选择合适的转换方式
    if len(image.shape) == 3 and image.shape[2] == 4:
        # 4通道图片先转为3通道
        image_3ch = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        image_rgb = cv2.cvtColor(image_3ch, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    if tolerance > 0:
        top_colors = _get_top_colors_with_tolerance(image_rgb, top_n, tolerance)
    else:
        top_colors = _get_top_colors(image_rgb, top_n)
    return top_colors


def _get_top_colors(image_rgb: np.ndarray, top_n=10) -> list[ColorInfo]:
    """
    获取图像中像素数量最多的前N种颜色
    """
    # 将图像重塑为像素数组
    pixels = image_rgb.reshape(-1, 3)

    # 转换为元组列表以便统计
    pixel_tuples = [tuple(pixel) for pixel in pixels]

    # 统计每种颜色的出现次数
    color_counter = Counter(pixel_tuples)

    # 总像素数
    total_pixels = len(pixel_tuples)

    # 获取出现次数最多的前N种颜色
    top_colors = color_counter.most_common(top_n)

    # 构建结果，使用 namedtuple 包装
    result = []
    for color, count in top_colors:
        percentage = count / total_pixels
        result.append(ColorInfo(rgb=color, count=count, percentage=percentage))

    return result

def _get_top_colors_with_tolerance(image_rgb: np.ndarray, top_n=10, tolerance=10) -> list[ColorInfo]:
    """
    获取图像中像素数量最多的前N种颜色（考虑容差）
    """
    pixels = image_rgb.reshape(-1, 3)
    pixel_tuples = [tuple(pixel) for pixel in pixels]

    # 合并相近颜色
    merged_colors = {}
    for pixel in pixel_tuples:
        found_match = False
        for existing_color in merged_colors.keys():
            if _colors_within_tolerance(pixel, existing_color, tolerance):
                merged_colors[existing_color] += 1
                found_match = True
                break

        if not found_match:
            merged_colors[pixel] = 1

    # 按数量排序
    sorted_colors = sorted(merged_colors.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # 计算总像素数
    total_pixels = len(pixel_tuples)

    # 构建结果
    result = []
    for color, count in sorted_colors:
        percentage = count / total_pixels
        result.append(ColorInfo(rgb=color, count=count, percentage=percentage))

    return result

def _colors_within_tolerance(color1, color2, tolerance=10):
    """
    :param color1
    :param color2
    :param tolerance
    判断两个RGB颜色是否在容差范围内
    """
    r_diff = abs(color1[0] - color2[0])
    g_diff = abs(color1[1] - color2[1])
    b_diff = abs(color1[2] - color2[2])

    return max(r_diff, g_diff, b_diff) <= tolerance

def _rgb_to_hsv_range(rgb_color: tuple[int, int, int], tolerance=(10, 50, 50)):
    """
    将RGB颜色转换为HSV范围
    :param rgb_color: RGB颜色值 (R, G, B) 元组
    :param tolerance: HSV容差 (H, S, V)
    """
    # 创建单像素图像进行转换
    pixel = np.uint8([[rgb_color]])
    hsv_pixel = cv2.cvtColor(pixel, cv2.COLOR_RGB2HSV)
    h, s, v = hsv_pixel[0][0]

    # 计算范围
    lower_hsv = (
        max(0, h - tolerance[0]),
        max(0, s - tolerance[1]),
        max(0, v - tolerance[2])
    )
    upper_hsv = (
        min(179, h + tolerance[0]),  # H通道最大值为179
        min(255, s + tolerance[1]),
        min(255, v + tolerance[2])
    )

    return lower_hsv, upper_hsv

def get_hsv_ranges_from_rgb(rgb_list: list[tuple[int, int, int]], tolerance=(10, 50, 50)):
    """
    从RGB列表计算HSV范围
    :param rgb_list 需要查询的RGB颜色列表
    :param tolerance 参数设置建议
                    - H（色相）容差：通常设置为5-15，控制颜色种类
                    - S（饱和度）容差：通常设置为30-50，适应饱和度变化
                    - V（明度）容差：通常设置为30-50，适应亮度变化
    """
    ranges = []
    for rgb in rgb_list:
        lower, upper = _rgb_to_hsv_range(rgb, tolerance)
        ranges.append((lower, upper))
    return ranges

def find_progress_bar_by_rgb(roi: np.ndarray, target_rgbs: list[tuple[int, int, int]],
                           tolerance=(5, 30, 30), min_aspect_ratio=3, min_length=80,
                           min_area=10, morph_kernel_size=3):
    """
    通过RGB颜色检测是否存在连续的某个颜色
    通用场景：血量条、进度条
    :param roi: 检测区域
    :param target_rgbs: 目标RGB颜色列表 [(r,g,b), ...]
    :param tolerance: HSV容差 (H,S,V)
    :param min_aspect_ratio: 最小宽高比
    :param min_length: 此颜色出现的最小长度(总数)
    :param min_area: 最小面积阈值，用于过滤噪声
    :param morph_kernel_size: 形态学操作核大小，决定了能连接的最大间隙
                              连接断裂区域：将距离较近的相同颜色区域连接起来
                              连接条件：如果两个相同颜色区域之间的空白距离 ≤ 核大小，则被连接
                              填充过程：通过滑动窗口的方式，将小的空白区域用周围的颜色填充
                              处理断层：如果进度条中的颜色有小的断裂（如抗锯齿边缘)
                              连接像素：将这些断开的像素连接成连续区域
                              阈值控制：只有当断层宽度 ≤ 核大小时才会被连接
                              实际效果:
                                - 断层在核大小范围内 → 被连接成连续区域
                                - 断层超过核大小 → 保持分离状态
                                - 不会改变原有区域的外部边界，只是填充内部空隙
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 创建综合掩码
    combined_mask = np.zeros_like(hsv[:, :, 0])

    for rgb in target_rgbs:
        lower_hsv, upper_hsv = _rgb_to_hsv_range(rgb, tolerance)
        single_mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
        combined_mask = cv2.bitwise_or(combined_mask, single_mask)

    # 形态学操作：连接断裂的像素区域
    if morph_kernel_size > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel_size, morph_kernel_size))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)

    # 轮廓检测
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        # 面积过滤：过滤过小的噪声区域
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        if w > h * min_aspect_ratio and w > min_length:
            return True
    return False



