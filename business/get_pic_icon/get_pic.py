from pictureDiscern.picCoordinate import getCoord
from business.pic_hash_icon.hash_key_comp import hashKey


class getPic:

    def __init__(self):
        self.get_coord = getCoord()
        self.hash = hashKey()

    def get_screen_pic(self, url_path):
        key_img_list = self.get_coord.get_pic_coord(url_path)
        if key_img_list is not None:
            keyword_list_result = self.hash.pic_hash_com(key_img_list)
            print(keyword_list_result)
            return keyword_list_result
        return None
