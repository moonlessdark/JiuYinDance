# encodings: utf-8
import yaml

from DeskPageV2.Utils.dataClass import DancePic, WhzDancePic, DmDll, GhostDll, Config, Team, TruckCarPic, \
    FindTruckCarTaskNPC, TruckCarReceiveTask
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

    def get_find_pic_config(self) -> Config:
        """
        读取图片识别的配置
        :return:
        """
        pic_config = Config()
        pic_config.dance_threshold = self.__datas["config"]["dance_threshold_tl"]
        pic_config.whz_dance_threshold = self.__datas["config"]["dance_threshold_whz"]
        pic_config.area_dance_threshold = self.__datas["config"]["dance_threshold_area"]
        pic_config.is_debug = self.__datas["config"]["debug"]
        return pic_config

    def update_find_pic_config(self, *args, **kwargs):
        """
        更新配置文件
        :param kwargs: dance_threshold, whz_dance_threshold, is_debug

        :return:
        """

        for item_key in kwargs:

            self.__datas["config"][item_key] = kwargs.get(item_key)
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
        team.create_team = self.__datas["team"]["create_team"]
        team.leave_team = self.__datas["team"]["leave_team"]
        team.flag_team = self.__datas["team"]["flag_team"]
        team.flag_team_status = self.__datas["team"]["flag_team_status"]
        return team

    def get_track_car(self):
        """
        获取镖车的目的地
        """
        get_track_car = TruckCarReceiveTask()
        # 寻找NPC并对话
        get_track_car.receive_task_talk = self.__datas["TruckCarFindTask"]["receive_task_talk"]
        # 选择目的地和镖车类型
        get_track_car.receive_task = self.__datas["TruckCarFindTask"]["receive_task"]
        get_track_car.receive_task_confirm = self.__datas["TruckCarFindTask"]["receive_task_confirm"]
        # 成都
        get_track_car.task_chengdu_GaiBang = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["GaiBang"]
        get_track_car.task_chengdu_NanGongShiJia = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["NanGong"]
        get_track_car.task_chengdu_QianDengZheng = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["QianDengZheng"]
        get_track_car.task_chengdu_ShenJiaBao = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["ShenJiaBao"]
        # 燕京
        get_track_car.task_yanjing_DongFangShiJia = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["DongFang"]
        get_track_car.task_yanjing_JiMingYi = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["JiMingYi"]
        get_track_car.task_yanjing_JunMaChang = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["JunMaChang"]
        get_track_car.task_yanjing_YiRenZhuang = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["YiRenZhuang"]
        # 车型
        get_track_car.car_type_little = self.__datas["TruckCarFindTask"]["car_type_little"]
        get_track_car.car_type_medium = self.__datas["TruckCarFindTask"]["car_type_medium"]
        get_track_car.car_type_big = self.__datas["TruckCarFindTask"]["car_type_big"]
        return get_track_car

    def truck_task(self):
        truck = TruckCarPic()
        truck.car_flag = self.__datas["TruckCarPic"]["car_flag"]
        truck.task_flag_status = self.__datas["TruckCarPic"]["task_flag_status"]
        truck.task_flags_yellow_car = self.__datas["TruckCarPic"]["task_flags_yellow_car"]
        truck.task_star_mode = self.__datas["TruckCarPic"]["task_star_mode"]
        truck.task_monster_fight = self.__datas["TruckCarPic"]["task_monster_fight"]
        truck.task_monster_target = self.__datas["TruckCarPic"]["task_monster_target"]
        truck.task_car_selected = self.__datas["TruckCarPic"]["task_car_selected"]
        return truck

    def find_track_car_task(self):
        """
        寻找地图上的接镖NPC
        """
        truck_car_task = FindTruckCarTaskNPC()
        truck_car_task.qin_xiu = self.__datas["TruckCarFindTask"]["qin_xiu"]
        truck_car_task.qin_xiu_activity_list = self.__datas["TruckCarFindTask"]["qin_xiu_activity_list"]
        truck_car_task.qin_xiu_truck_car_task = self.__datas["TruckCarFindTask"]["qin_xiu_truck_car_task"]
        # 成都
        truck_car_task.task_point_chengdu = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["address"]
        truck_car_task.task_point_chengdu_npc = self.__datas["TruckCarFindTask"]["Area"]["chengdu"]["npc"]
        # 燕京
        truck_car_task.task_point_yanjing = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["address"]
        truck_car_task.task_point_yanjing_npc = self.__datas["TruckCarFindTask"]["Area"]["YanJin"]["npc"]
        return truck_car_task


if __name__ == '__main__':
    GetConfig().save_key_even_code_auto_list([123, 123, 123])
    s = GetConfig().get_key_even_code_auto_list()
    print(s)
