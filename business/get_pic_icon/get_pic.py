from common.tools.pic_tools.picCoordinate import getCoord
from business.pic_hash_icon.hash_key_comp import hashKey


class getPic:

    def __init__(self):
        self.get_coord = getCoord()
        self.hash = hashKey()

    def get_screen_pic(self, url_path, execute_type):


        key_img_list = self.get_coord.get_pic_coord(url_path)
        if key_img_list is not None and len(key_img_list) > 0:
            keyword_list_result = self.hash.pic_hash_com(key_img_list)
            return keyword_list_result
        else:
            pic_list = self.get_coord.get_end_pic(url_path)
            return self.hash.pic_hash_end_icon_all(pic_list, execute_type)