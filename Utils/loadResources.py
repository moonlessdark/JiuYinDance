# encodings: utf-8
"""
资源读取与用户配置读写。

资源路径已经迁移到 Utils/resourceConfig.py 的 ResourcesConfig 对象中，
本文件中的 GetConfig 仅作为兼容层保留，避免一次性修改所有业务模块。
"""
import json
import os.path

from Utils.dataClass import BackpackItem, ChallengePoint2LuckyMoney, DancePicGreen, DancePicGrey, DancePicWhz, \
    DmDll, FindTruckCarTaskNPC, GhostDll, GoodsOptStatus, MapPic, MapPointNum, MarketPic, MyFight, \
    PersonStatusAndBuff, Team, TruckCarPic, TruckCarReceiveTask
from Core.config.paths import PathUtil
from Utils.resourceConfig import ResourcesConfig, get_resources


def _get_dir_map_goods_point_path() -> str:
    """
    地图采集物坐标list
    """
    return PathUtil().get_path_from_resources("mapGoodsPointList.json")


def update_map_goods_point_list(content_list: list):
    """
    更新地图采集物坐标配置文件
    :param content_list
    :return:
    """

    if len(content_list) == 0:
        return None
    if not os.path.exists(_get_dir_map_goods_point_path()):
        file = open(_get_dir_map_goods_point_path(), "w")
        file.close()
    with open(_get_dir_map_goods_point_path(), 'w', encoding="gbk") as file:
        json.dump(content_list, file, ensure_ascii=False, indent=4)
        return None


def get_map_goods_point_list() -> list:
    """
    获取地图资源坐标
    """
    with open(_get_dir_map_goods_point_path(), 'r', encoding="gbk") as f:
        fs = f.read()
        res = json.loads(fs)
        return res


def get_map_goods_point_list_by_selected() -> list:
    """
    查询已经选中的地图路线
    """
    _res: list = get_map_goods_point_list()
    map_point_list = []
    _first_line_point_list: list = []
    for pp in _res:
        is_selected: bool = pp.get("selected")
        _first_line_point_list = pp.get("map_point")
        if not is_selected:
            continue
        map_point_list: list = pp.get("map_point")
    if len(map_point_list) == 0:
        # 如果没有设置采集路线，那么默认那第一个
        map_point_list = _first_line_point_list
    return map_point_list


def _get_dir_skill_group() -> str:
    """
    获取技能组
    """
    return PathUtil().get_path_from_resources("SkillSetting.json")


def get_skill_group_list() -> dict:
    """
    获取技能组
    """
    with open(_get_dir_skill_group(), 'r', encoding="gbk") as f:
        fs = f.read()
        res = json.loads(fs)
        return res


def update_skill_group_list(*args, **kwargs):
    """
    更新配置文件
    :param kwargs: dance_threshold, whz_dance_threshold, is_debug
    :return:
    """
    with open(_get_dir_skill_group(), 'w', encoding="gbk") as file:
        dict_skill = kwargs.get("_skill_dict")
        json.dump(dict_skill, file, ensure_ascii=False, indent=4)


class GetConfig:
    """
    资源路径兼容层。

    真正的数据保存在 Utils/resourceConfig.py 的 ResourcesConfig 单例中，
    这里不再读取 YAML，也不会重复创建路径对象。
    """

    def __init__(self):
        self._resources: ResourcesConfig = get_resources()

    def get_dll_dm(self) -> DmDll:
        """大漠驱动的 dll"""
        return self._resources.dm_dll

    def get_dll_ghost(self) -> GhostDll:
        """幽灵键鼠的 dll"""
        return self._resources.ghost_dll

    def get_dance_grey_pic(self) -> DancePicGrey:
        """团练授业按钮图标"""
        return self._resources.dance_grey

    def get_dance_green_pic(self) -> DancePicGreen:
        """绿色的上下左右，用于漠西风涛"""
        return self._resources.dance_green

    def get_dance_whz_pic(self) -> DancePicWhz:
        """绿色的上下左右，用于挖宝、隐士、势力任务"""
        return self._resources.dance_whz

    def get_backpack_item_pic(self) -> BackpackItem:
        """获取背包中的物品"""
        return self._resources.backpack

    def get_goods_opt_status(self) -> GoodsOptStatus:
        """获取物品操作的状态"""
        return self._resources.opt_status

    def get_map_pic(self) -> MapPic:
        """地图"""
        return self._resources.map_pic

    def get_team(self) -> Team:
        """队伍"""
        return self._resources.team

    def get_track_car(self) -> TruckCarReceiveTask:
        """获取镖车的目的地"""
        return self._resources.truck_car_receive_task

    def truck_task(self) -> TruckCarPic:
        """运镖战斗相关"""
        return self._resources.truck_car_pic

    def find_track_car_task(self) -> FindTruckCarTaskNPC:
        """寻找地图上的接镖 NPC"""
        return self._resources.find_truck_car_task

    def find_person_buff(self) -> PersonStatusAndBuff:
        """右上角人物 buff"""
        return self._resources.person_buff

    def find_person_point(self) -> MapPointNum:
        """人物右上角的坐标值"""
        return self._resources.person_point

    def find_my_fight(self) -> MyFight:
        """我的战斗"""
        return self._resources.my_fight

    def get_market_pic(self) -> MarketPic:
        """世界竞拍"""
        return self._resources.market_pic

    def get_change_2_lucky_money(self) -> ChallengePoint2LuckyMoney:
        """挑战点换幸运硬币"""
        return self._resources.challenge_point_2_lucky_money
