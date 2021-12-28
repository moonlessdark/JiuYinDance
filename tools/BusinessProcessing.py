import os
import time

from tools.pic_hash import PictureHashCompare
from tools.file_opt import fileOpt
from businese.online_businese.get_element import GetHsexElement


class executeElement(GetHsexElement):



    def goto_picture(self):
        """
        开始处理页面上的图片
        :param ip_port: 代理ip端口
        :param log_path_flor: 日志存放的文件夹路径
        :param origin_pic_path: 源图片路径
        :param url: paseNum的url
        :param page_num: 第几页
        :return: 
        """
        video_dict = self.get_pic_and_title(url, ip_port)
        if video_dict is not None:
            title_list = list(video_dict.get('title'))
            url_list = list(video_dict.get('pic_url'))
            author_list = list(video_dict.get('author'))

            avg_origin_hash = self.pic_cmp.avg_hash(origin_pic_path)

            for i in range(0, len(url_list)):
                pic_name = title_list[i]
                pic_url = url_list[i]
                author = author_list[i]

                url_content = self.get_pic_content(url=pic_url)
                if url_content is not None:
                    avg_target_hash = self.pic_cmp.avg_hash(url_content)
                    avg_hash = self.pic_cmp.cmpHash(avg_origin_hash, avg_target_hash)

                    if avg_hash > 0.70:
                        # 计算差值hash
                        d_origin_hash = self.pic_cmp.difference_hash(origin_pic_path)
                        d_target_hash = self.pic_cmp.difference_hash(url_content)
                        d_hash = self.pic_cmp.cmpHash(d_origin_hash, d_target_hash)
                        if d_hash > 0.70:
                            # 计算感知哈希
                            p_origin_hash = self.pic_cmp.perception_hash(origin_pic_path)
                            p_target_hash = self.pic_cmp.perception_hash(url_content)
                            p_hash = self.pic_cmp.cmp2hash(p_origin_hash, p_target_hash)
                            if p_hash > 0.70:
                                new_line = "[相似度高]视频名：" + pic_name + " 上传者：" + author + " 视频封面url: " + pic_url
                                with open(log_path_flor, 'a+') as f:
                                    f.writelines(new_line + '\n')
                                f.close()
                else:
                    new_line = "[请求异常]视频名：" + pic_name + " 上传者：" + author + " 视频封面url: " + pic_url
                    with open(log_path_flor, 'a+') as f:
                        f.writelines(new_line + '\n')
                    f.close()
            new_line = "[请求完成]url: " + url + " 的页面信息已经全部处理完了"
            with open(log_path_flor, 'a+') as f:
                f.writelines(new_line + '\n')
            f.close()
        else:
            new_line = "[请求异常]url: " + url + " 未能获取到页面信息"
            with open(log_path_flor, 'a+') as f:
                f.writelines(new_line + '\n')
            f.close()
