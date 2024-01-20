import cv2
from numpy import uint8, fromfile

from DeskPage.DeskTools.KeyEnumSoft.enum_key import IconEnum
from DeskPage.DeskTools.WindowsSoft.get_windows import find_pic


class FindButton:
    """
    大图找小图的方式查找按钮
    """

    def __init__(self):
        self.j = cv2.imdecode(fromfile(IconEnum.j.value, dtype=uint8), -1)
        self.k = cv2.imdecode(fromfile(IconEnum.k.value, dtype=uint8), -1)
        self.l = cv2.imdecode(fromfile(IconEnum.L.value, dtype=uint8), -1)
        self.up = cv2.imdecode(fromfile(IconEnum.up.value, dtype=uint8), -1)
        self.down = cv2.imdecode(fromfile(IconEnum.down.value, dtype=uint8), -1)
        self.left = cv2.imdecode(fromfile(IconEnum.left.value, dtype=uint8), -1)
        self.right = cv2.imdecode(fromfile(IconEnum.right.value, dtype=uint8), -1)
        self.whz_dance_up = cv2.imdecode(fromfile(IconEnum.whz_dance_up.value, dtype=uint8), -1)
        self.whz_dance_down = cv2.imdecode(fromfile(IconEnum.whz_dance_down.value, dtype=uint8), -1)
        self.whz_dance_left = cv2.imdecode(fromfile(IconEnum.whz_dance_left.value, dtype=uint8), -1)
        self.whz_dance_right = cv2.imdecode(fromfile(IconEnum.whz_dance_right.value, dtype=uint8), -1)

    def get_dance_pic(self) -> list:
        """
        团练授业
        先将图标加载到内存中，方便后面调用
        :return:
        """
        return [("J", self.j), ("K", self.k), ("L", self.l), ("UP", self.up), ("Down", self.down), ("Left", self.left), ("Right", self.right)]

    def get_whz_dance_pic(self) -> list:
        """
        获取望辉洲的图片
        :return:
        """
        return [("UP", self.whz_dance_up), ("Down", self.whz_dance_down), ("Left", self.whz_dance_left), ("Right", self.whz_dance_right)]

    def sort_button(self, button_dict: dict):
        """
        给按钮排序
        :param button_dict:
        :return:
        """
        x_list: list = []
        button_key_list = []
        if len(button_dict) > 0:
            for key in button_dict:
                for b in button_dict.get(key):
                    x_list.append(b)
            x_list.sort()  # 排序一下，默认按从小打到
            for n in x_list:
                for kk, vv in button_dict.items():
                    if n in vv:  # 如果该坐标在这个key的value数组中
                        button_key_list.append(kk)
        return button_key_list

    def find_pic_by_bigger(self, bigger_pic_cap: PicCapture, find_type="团练", threshold: float = 0.9) -> list:
        """
        从大图里面找小图，并进行从左到右排序
        :param threshold:
        :param find_type: 查找方式，团练 或者 望辉洲
        :param bigger_pic_cap: 需要找的大图，是已经读取的图片
        :return: list[str]
        """
        bigger_pic = bigger_pic_cap.pic_content
        width = bigger_pic_cap.pic_width
        height = bigger_pic_cap.pic_height
        button_dict = {}

        if width > 0 and height > 0:
            """
            裁剪一下区域，大致把按钮出现的区域放进来
            """
            if find_type == "团练":
                bigger_pic = bigger_pic[int(height * 0.64):int(height * 0.85), int(width * 0.35):int(width * 0.65)]
                threshold = 0.9
            else:
                bigger_pic = bigger_pic[int(height * 0.70):int(height * 0.78), int(width * 0.40):int(width * 0.60)]
                threshold = 0.65

            # cv2.imshow("dd", bigger_pic)
            # cv2.waitKey()

            button_list: list = self.get_dance_pic() if find_type == "团练" else self.get_whz_dance_pic()
            for i in button_list:
                button_num_list: list = find_pic(i[1], bigger_pic, threshold)  # 去界面找一下按钮的坐标
                button_x = []
                for bu in button_num_list:
                    button_x.append(bu[0])  # 把获取到的按钮 x(横坐标) 拿出来，待会要进行排序使用
                if len(button_x) > 0:
                    button_dict[i[0]] = button_x  # {J:[123,456], K:[234,567]}
        return self.sort_button(button_dict)


# if __name__ == '__main__':
#     aa = cv2.imread("D:\SoftWare\Dev\Project\JiuYinDance\\21_31_11.png", 0)
#     aa = cv2.cvtColor(aa, cv2.COLOR_BGR2RGB)
#     b = FindButton().find_pic_by_bigger(bigger_pic=aa, pic_size=[1377, 2560], find_type="sss")
#     print(str(b))
