from deskPage.bussinese.dance.findPicByHashCom.get_pic_icon.getKeyCount import getPicByWindows


class getCoord(object):
    """
    计算按钮出现的坐标
    """
    def __init__(self):
        self.get_count = getPicByWindows()

    def get_pic_coord_1080p(self, img, zoom_ratio: int = 100):
        """
        1080P,100%缩放
        根据图片的按钮个数获取图片坐标
        :param zoom_ratio: 屏幕缩放率，1080p下默认100%
        :param img: 图片内容
        :return:
        """
        a = 735
        b = 775

        pic_count = self.get_count.get_button_area_pic(img, 1080, 100)
        key_coord_list = []
        if pic_count == 0:
            return None
        elif pic_count == 1:
            key = img[a:b, 939:979]
            key_coord_list.append(key)
        elif pic_count == 2:
            # image5 = img[758:798, 919:959]
            # image6 = img[758:798, 959:999]
            c = 919
            for i in range(2):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 3:
            c = 899
            for i in range(3):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 4:
            c = 879
            for i in range(4):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 5:
            c = 859
            for i in range(5):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 6:
            c = 839
            for i in range(6):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 7:
            c = 819
            for i in range(7):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        elif pic_count == 8:
            c = 799
            for i in range(8):
                d = c + 40
                key = img[a:b, c:d]
                c = c + 40
                key_coord_list.append(key)
        else:
            return None
        return key_coord_list

    def get_pic_coord_4k(self, img, zoom_ratio: int):
        """
        4K,150%缩放
        根据图片的按钮个数获取图片坐标
        :param zoom_ratio: 屏幕缩放比率
        :param img: cv2已经读取后的图片内容
        :return:
        """
        key_coord_list = []  # 用于存放计算出来的按钮坐标
        high_top: int = 0  # cv2切图中的上高
        high_down: int = 0  # cv2切图中的下高
        w_left: int = 0  # cv2切图中的左款

        # 根据显示器分辨率缩放比率初始化一下坐标
        if zoom_ratio == 150:  # 如果是150%缩放
            high_top = 975
            high_down = 1015
            w_left = 1259
        elif zoom_ratio == 125:  # 如果是125% 缩放
            high_top = 1167
            high_down = 1207
            w_left = 1515
        pic_count: int = self.get_count.get_button_area_pic(img, screen_resolutions=3840, zoom_ratio=zoom_ratio)

        w_left_screen: int = w_left - (pic_count-1)*20 if pic_count > 1 else w_left

        if pic_count == 0:
            return None
        elif pic_count == 1:
            key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
            key_coord_list.append(key)
        elif pic_count == 2:
            for i in range(2):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 3:
            for i in range(3):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 4:
            for i in range(4):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 5:
            for i in range(5):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 6:
            for i in range(6):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 7:
            for i in range(7):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        elif pic_count == 8:
            for i in range(8):
                key = img[high_top:high_down, w_left_screen:w_left_screen + 40]
                w_left_screen = w_left_screen + 40  # 往右边移动40个像素，去拿下一个按钮图标
                key_coord_list.append(key)
        else:
            return None
        return key_coord_list

    def get_end_pic(self, img):
        """
        结束的标志图片在不在
        :param img:
        :return:
        """
        return self.get_count.get_end_icon(img)
