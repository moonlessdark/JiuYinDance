from numpy import fromfile, uint8, float32, mean
import cv2


class PictureHashCompare(object):
    """
    3种哈希的差异请查看 https://blog.csdn.net/qq_32799915/article/details/81000437
    """

    def __init__(self):
        self.img_read = None
        self.accuracy_num = 64  # 精准度

    def avg_hash(self, img):
        """
        均值哈希算法
        :param img: 图片路径
        :return:
        """

        if isinstance(img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            self.img_read = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            # self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
            self.img_read = img
        # 缩放为8*8
        # img_read = cv2.resize(self.img_read, (64, 64), interpolation=cv2.INTER_CUBIC)
        img_read = cv2.resize(self.img_read, (self.accuracy_num, self.accuracy_num), interpolation=cv2.INTER_CUBIC)
        # 转换为灰度图
        gray = cv2.cvtColor(img_read, cv2.COLOR_BGR2GRAY)
        # s为像素和初值为0，hash_str为hash值初值为''
        s = 0
        hash_str = ''
        # 遍历累加求像素和
        for i in range(self.accuracy_num):
            for j in range(self.accuracy_num):
                s = s + gray[i, j]
        # 求平均灰度
        avg = s / (self.accuracy_num * self.accuracy_num)
        # 灰度大于平均值为1相反为0生成图片的hash值
        for i in range(self.accuracy_num):
            for j in range(self.accuracy_num):
                if gray[i, j] > avg:
                    hash_str = hash_str + '1'
                else:
                    hash_str = hash_str + '0'
        return hash_str

    def difference_hash(self, img):
        """
        差值感知算法
        :param img: 图片路径
        :return:
        """
        if isinstance(img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            self.img_read = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            self.img_read = img
        #     self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        # 缩放65*64
        # img_read = cv2.resize(self.img_read, (65, 64), interpolation=cv2.INTER_CUBIC)
        img_read = cv2.resize(self.img_read, (self.accuracy_num + 1, self.accuracy_num), interpolation=cv2.INTER_CUBIC)
        # 转换灰度图
        gray = cv2.cvtColor(img_read, cv2.COLOR_BGR2GRAY)
        hash_str = ''
        # 每行前一个像素大于后一个像素为1，相反为0，生成哈希
        for i in range(self.accuracy_num):
            for j in range(self.accuracy_num):
                if gray[i, j] > gray[i, j + 1]:
                    hash_str = hash_str + '1'
                else:
                    hash_str = hash_str + '0'
        return hash_str

    def perception_hash(self, img):
        """
        感知哈希法，准确度最高
        :param img:
        :return:
        """
        if isinstance(img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            self.img_read = cv2.imdecode(fromfile(img, dtype=uint8), -1)
        else:
            self.img_read = img
        #     self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        self.img_read = cv2.resize(self.img_read, (32, 32))

        gray = cv2.cvtColor(self.img_read, cv2.COLOR_BGR2GRAY)

        dct = cv2.dct(float32(gray))

        dct_roi = dct[0:8, 0:8]

        hash = []
        avreage = mean(dct_roi)
        for i in range(dct_roi.shape[0]):
            for j in range(dct_roi.shape[1]):
                if dct_roi[i, j] > avreage:
                    hash.append(1)
                else:
                    hash.append(0)
        return hash

    def cmpHash(self, hash1, hash2):
        """
        #Hash值对比,适用于均值哈希和插值哈希
        :param hash_type:
        :param hash1:
        :param hash2:
        :return:
        """

        n = 0
        # hash长度不同则异常
        assert len(hash1) == len(hash2)
        # 遍历判断
        for i in range(len(hash1)):
            # 不相等则n计数+1，n最终为相似度
            if hash1[i] != hash2[i]:
                n = n + 1
        # return round((len(hash1)-n)*100/len(hash2), 2)
        return round(1 - n / (self.accuracy_num * self.accuracy_num), 2)

    def cmp2hash(self, hash1, hash2):
        """
        感知哈希对比使用该方法
        :param hash1:
        :param hash2:
        :return:
        """
        num = 0
        assert len(hash1) == len(hash2)
        for i in range(len(hash1)):
            if hash1[i] != hash2[i]:
                num += 1
        if num >= 100:
            num = 0
        else:
            # num = (100-num)/100
            num = 1 - num / 1024
        return round(num, 2)


def get_button_area_pic(img):
    """
    使用查找到的轮廓生成ROI剪切图片中感兴趣区域
    :param img: 已经被cv2读取了的图片
    :return:
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)  # 阈值化
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # 寻找轮廓线
    i = 0
    for contour in contours:  # 遍历所有轮廓
        area = cv2.contourArea(contour)  # 轮廓图面积
        if area > 300:  # 轮廓面积大于300的做 mask
            i += 1
    if i == 0:
        return i
    # print("个数为：%d" % (i-1))
    return i - 1
