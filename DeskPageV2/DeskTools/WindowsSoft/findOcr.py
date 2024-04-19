from numpy import fromfile, uint8
from ppocronnx.predict_system import TextSystem
import cv2

text_sys = TextSystem()


def find_ocr(image, temp_text: str) -> list or None:
    """
    :param image: 需要查找文字的图片
    :param temp_text: 想要再图片中查询的文字
    :return 查找到的第一个匹配的文字的坐标
    """
    if isinstance(image, str):
        # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
        img_read = cv2.imdecode(fromfile(image, dtype=uint8), -1)
    else:
        img_read = image
    res = text_sys.detect_and_ocr(img_read)
    for boxed_result in res:
        if temp_text in boxed_result.ocr_text:
            rect = boxed_result.box
            x_center = (rect[0][0] + rect[2][0])/2
            y_center = (rect[0][1] + rect[2][1])/2
            return [int(x_center), int(y_center)]
    return None
