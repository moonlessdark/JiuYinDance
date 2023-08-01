import cv2

from deskPage.bussinese.dance.findPicByHashCom.get_pic_icon.picCoordinate import getCoord
from deskPage.bussinese.dance.findPicByHashCom.pic_hash_icon.hash_key_comp import hashKey


class getPic:

    def __init__(self):
        self.get_coord = getCoord()
        self.hash = hashKey()

    def get_screen_pic(self, url_path, execute_type="团练", resolution_ratio=1920):
        key_img_list = []
        if resolution_ratio == 1920:
            key_img_list = self.get_coord.get_pic_coord_1080p(url_path, 100)
        elif resolution_ratio == 3840:
            key_img_list = self.get_coord.get_pic_coord_4k(url_path, 150)
        if key_img_list is not None and len(key_img_list) > 0:
            keyword_list_result = self.hash.pic_hash_com(key_img_list)
            return keyword_list_result
        # else:
        #     pic_list = self.get_coord.get_end_pic(url_path)
        #     return self.hash.pic_hash_end_icon_all(pic_list, execute_type)


if __name__ == '__main__':
    r = cv2.imread("D://JiuYin/4K_1.png")
    getPic().get_screen_pic(r)