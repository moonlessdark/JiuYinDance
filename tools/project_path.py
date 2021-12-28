# 本模块为获取项目根路径的类，为资源文件的读写提供路径帮助
# 感谢 https://www.jianshu.com/p/f7def9c58287

import os
import sys


class pathUtil(object):
    """路径处理工具类"""

    def __init__(self):
        # 判断调试模式
        debug_vars = dict((a, b) for a, b in os.environ.items()
                          if a.find('IPYTHONENABLE') >= 0)
        # 根据不同场景获取根目录
        if len(debug_vars) > 0:
            """当前为debug运行时"""
            self.rootPath = sys.path[2]
        elif getattr(sys, 'frozen', False):
            """当前为exe运行时"""
            self.rootPath = os.getcwd()
        else:
            """正常执行"""
            self.rootPath = sys.path[1]
        # 替换斜杠
        self.rootPath = self.rootPath.replace("\\", "/")

    def get_path_from_resources(self, file_name):
        """按照文件名拼接资源文件路径"""
        file_path = "%s/resources/%s" % (self.rootPath, file_name)
        return file_path

    # 生成资源文件目录访问路径
    def resource_path(self, relative_path):
        if getattr(sys, 'frozen', False):  # 是否Bundle Resource
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
