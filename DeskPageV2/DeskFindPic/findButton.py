import cv2
from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic
from DeskPageV2.Utils.load_res import GetConfig
from DeskPageV2.DeskTools.WindowsSoft.get_windows import find_pic, WindowsCapture, PicCapture


class FindButton:
    """
    大图找小图的方式查找按钮
    """

    config = GetConfig()
    dance_pic: DancePic = config.get_dance_pic()
    whz_dance_pic: WhzDancePic = config.get_whz_dance_pic()

    def __init__(self):
        self.j = cv2.imread(self.dance_pic.dance_J)
        self.k = cv2.imread(self.dance_pic.dance_K)
        self.l = cv2.imread(self.dance_pic.dance_L)
        self.up = cv2.imread(self.dance_pic.dance_Up)
        self.down = cv2.imread(self.dance_pic.dance_Down)
        self.left = cv2.imread(self.dance_pic.dance_Left)
        self.right = cv2.imread(self.dance_pic.dance_Right)

        self.whz_dance_up = cv2.imread(self.whz_dance_pic.dance_Up)
        self.whz_dance_down = cv2.imread(self.whz_dance_pic.dance_Down)
        self.whz_dance_left = cv2.imread(self.whz_dance_pic.dance_Left)
        self.whz_dance_right = cv2.imread(self.whz_dance_pic.dance_Right)

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

    @staticmethod
    def sort_button(button_dict: dict):
        """
        给按钮排序
        :param button_dict:
        :return:
        """
        x_list: list = []
        button_key_list = []
        if len(button_dict) > 0:
            for key in button_dict:
                for bs in button_dict.get(key):
                    x_list.append(bs)
            x_list.sort()  # 排序一下，默认按从小打到
            for n in x_list:
                for kk, vv in button_dict.items():
                    if n in vv:  # 如果该坐标在这个key的value数组中
                        button_key_list.append(kk)
        return button_key_list

    def find_pic_by_bigger(self, bigger_pic_cap: PicCapture, find_type="团练") -> list:
        """
        从大图里面找小图，并进行从左到右排序
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


if __name__ == '__main__':
    import time
    aa = cv2.imread("D:\\SoftWare\\Dev\\Project\\JiuYinDancingPyside6\\56.png", 0)
    pic = cv2.cvtColor(aa, cv2.COLOR_BGR2RGB)

    start_time = time.time()
    pic = WindowsCapture().clear_black_area2(pic)
    end_time = time.time()
    execution_time = end_time - start_time
    print("执行时间为: " + str(execution_time) + "秒")

    start_time = time.time()
    b = FindButton().find_pic_by_bigger(bigger_pic_cap=pic, find_type="团练")
    print(f"查询到的按钮：{b}")
    end_time = time.time()
    execution_time = end_time - start_time
    print("执行时间为: " + str(execution_time) + "秒")
