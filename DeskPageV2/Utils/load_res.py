# encodings: utf-8
import yaml

from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic, DmDll, GhostDll, Config
from DeskPageV2.Utils.project_path import PathUtil


def _get_dir_path() -> str:
    """
    获取项目目录
    :return:
    """
    # return PathUtil().get_path_from_resources("../Resources/config.yaml")
    return PathUtil().get_path_from_resources("config.yaml")


def _get_project_path() -> str:
    """
    项目目录
    :return:
    """
    return PathUtil().get_root_path()


class GetConfig:
    def __init__(self):
        fs = open(_get_dir_path(), encoding="UTF-8")
        self.datas = yaml.load(fs, Loader=yaml.FullLoader)  # 添加后就不警告了
        fs.close()
        self.project_dir: str = _get_project_path()

    def get_dance_pic(self) -> DancePic:
        """
        团练授业按钮图标
        :return:
        """
        pic_dance: DancePic = DancePic()
        # 赋值
        pic_dance.dance_area = self.project_dir + self.datas["dancePic"]["button_find_area"]
        pic_dance.dance_area_night = self.project_dir + self.datas["dancePic"]["button_find_area_night"]
        pic_dance.dance_J = self.project_dir + self.datas["dancePic"]["button_j"]
        pic_dance.dance_K = self.project_dir + self.datas["dancePic"]["button_k"]
        pic_dance.dance_L = self.project_dir + self.datas["dancePic"]["button_l"]
        pic_dance.dance_Up = self.project_dir + self.datas["dancePic"]["button_up"]
        pic_dance.dance_Down = self.project_dir + self.datas["dancePic"]["button_down"]
        pic_dance.dance_Left = self.project_dir + self.datas["dancePic"]["button_left"]
        pic_dance.dance_Right = self.project_dir + self.datas["dancePic"]["button_right"]
        return pic_dance

    def get_whz_dance_pic(self) -> WhzDancePic:
        """
        望辉州的图标
        :return:
        """
        whz_dance: WhzDancePic = WhzDancePic()
        # 赋值
        whz_dance.dance_area = self.project_dir + self.datas["whzDancePic"]["button_find_area"]
        whz_dance.dance_Left = self.project_dir + self.datas["whzDancePic"]["button_left"]
        whz_dance.dance_Right = self.project_dir + self.datas["whzDancePic"]["button_right"]
        whz_dance.dance_Up = self.project_dir + self.datas["whzDancePic"]["button_up"]
        whz_dance.dance_Down = self.project_dir + self.datas["whzDancePic"]["button_down"]
        return whz_dance

    def get_dll_dm(self) -> DmDll:
        """
        大漠驱动的dll
        :return:
        """
        dll_dm = DmDll()
        dll_dm.dll_dm = self.project_dir + self.datas["dmDll"]["dm"]
        dll_dm.dll_dm_reg = self.project_dir + self.datas["dmDll"]["dm_reg"]
        return dll_dm

    def get_dll_ghost(self) -> GhostDll:
        """
        幽灵键鼠的dll
        :return:
        """
        ghost_dm = GhostDll()
        ghost_dm.dll_ghost = self.project_dir + self.datas["ghostDll"]["ghost_dll"]
        return ghost_dm

    def get_find_pic_config(self) -> Config:
        """
        读取图片识别的配置
        :return:
        """
        pic_config = Config()
        pic_config.dance_threshold = self.datas["dance_threshold"]
        pic_config.whz_dance_threshold = self.datas["whz_dance_threshold"]
        return pic_config


if __name__ == '__main__':
    s = GetConfig().get_dance_pic()
    print(s)
