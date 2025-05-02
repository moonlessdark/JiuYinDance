# encodings: utf-8
import json

import yaml

from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic, DmDll, GhostDll, Config, Team, TruckCarPic, \
    FindTruckCarTaskNPC, TruckCarReceiveTask, MarketPic, Goods, MapPic, ChengYuPic
from DeskPageV2.Utils.project_path import PathUtil


def _get_dir_path() -> str:
    """
    获取项目目录
    :return:
    """
    # return PathUtil().get_path_from_resources("../Resources/config.yaml")
    return PathUtil().get_path_from_resources("config.yaml")


def _get_dir_key_even_path() -> str:
    """
    获取项目目录
    :return:
    """
    # return PathUtil().get_path_from_resources("../Resources/config.yaml")
    return PathUtil().get_path_from_resources("KeyEvenList.ini")


def _get_dir_skill_group() -> str:
    """
    获取技能组
    """
    return PathUtil().get_path_from_resources("SkillGroup.json")


def _get_project_path() -> str:
    """
    项目目录
    :return:
    """
    return PathUtil().get_root_path()


class GetConfig:
    def __init__(self):
        self.fs = open(_get_dir_path(), encoding="UTF-8")
        self.__datas = yaml.load(self.fs, Loader=yaml.FullLoader)  # 添加后就不警告了
        self.project_dir: str = _get_project_path()

    def __del__(self):
        self.fs.close()

    def get_dance_pic(self) -> DancePic:
        """
        团练授业按钮图标
        :return:
        """
        pic_dance: DancePic = DancePic()
        # 赋值
        pic_dance.dance_area = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_find_area"]
        pic_dance.dance_area_night = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_find_area_night"]
        pic_dance.dance_J = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_j"]
        pic_dance.dance_K = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_k"]
        pic_dance.dance_L = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_l"]
        pic_dance.dance_Up = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_up"]
        pic_dance.dance_Down = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_down"]
        pic_dance.dance_Left = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_left"]
        pic_dance.dance_Right = self.project_dir + self.__datas["dancePic"]["tlDancePic"]["button_right"]
        return pic_dance

    def get_whz_dance_pic(self) -> WhzDancePic:
        """
        望辉州的图标
        :return:
        """
        whz_dance: WhzDancePic = WhzDancePic()
        # 赋值
        whz_dance.dance_area = self.project_dir + self.__datas["dancePic"]["whzDancePic"]["button_find_area"]
        whz_dance.dance_Left = self.project_dir + self.__datas["dancePic"]["whzDancePic"]["button_left"]
        whz_dance.dance_Right = self.project_dir + self.__datas["dancePic"]["whzDancePic"]["button_right"]
        whz_dance.dance_Up = self.project_dir + self.__datas["dancePic"]["whzDancePic"]["button_up"]
        whz_dance.dance_Down = self.project_dir + self.__datas["dancePic"]["whzDancePic"]["button_down"]
        return whz_dance

    def get_dll_dm(self) -> DmDll:
        """
        大漠驱动的dll
        :return:
        """
        dll_dm = DmDll()
        dll_dm.dll_dm = self.project_dir + self.__datas["keyBoardMouseDll"]["dmDll"]["dm"]
        dll_dm.dll_dm_reg = self.project_dir + self.__datas["keyBoardMouseDll"]["dmDll"]["dm_reg"]
        return dll_dm

    def get_dll_ghost(self) -> GhostDll:
        """
        幽灵键鼠的dll
        :return:
        """
        ghost_dm = GhostDll()
        ghost_dm.dll_ghost = self.project_dir + self.__datas["keyBoardMouseDll"]["ghostDll"]["ghost_dll"]
        return ghost_dm

    def get_bag_goods(self) -> Goods:
        """
        获取背包中的物品
        """
        __goods = Goods()
        __goods.goods_bag_tag_clickable = self.project_dir + self.__datas["goods"]["goods_bag_tag_clickable"]
        __goods.goods_bag_tag_clicked = self.project_dir + self.__datas["goods"]["goods_bag_tag_clicked"]
        __goods.run_goods = self.project_dir + self.__datas["goods"]["run_goods"]
        __goods.run_goods_ready = self.project_dir + self.__datas["goods"]["run_goods_ready"]
        __goods.run_goods_buff = self.project_dir + self.__datas["goods"]["run_goods_buff"]
        __goods.null_blood = self.project_dir + self.__datas["goods"]["non_blood"]
        __goods.sit_blood = self.project_dir + self.__datas["goods"]["sit_blood"]
        __goods.gift_card = self.project_dir + self.__datas["goods"]["gift_card"]
        __goods.open_loading = self.project_dir + self.__datas["goods"]["open_loading"]
        __goods.get_all_goods = self.project_dir + self.__datas["goods"]["get_all_goods"]
        return __goods

    def get_find_pic_config(self) -> Config:
        """
        读取图片识别的配置
        :return:
        """
        pic_config = Config()
        pic_config.dance_threshold = self.__datas["danceConfig"]["dance_threshold_tl"]
        pic_config.whz_dance_threshold = self.__datas["danceConfig"]["dance_threshold_whz"]
        pic_config.area_dance_threshold = self.__datas["danceConfig"]["dance_threshold_area"]
        pic_config.is_debug = self.__datas["danceConfig"]["debug"]
        pic_config.truck_car_sum = self.__datas["danceConfig"]["truck_car_max_sum"]
        return pic_config

    def update_find_pic_config(self, *args, **kwargs):
        """
        更新配置文件
        :param kwargs: dance_threshold, whz_dance_threshold, is_debug

        :return:
        """

        for item_key in kwargs:

            self.__datas["danceConfig"][item_key] = kwargs.get(item_key)
            with open(_get_dir_path(), 'w', encoding='utf-8') as f:
                yaml.dump(self.__datas, f, allow_unicode=True)  # allow_unicode=True，解决存储时unicode编码问题。

    @staticmethod
    def get_key_even_code_auto_list():
        """
        获取配置文件中的按钮列表
        :return:
        """
        with open(_get_dir_key_even_path(), "r", encoding="UTF-8") as f:
            res = f.readlines()
            return res[0]

    @staticmethod
    def get_skill_group_list() -> dict:
        """
        获取技能组
        """
        with open(_get_dir_skill_group(), 'r', encoding="gbk") as f:
            fs = f.read()
            res = json.loads(fs)
            return res

    def update_skill_group_list(self, *args, **kwargs):
        """
        更新配置文件
        :param kwargs: dance_threshold, whz_dance_threshold, is_debug

        :return:
        """
        dict_skill: dict = {}
        with open(_get_dir_skill_group(), 'w', encoding="gbk") as file:
            dict_skill["打怪套路"] = kwargs.get("_skill_dict")
            json.dump(dict_skill, file, ensure_ascii=False, indent=4)

    @staticmethod
    def save_key_even_code_auto_list(key_list: list):
        """
        保存配置
        :return:
        """
        try:
            with open(_get_dir_key_even_path(), "w", encoding="UTF-8") as f:
                f.writelines(str(key_list))
                return True
        except RuntimeError as e:
            raise e

    def get_team(self):
        """
        队伍
        """
        team = Team()
        team.create_team = self.project_dir + self.__datas["team"]["create_team"]
        team.leave_team = self.project_dir + self.__datas["team"]["leave_team"]
        team.flag_team = self.project_dir + self.__datas["team"]["flag_team"]
        team.flag_team_status = self.project_dir + self.__datas["team"]["flag_team_status"]
        return team

    def get_track_car(self):
        """
        获取镖车的目的地
        """
        get_track_car = TruckCarReceiveTask()
        # 寻找NPC并对话
        get_track_car.receive_task_talk = self.project_dir + self.__datas["TruckCarFindTask"]["receive_task_talk"]
        # 选择目的地和镖车类型
        get_track_car.receive_task = self.project_dir + self.__datas["TruckCarFindTask"]["receive_task"]
        get_track_car.receive_task_confirm = self.project_dir + self.__datas["TruckCarFindTask"]["receive_task_confirm"]
        # 成都
        get_track_car.task_chengdu_GaiBang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["GaiBang"]
        get_track_car.task_chengdu_NanGongShiJia = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["NanGong"]
        get_track_car.task_chengdu_QianDengZheng = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["QianDengZheng"]
        get_track_car.task_chengdu_ShenJiaBao = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["ShenJiaBao"]
        # 燕京
        get_track_car.task_yanjing_DongFangShiJia = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["DongFang"]
        get_track_car.task_yanjing_JiMingYi = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["JiMingYi"]
        get_track_car.task_yanjing_JunMaChang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["JunMaChang"]
        get_track_car.task_yanjing_YiRenZhuang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["YiRenZhuang"]
        # 苏州
        get_track_car.task_suzhou_YongCuiShanZhuang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["YongCuiShanZhuang"]
        get_track_car.task_suzhou_WuWangMu = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["WuWangMu"]
        get_track_car.task_suzhou_CaiShiChang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["CaiShiChang"]
        get_track_car.task_suzhou_BaoChuanChang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["BaoChuanChang"]
        # 金陵
        get_track_car.task_jinlin_MeiHuaMen = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["JinLing"]["MeiHuaMen"]
        get_track_car.task_jinlin_HuangJiaLieChang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["JinLing"]["HuangJiaLieChang"]
        get_track_car.task_jinlin_MoChouHu = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["JinLing"]["MoChouHu"]
        # 洛阳
        get_track_car.task_luoyang_BaoDuZhai = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["LuoYang"]["BaoDuZhai"]
        get_track_car.task_luoyang_YanMenShiJia = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["LuoYang"]["YanMenShiJia"]
        get_track_car.task_luoyang_QinWangFu = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["LuoYang"]["QinWangFu"]
        # 车型
        get_track_car.car_type_little = self.project_dir + self.__datas["TruckCarFindTask"]["car_type_little"]
        get_track_car.car_type_medium = self.project_dir + self.__datas["TruckCarFindTask"]["car_type_medium"]
        get_track_car.car_type_big = self.project_dir + self.__datas["TruckCarFindTask"]["car_type_big"]
        # npc对话
        get_track_car.break_npc_talk = self.project_dir + self.__datas["TruckCarFindTask"]["break_npc_talk"]
        return get_track_car

    def truck_task(self):
        truck = TruckCarPic()
        truck.car_flag = self.project_dir + self.__datas["TruckCarPic"]["car_flag"]
        truck.task_flag_status = self.project_dir + self.__datas["TruckCarPic"]["task_flag_status"]
        truck.task_flags_yellow_car = self.project_dir + self.__datas["TruckCarPic"]["task_flags_yellow_car"]
        truck.task_star_mode = self.project_dir + self.__datas["TruckCarPic"]["task_star_mode"]
        truck.task_monster_fight = self.project_dir + self.__datas["TruckCarPic"]["task_monster_fight"]
        truck.task_monster_target = self.project_dir + self.__datas["TruckCarPic"]["task_monster_target"]
        truck.task_monster_target_skil = self.project_dir + self.__datas["TruckCarPic"]["task_monster_target_skill"]
        truck.task_car_selected = self.project_dir + self.__datas["TruckCarPic"]["task_car_selected"]
        truck.fight_other_truck_car = self.project_dir + self.__datas["TruckCarPic"]["fight_other_truck_car"]
        return truck

    def map_pic(self) -> MapPic:
        """
        地图
        """
        __map = MapPic()
        __map.pos_x = self.project_dir + self.__datas["MapPic"]["pos_x"]
        __map.pos_y = self.project_dir + self.__datas["MapPic"]["pos_y"]
        __map.search_pos = self.project_dir + self.__datas["MapPic"]["search_pos"]
        __map.result_point = self.project_dir + self.__datas["MapPic"]["result_point"]
        __map.plus_map = self.project_dir + self.__datas["MapPic"]["plus_map"]
        return __map

    def find_track_car_task(self):
        """
        寻找地图上的接镖NPC
        """
        truck_car_task = FindTruckCarTaskNPC()
        truck_car_task.qin_xiu = self.project_dir + self.__datas["TruckCarFindTask"]["qin_xiu"]
        truck_car_task.qin_xiu_activity_list = self.project_dir + self.__datas["TruckCarFindTask"]["qin_xiu_activity_list"]
        truck_car_task.qin_xiu_truck_car_task = self.project_dir + self.__datas["TruckCarFindTask"]["qin_xiu_truck_car_task"]
        truck_car_task.bang_hui = self.project_dir + self.__datas["TruckCarFindTask"]["bang_hui"]

        # 成都
        truck_car_task.task_point_chengdu = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["address"]
        truck_car_task.task_point_chengdu_npc = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["npc"]
        # 燕京
        truck_car_task.task_point_yanjing = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["address"]
        truck_car_task.task_point_yanjing_npc = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["npc"]
        # 金陵
        truck_car_task.task_point_jinling = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["JinLing"]["address"]
        truck_car_task.task_point_jinling_npc = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["JinLing"]["npc"]
        # 苏州
        truck_car_task.task_point_suzhou = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["address"]
        truck_car_task.task_point_suzhou_npc = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["SuZhou"]["npc"]
        # 洛阳
        truck_car_task.task_point_luoyang = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["LuoYang"]["address"]
        truck_car_task.task_point_luoyang_npc = self.project_dir + self.__datas["TruckCarFindTask"]["Area"]["LuoYang"]["npc"]
        return truck_car_task

    def get_market_pic(self) -> MarketPic:
        # 世界竞拍
        __market_pic = MarketPic()
        __market_pic.main_line = self.project_dir + self.__datas["MarketPic"]["main_line"]
        __market_pic.follow_line = self.project_dir + self.__datas["MarketPic"]["follow_line"]
        __market_pic.ok = self.project_dir + self.__datas["MarketPic"]["ok"]
        __market_pic.plus_price_10 = self.project_dir + self.__datas["MarketPic"]["plus_price"]
        __market_pic.plus_price_100 = self.project_dir + self.__datas["MarketPic"]["plus_price_100"]
        __market_pic.summit_price = self.project_dir + self.__datas["MarketPic"]["summit_price"]
        return __market_pic

    def get_chengyu_pic(self) -> ChengYuPic:
        # 成语填空
        __chengyu = ChengYuPic()
        __chengyu.idiom = self.project_dir + self.__datas["ShaMo"]["idiom"]
        __chengyu.up_move = self.project_dir + self.__datas["ShaMo"]["up_move"]
        __chengyu.down_move = self.project_dir + self.__datas["ShaMo"]["down_move"]
        __chengyu.unlock = self.project_dir + self.__datas["ShaMo"]["unlock"]
        __chengyu.l_r_tag = self.project_dir + self.__datas["ShaMo"]["l_r_tag"]
        return __chengyu


if __name__ == '__main__':
    GetConfig().save_key_even_code_auto_list([123, 123, 123])
    s = GetConfig().get_key_even_code_auto_list()
    print(s)
