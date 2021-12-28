import cv2
import numpy as np

# from tools.Enum_tools import hash_type as ht


class PictureHashCompare(object):
    """
    3种哈希的差异请查看 https://blog.csdn.net/qq_32799915/article/details/81000437
    """
    def __init__(self):
        self.img_read = None

    def avg_hash(self, img):
        """
        均值哈希算法
        :param img: 图片路径
        :return:
        """

        if isinstance(img, str):
            # img_read = cv2.cv2.imread(img)   # 这个方法无法处理带中文的路径
            self.img_read = cv2.imdecode(np.fromfile(img, dtype=np.uint8), -1)
        else:
            # self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
            self.img_read = img
        # 缩放为8*8
        img_read = cv2.resize(self.img_read, (64, 64), interpolation=cv2.INTER_CUBIC)
        # 转换为灰度图
        gray = cv2.cvtColor(img_read, cv2.COLOR_BGR2GRAY)
        # s为像素和初值为0，hash_str为hash值初值为''
        s = 0
        hash_str = ''
        # 遍历累加求像素和
        for i in range(64):
            for j in range(64):
                s = s + gray[i, j]
        # 求平均灰度
        avg = s / 4096
        # 灰度大于平均值为1相反为0生成图片的hash值
        for i in range(64):
            for j in range(64):
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
            self.img_read = cv2.imdecode(np.fromfile(img, dtype=np.uint8), -1)
        else:
            self.img_read = img
        #     self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        # 缩放65*64
        img_read = cv2.resize(self.img_read, (65, 64), interpolation=cv2.INTER_CUBIC)
        # 转换灰度图
        gray = cv2.cvtColor(img_read, cv2.COLOR_BGR2GRAY)
        hash_str = ''
        # 每行前一个像素大于后一个像素为1，相反为0，生成哈希
        for i in range(64):
            for j in range(64):
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
            self.img_read = cv2.imdecode(np.fromfile(img, dtype=np.uint8), -1)
        else:
            self.img_read = img
        #     self.img_read = cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR)
        self.img_read = cv2.cv2.resize(self.img_read, (32, 32))

        gray = cv2.cv2.cvtColor(self.img_read, cv2.cv2.COLOR_BGR2GRAY)

        dct = cv2.cv2.dct(np.float32(gray))

        dct_roi = dct[0:8, 0:8]

        hash = []
        avreage = np.mean(dct_roi)
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
        return 1 - n / 4096

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
        return num

    # def contrast_hash(self, pic_url_1, pic_url_2, hash_type):
    #     """
    #     2张图片的hash对比
    #     :param pic_url_1: 图片路径1
    #     :param pic_url_2: 图片路径2
    #     :param hash_type: 哈希类型(str)，'感知哈希', '差值哈希', '均值哈希'
    #     :return: 对比结果
    #     """
    #     if hash_type == ht.avg_hash.value:
    #         hash_1 = self.avg_hash(pic_url_1)
    #         hash_2 = self.avg_hash(pic_url_2)
    #         result = self.cmpHash(hash_1, hash_2)
    #         return result
    #     elif hash_type == ht.difference_hash.value:
    #         hash_1 = self.difference_hash(pic_url_1)
    #         hash_2 = self.difference_hash(pic_url_2)
    #         result = self.cmpHash(hash_1, hash_2)
    #         return result
    #     elif hash_type == ht.perception_hash.value:
    #         hash_1 = self.perception_hash(pic_url_1)
    #         hash_2 = self.perception_hash(pic_url_2)
    #         result = self.cmp2hash(hash_1, hash_2)
    #         return result
    #     else:
    #         raise
