from deskPage.common.tools.pic_tools.getKeyCount import getPicByWindows


class getCoord(object):
    """
    计算按钮出现的坐标
    """
    def __init__(self):
        self.get_count = getPicByWindows()

    def get_pic_coord(self, img):
        """
        根据图片的按钮个数获取图片坐标
        :param img: 图片内容
        :return:
        """
        a = 735
        b = 775

        pic_count = self.get_count.get_button_area_pic(img)
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
            # key_1 = img[758:798, 839:879]
            # key_2 = img[758:798, 879:919]
            # key_3 = img[758:798, 919:959]
            # key_4 = img[758:798, 959:999]
            # key_5 = img[758:798, 999:1039]
            # key_6 = img[758:798, 1039:1079]

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

    def get_end_pic(self, img):
        """
        结束的标志图片在不在
        :param img:
        :return:
        """
        return self.get_count.get_end_icon(img)
