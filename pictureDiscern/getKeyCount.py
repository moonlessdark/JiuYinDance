import cv2


class getCountByPic(object):

    def get_count(self, img):
        """

        :param img: 已经被cv2读取了的图片
        :return:
        """
        """使用查找到的轮廓生成ROI剪切图片中感兴趣区域"""
        # img = cv2.imread(pic_path_list)  # 载入图像
        img = img[735:775, 740:1180]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, binary = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)  # 阈值化
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # 寻找轮廓线
        i = 0
        for contour in contours:  # 遍历所有轮廓
            area = cv2.contourArea(contour)  # 轮廓图面积
            if (area > 300):  # 轮廓面积大于300的做 mask
                i += 1
        if i == 0:
            return i
        print("个数为：%d" % (i-1))
        return i - 1


if __name__ == '__main__':
    getCountByPic().get_count("D:/12.png")