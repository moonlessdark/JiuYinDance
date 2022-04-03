import cv2

from tools.enum_key import iconEnum
from tools.pic_hash import PictureHashCompare


class hashKey:

    def __init__(self):
        self.pic_hash = PictureHashCompare()
        self.origin_hash_dict = None
        self.end_hash_dict = None
        self.origin_hash()

    def origin_hash(self):
        """
        拼装一下按钮的图片
        :return:
        """
        j = iconEnum.j.value
        k = iconEnum.k.value
        up = iconEnum.up.value
        down = iconEnum.down.value
        left = iconEnum.left.value
        right = iconEnum.right.value
        end_tl = iconEnum.end_tl.value
        end_sy = iconEnum.end_sy.value


        avg_hash_j = self.pic_hash.avg_hash(j)
        avg_hash_k = self.pic_hash.avg_hash(k)
        avg_hash_up = self.pic_hash.avg_hash(up)
        avg_hash_down = self.pic_hash.avg_hash(down)
        avg_hash_left = self.pic_hash.avg_hash(left)
        avg_hash_right = self.pic_hash.avg_hash(right)
        avg_hash_end_tl = self.pic_hash.avg_hash(end_tl)
        avg_hash_end_sy = self.pic_hash.avg_hash(end_sy)

        p_hash_j = self.pic_hash.perception_hash(j)
        p_hash_k = self.pic_hash.perception_hash(k)
        p_hash_up = self.pic_hash.perception_hash(up)
        p_hash_down = self.pic_hash.perception_hash(down)
        p_hash_left = self.pic_hash.perception_hash(left)
        p_hash_right = self.pic_hash.perception_hash(right)
        p_hash_end_tl = self.pic_hash.perception_hash(end_tl)
        p_hash_end_sy = self.pic_hash.perception_hash(end_sy)

        d_hash_j = self.pic_hash.difference_hash(j)
        d_hash_k = self.pic_hash.difference_hash(k)
        d_hash_up = self.pic_hash.difference_hash(up)
        d_hash_down = self.pic_hash.difference_hash(down)
        d_hash_left = self.pic_hash.difference_hash(left)
        d_hash_right = self.pic_hash.difference_hash(right)
        d_hash_end_tl = self.pic_hash.difference_hash(end_tl)
        d_hash_end_sy = self.pic_hash.difference_hash(end_sy)

        avg_hash_list = [['j', avg_hash_j], ['k', avg_hash_k], ['up', avg_hash_up], ['down', avg_hash_down], ['left', avg_hash_left], ['right', avg_hash_right]]
        d_hash_list = [['j', d_hash_j], ['k', d_hash_k], ['up', d_hash_up], ['down', d_hash_down], ['left', d_hash_left], ['right', d_hash_right]]
        p_hash_list = [['j', p_hash_j], ['k', p_hash_k], ['up', p_hash_up], ['down', p_hash_down], ['left', p_hash_left], ['right', p_hash_right]]

        avg_hash_end_tl_list = [['end_tl', avg_hash_end_tl], ['end_sy', avg_hash_end_sy]]
        d_hash_end_tl_list = [['end_tl', d_hash_end_tl], ['end_sy', d_hash_end_sy]]
        p_hash_end_tl_list = [['end_tl', p_hash_end_tl], ['end_sy', p_hash_end_sy]]

        self.origin_hash_dict = {"avg_hash_list": avg_hash_list,
                                 "d_hash_list": d_hash_list,
                                 "p_hash_list": p_hash_list}
        self.end_hash_dict = {"avg_hash_list": avg_hash_end_tl_list,
                              "d_hash_list": d_hash_end_tl_list,
                              "p_hash_list": p_hash_end_tl_list}

    def pic_hash_com(self, pic_path_list):

        if self.origin_hash_dict is None:
            self.origin_hash()

        keyword_list = []
        # 先计算均值hash
        avg_hash_list = self.origin_hash_dict.get('avg_hash_list')
        # d_hash_list = self.origin_hash_dict.get('d_hash_list')
        p_hash_list = self.origin_hash_dict.get('p_hash_list')
        for n in range(len(pic_path_list)):
            for i in range(len(avg_hash_list)):
                avg_com = self.pic_hash.cmpHash(avg_hash_list[i][1], self.pic_hash.avg_hash(pic_path_list[n]))
                if avg_com > 0.90:
                    p_com = self.pic_hash.cmp2hash(p_hash_list[i][1], self.pic_hash.perception_hash(pic_path_list[n]))
                    if p_com > 0.90:
                        keyword_list.append(p_hash_list[i][0])
                        break
        if len(keyword_list) > 0:
            return keyword_list
        else:
            return None

    # def pic_hash_end_icon(self, pic_img_list, execute_type):
    #     """
    #     如果找到了结束团练授业结束图片，就返回true
    #     :param execute_type:
    #     :param pic_img_list:
    #     :return:
    #     """
    #
    #     global avg_pic, d_pic, p_pic
    #     avg_hash_list = self.end_hash_dict.get('avg_hash_list')
    #     d_hash_list = self.end_hash_dict.get('d_hash_list')
    #     p_hash_list = self.end_hash_dict.get('p_hash_list')
    #
    #     if execute_type == "团练模式":
    #         avg_pic = avg_hash_list[0][1]
    #         d_pic = d_hash_list[0][1]
    #         p_pic = p_hash_list[0][1]
    #     else:
    #         avg_pic = avg_hash_list[1][1]
    #         d_pic = d_hash_list[1][1]
    #         p_pic = p_hash_list[1][1]
    #
    #     avg_com = self.pic_hash.cmpHash(avg_pic, self.pic_hash.avg_hash(pic_img_list))
    #     print("avg:%d" % avg_com)
    #     if avg_com > 0.8:
    #         d_com = self.pic_hash.cmpHash(d_pic, self.pic_hash.difference_hash(pic_img_list))
    #         print("d:%d" % d_com)
    #         if d_com > 0.6:
    #             p_com = self.pic_hash.cmp2hash(p_pic, self.pic_hash.perception_hash(pic_img_list))
    #             print("p:%d" % p_com)
    #             if p_com > 0.8:
    #                 return True
    #     return False

    def pic_hash_end_icon_all(self, pic_img_list, execute_type):
        """
        如果找到了结束团练授业结束图片，就返回true
        :param execute_type:
        :param pic_img_list:
        :return:
        """
        end_icon_result = {"团练": False, "授业": False}
        global avg_pic, d_pic, p_pic
        avg_hash_list = self.end_hash_dict.get('avg_hash_list')
        d_hash_list = self.end_hash_dict.get('d_hash_list')
        p_hash_list = self.end_hash_dict.get('p_hash_list')
        for key in pic_img_list:
            if key == "团练" and execute_type == "团练模式":
                avg_pic = avg_hash_list[0][1]
                d_pic = d_hash_list[0][1]
                p_pic = p_hash_list[0][1]
                avg_com = self.pic_hash.cmpHash(avg_pic, self.pic_hash.avg_hash(pic_img_list[key]))
                # print("avg:%s" % str(avg_com))
                if avg_com > 0.8:
                    d_com = self.pic_hash.cmpHash(d_pic, self.pic_hash.difference_hash(pic_img_list[key]))
                    # print("d:%s" % str(d_com))
                    if d_com > 0.6:
                        p_com = self.pic_hash.cmp2hash(p_pic, self.pic_hash.perception_hash(pic_img_list[key]))
                        # print("p:%s" % str(p_com))
                        if p_com > 0.8:
                            end_icon_result.update({"团练": True})
            elif key == "授业" and execute_type == "授业模式":
                avg_pic = avg_hash_list[1][1]
                d_pic = d_hash_list[1][1]
                p_pic = p_hash_list[1][1]
                avg_com = self.pic_hash.cmpHash(avg_pic, self.pic_hash.avg_hash(pic_img_list[key]))
                if avg_com > 0.8:
                    d_com = self.pic_hash.cmpHash(d_pic, self.pic_hash.difference_hash(pic_img_list[key]))
                    if d_com > 0.6:
                        p_com = self.pic_hash.cmp2hash(p_pic, self.pic_hash.perception_hash(pic_img_list[key]))
                        if p_com > 0.8:
                            end_icon_result.update({"授业": True})
        return end_icon_result


if __name__ == "__main__":
    img = cv2.imread("D:\\111.png")  # 载入图像
    imgs = img[30:190, 1735:1795]
    hashKey().pic_hash_end_icon(imgs, "授业模式")