from tools.enum_key import icon_enum
from tools.pic_hash import PictureHashCompare


class hashKey:

    def __init__(self):
        self.pic_hash = PictureHashCompare()
        self.origin_hash_dict = None

    def origin_hash(self):

        j = icon_enum.j.value
        k = icon_enum.k.value
        up = icon_enum.up.value
        down = icon_enum.down.value
        left = icon_enum.left.value
        right = icon_enum.right.value

        avg_hash_j = self.pic_hash.avg_hash(j)
        avg_hash_k = self.pic_hash.avg_hash(k)
        avg_hash_up = self.pic_hash.avg_hash(up)
        avg_hash_down = self.pic_hash.avg_hash(down)
        avg_hash_left = self.pic_hash.avg_hash(left)
        avg_hash_right = self.pic_hash.avg_hash(right)

        p_hash_j = self.pic_hash.perception_hash(j)
        p_hash_k = self.pic_hash.perception_hash(k)
        p_hash_up = self.pic_hash.perception_hash(up)
        p_hash_down = self.pic_hash.perception_hash(down)
        p_hash_left = self.pic_hash.perception_hash(left)
        p_hash_right = self.pic_hash.perception_hash(right)

        d_hash_j = self.pic_hash.difference_hash(j)
        d_hash_k = self.pic_hash.difference_hash(k)
        d_hash_up = self.pic_hash.difference_hash(up)
        d_hash_down = self.pic_hash.difference_hash(down)
        d_hash_left = self.pic_hash.difference_hash(left)
        d_hash_right = self.pic_hash.difference_hash(right)

        avg_hash_list = [['j', avg_hash_j], ['k', avg_hash_k], ['up', avg_hash_up], ['down', avg_hash_down],
                         ['left', avg_hash_left], ['right', avg_hash_right]]
        d_hash_list = [['j', d_hash_j], ['k', d_hash_k], ['up', d_hash_up], ['down', d_hash_down],
                       ['left', d_hash_left], ['right', d_hash_right]]
        p_hash_list = [['j', p_hash_j], ['k', p_hash_k], ['up', p_hash_up], ['down', p_hash_down],
                       ['left', p_hash_left], ['right', p_hash_right]]

        self.origin_hash_dict = {"avg_hash_list": avg_hash_list,
                                 "d_hash_list": d_hash_list,
                                 "p_hash_list": p_hash_list}

    def pic_hash_com(self, pic_path_list):
        while True:
            if self.origin_hash_dict is None:
                self.origin_hash()
                break
        keyword_list = []
        # 先计算均值hash
        avg_hash_list = self.origin_hash_dict.get('avg_hash_list')
        d_hash_list = self.origin_hash_dict.get('d_hash_list')
        p_hash_list = self.origin_hash_dict.get('p_hash_list')
        for n in range(len(pic_path_list)):
            for i in range(len(avg_hash_list)):
                name = avg_hash_list[i][0]
                avg_com = self.pic_hash.cmpHash(avg_hash_list[i][1], self.pic_hash.avg_hash(pic_path_list[n]))
                if avg_com > 0.9:
                    d_com = self.pic_hash.cmpHash(d_hash_list[i][1], self.pic_hash.difference_hash(pic_path_list[n]))
                    if d_com > 0.6:
                        p_com = self.pic_hash.cmp2hash(p_hash_list[i][1], self.pic_hash.perception_hash(pic_path_list[n]))
                        if p_com > 0.9:
                            keyword_list.append(p_hash_list[i][0])
                            break
        if len(keyword_list) > 0:
            return keyword_list
        else:
            return None
