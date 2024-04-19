import dataclasses


@dataclasses.dataclass
class DancePic:
    """
    团练图标
    """
    dance_area: str = dataclasses.field(default_factory=str)
    dance_area_night: str = dataclasses.field(default_factory=str)
    dance_J: str = dataclasses.field(default_factory=str)
    dance_K: str = dataclasses.field(default_factory=str)
    dance_L: str = dataclasses.field(default_factory=str)
    dance_Down: str = dataclasses.field(default_factory=str)
    dance_Up: str = dataclasses.field(default_factory=str)
    dance_Left: str = dataclasses.field(default_factory=str)
    dance_Right: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class WhzDancePic:
    """
    绿色的团练图标，用于修罗刀和隐士。势力的按钮
    """
    dance_area: str = dataclasses.field(default_factory=str)
    dance_Down: str = dataclasses.field(default_factory=str)
    dance_Up: str = dataclasses.field(default_factory=str)
    dance_Left: str = dataclasses.field(default_factory=str)
    dance_Right: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class DmDll:
    """
    大漠插件
    """
    dll_dm: str = dataclasses.field(default_factory=str)
    dll_dm_reg: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class GhostDll:
    """
    幽灵键鼠
    """
    dll_ghost: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class Team:
    """
    组队，离开队伍
    """
    create_team: str = dataclasses.field(default_factory=str)
    leave_team: str = dataclasses.field(default_factory=str)
    flag_team: str = dataclasses.field(default_factory=str)
    flag_team_status: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class TaskDay:
    """
    日常勤修任务，在这里用于进入押镖
    """
    qin_xiu: str = dataclasses.field(default_factory=str)  # 勤修图标
    truck_car: str = dataclasses.field(default_factory=str)  # 日常运镖
    truck_car_black: str = dataclasses.field(default_factory=str)  # 日常运镖，已经满5次，颜色变灰色
    truck_task_man: list = dataclasses.field(default_factory=list)  # 任务接取人，数组，多个人


@dataclasses.dataclass
class TruckCarReceiveTask:
    """
    接镖
    """
    receive_task_talk: str = dataclasses.field(default_factory=str)  # 接镖_和NPC的对话
    receive_task: str = dataclasses.field(default_factory=str)  # 接镖
    receive_task_confirm: str = dataclasses.field(default_factory=str)  # 确定接镖

    car_type_little: str = dataclasses.field(default_factory=str)  # 镖车类型：小镖车
    car_type_medium: str = dataclasses.field(default_factory=str)  # 镖车类型：中镖车
    car_type_big: str = dataclasses.field(default_factory=str)  # 镖车类型：大镖车

    # 成都
    task_chengdu_GaiBang: str = dataclasses.field(default_factory=str)  # 选择目的地：成都丐帮
    task_chengdu_NanGongShiJia: str = dataclasses.field(default_factory=str)  # 选择目的地：南宫世家
    task_chengdu_QianDengZheng: str = dataclasses.field(default_factory=str)  # 选择目的地：千灯镇
    task_chengdu_ShenJiaBao: str = dataclasses.field(default_factory=str)  # 选择目的地：沈家堡

    # 燕京
    task_yanjing_DongFangShiJia: str = dataclasses.field(default_factory=str)  # 选择目的地：东方世家
    task_yanjing_JiMingYi: str = dataclasses.field(default_factory=str)  # 选择目的地：鸡鸣驿
    task_yanjing_JunMaChang: str = dataclasses.field(default_factory=str)  # 选择目的地：军马场
    task_yanjing_YiRenZhuang: str = dataclasses.field(default_factory=str)  # 选择目的地：异人庄


@dataclasses.dataclass
class TruckCarPic:
    """
    运镖
    """
    car_flag: str = dataclasses.field(default_factory=str)  # 寻找镖车
    task_flag_status: str = dataclasses.field(default_factory=str)  # 运镖状态，有此图标表示任务进行中
    task_flags_yellow_car: str = dataclasses.field(default_factory=str)  # 镖车上的黄色小旗子，用于判断车的位置
    task_star_mode: str = dataclasses.field(default_factory=str)  # 运镖方式，驾车还是赶路
    task_monster_fight: str = dataclasses.field(default_factory=str)  # 进入战斗，劫匪或者垃圾四害
    task_monster_target: list = dataclasses.field(default_factory=list)  # 劫匪，数组，有多个判断标志,头像
    task_car_selected: str = dataclasses.field(default_factory=str)  # 已经选中了镖车


@dataclasses.dataclass
class FindTruckCarTaskNPC:
    """
    寻找运镖NPC
    """
    qin_xiu: str = dataclasses.field(default_factory=str)  # 勤修图标
    qin_xiu_activity_list: str = dataclasses.field(default_factory=str)  # 活动列表
    qin_xiu_truck_car_task: str = dataclasses.field(default_factory=str)  # 日常运镖

    # 成都NPC
    task_point_chengdu: str = dataclasses.field(default_factory=str)
    task_point_chengdu_npc: str = dataclasses.field(default_factory=str)
    # 金陵NPC
    task_point_jinling: str = dataclasses.field(default_factory=str)
    task_point_jingling_npc: str = dataclasses.field(default_factory=str)
    # 洛阳NPC
    task_point_luoyang: str = dataclasses.field(default_factory=str)
    task_point_luoyang_npc: str = dataclasses.field(default_factory=str)
    # 苏州NPC
    task_point_suzhou: str = dataclasses.field(default_factory=str)
    task_point_suzhou_npc: str = dataclasses.field(default_factory=str)
    # 燕京NPC
    task_point_yanjing: str = dataclasses.field(default_factory=str)
    task_point_yanjing_npc: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class Config:
    dance_threshold: float = dataclasses.field(default_factory=float)
    whz_dance_threshold: float = dataclasses.field(default_factory=float)
    area_dance_threshold: float = dataclasses.field(default_factory=float)
    is_debug: bool = dataclasses.field(default_factory=bool)
