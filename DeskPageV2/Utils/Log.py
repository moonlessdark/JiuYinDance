import os.path
import stat
import time


class Logger:

    def __init__(self):
        self.__log_dir = None

    @property
    def __exist_log_path(self) -> str:
        """
        检测配置文件是否存在，不存在就新建
        """
        now: str = time.strftime("%Y_%m_%d", time.localtime())
        log_file_path = f'./Log/{now}.log'
        if not os.path.exists(log_file_path):
            """
            如果文件目录不存在
            """
            if not os.path.exists("./Log"):
                os.makedirs("./Log")
            text_file = open(log_file_path, "w")
            os.chmod(log_file_path, stat.S_IRWXU)
            text_file.close()
        return log_file_path

    def write_log(self, log_str: str):
        """
        写入日志
        """
        if self.__log_dir is None:
            self.__log_dir = self.__exist_log_path  # 文件路径
        with open(self.__log_dir, 'a') as file:
            now_time: str = time.strftime("%H:%M:%S", time.localtime())
            file.write(f"{now_time}: {log_str} " + '\n')
