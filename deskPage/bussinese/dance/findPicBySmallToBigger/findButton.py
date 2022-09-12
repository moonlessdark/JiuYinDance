import cv2
from deskPage.toolSoft.enum_key import iconEnum
from deskPage.common.windowsSoft.get_windows import find_pic


class FindButton:
    """
    大图找小图的方式查找按钮
    """
    def read_small_pic(self) -> list:
        """
        先将图标加载到内存中，方便后面调用
        :return:
        """
        j = cv2.imread(iconEnum.j.value)
        k = cv2.imread(iconEnum.k.value)
        up = cv2.imread(iconEnum.up.value)
        down = cv2.imread(iconEnum.down.value)
        left = cv2.imread(iconEnum.left.value)
        right = cv2.imread(iconEnum.right.value)
        return [("J", j), ("K", k), ("UP", up), ("Down", down), ("Left", left), ("Right", right)]

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

    def find_pic_by_bigger(self, bigger_pic, pic_size=None) -> list:
        """
        从大图里面找小图，并进行从左到右排序
        :param pic_size: 图片大小 [high, width]
        :param bigger_pic: 需要找的大图，是已经读取的图片
        :return: list[str]
        """
        h = pic_size[0]
        w = pic_size[1]
        if pic_size is not None:
            """
            裁剪一下区域，大致把按钮出现的区域放进来
            """
            bigger_pic = bigger_pic[int(h*0.64):int(h*0.85), int(w*0.35):int(w*0.65)]
        button_list: list = self.read_small_pic()
        button_dict = {}
        for i in button_list:
            button_num_list: list = find_pic(i[1], bigger_pic)  # 去界面找一下按钮的坐标
            button_x = []
            for bu in button_num_list:
                button_x.append(bu[0])  # 把获取到的按钮 x(横坐标) 拿出来，待会要进行排序使用
            if len(button_x) > 0:
                button_dict[i[0]] = button_x  # {J:[123,456], K:[234,567]}
        return self.sort_button(button_dict)
