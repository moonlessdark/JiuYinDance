import dataclasses


@dataclasses.dataclass
class DancePicGrey:
    """
    团练图标
    """
    dance_J: str = dataclasses.field(default_factory=str)
    dance_K: str = dataclasses.field(default_factory=str)
    dance_L: str = dataclasses.field(default_factory=str)
    dance_Down: str = dataclasses.field(default_factory=str)
    dance_Up: str = dataclasses.field(default_factory=str)
    dance_Left: str = dataclasses.field(default_factory=str)
    dance_Right: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class DancePicGreen:
    """
    绿色的团练图标，用于修罗刀和隐士。势力的按钮
    """
    dance_Down: str = dataclasses.field(default_factory=str)
    dance_Up: str = dataclasses.field(default_factory=str)
    dance_Left: str = dataclasses.field(default_factory=str)
    dance_Right: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class DancePicWhz:
    """
    绿色的团练图标，用于修罗刀和隐士。势力的按钮
    """
    dance_whz_Down: str = dataclasses.field(default_factory=str)
    dance_whz_Up: str = dataclasses.field(default_factory=str)
    dance_whz_Left: str = dataclasses.field(default_factory=str)
    dance_whz_Right: str = dataclasses.field(default_factory=str)


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
class BackpackItem:
    """
    物品信息，背包中的物品
    """
    goods_bag_tag_clickable: str = dataclasses.field(default_factory=str)  # 未打开的背包
    goods_bag_tag_clicked: str = dataclasses.field(default_factory=str)  # 已经打开的背包
    gift_card: str = dataclasses.field(default_factory=str)  # 9点开卡的礼卡
    run_goods: str = dataclasses.field(default_factory=str)  # 御风神水


@dataclasses.dataclass
class GoodsOptStatus:
    """
    操作状态
    """
    open_loading: str = dataclasses.field(default_factory=str)  # 物品使用中的进度条
    get_all_goods: str = dataclasses.field(default_factory=str)  # 获取所有物品


@dataclasses.dataclass
class PersonStatusAndBuff:
    """
    人物状态和人物buff
    """
    null_blood: str = dataclasses.field(default_factory=str)  # 残血
    sit_blood: str = dataclasses.field(default_factory=str)  # 满血
    run_goods_ready: str = dataclasses.field(default_factory=str)  # 御风神水(准备中)
    run_goods_buff: str = dataclasses.field(default_factory=str)  # 御风神水(准备完毕)


@dataclasses.dataclass
class MapPic:
    pos_x: str = dataclasses.field(default_factory=str)
    pos_y: str = dataclasses.field(default_factory=str)
    search_pos: str = dataclasses.field(default_factory=str)
    result_point: str = dataclasses.field(default_factory=str)
    plus_map: str = dataclasses.field(default_factory=str)


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

    break_npc_talk: str = dataclasses.field(default_factory=str)  # 退出NPC对话界面

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

    # 金陵
    task_jinlin_MeiHuaMen: str = dataclasses.field(default_factory=str)  # 选择目的地：梅花门
    task_jinlin_HuangJiaLieChang: str = dataclasses.field(default_factory=str)  # 选择目的地：皇家猎场
    task_jinlin_MoChouHu: str = dataclasses.field(default_factory=str)  # 选择目的地：莫愁湖

    # 苏州
    task_suzhou_YongCuiShanZhuang: str = dataclasses.field(default_factory=str)  # 选择目的地：拥翠山庄
    task_suzhou_WuWangMu: str = dataclasses.field(default_factory=str)  # 选择目的地：吴王墓
    task_suzhou_CaiShiChang: str = dataclasses.field(default_factory=str)  # 选择目的地：采石场
    task_suzhou_BaoChuanChang: str = dataclasses.field(default_factory=str)  # 选择目的地：宝船厂

    # 洛阳
    task_luoyang_BaoDuZhai: str = dataclasses.field(default_factory=str)  # 选择目的地：抱犊寨
    task_luoyang_YanMenShiJia: str = dataclasses.field(default_factory=str)  # 选择目的地：燕门世家
    task_luoyang_QinWangFu: str = dataclasses.field(default_factory=str)  # 选择目的地：秦王府


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
    task_monster_target: str = dataclasses.field(default_factory=str)  # 劫匪，数组，有多个判断标志,头像
    task_monster_target_skil: str = dataclasses.field(default_factory=str)  # 劫匪NPC的技能，此时需要格挡
    task_car_selected: str = dataclasses.field(default_factory=str)  # 已经选中了镖车
    fight_other_truck_car: str = dataclasses.field(default_factory=str)  # 镖车切磋


@dataclasses.dataclass
class FindTruckCarTaskNPC:
    """
    寻找运镖NPC
    """
    qin_xiu: str = dataclasses.field(default_factory=str)  # 勤修图标
    qin_xiu_activity_list: str = dataclasses.field(default_factory=str)  # 活动列表
    qin_xiu_truck_car_task: str = dataclasses.field(default_factory=str)  # 日常运镖
    bang_hui: str = dataclasses.field(default_factory=str)  # 按N之后的帮会

    # 成都NPC
    task_point_chengdu: str = dataclasses.field(default_factory=str)
    task_point_chengdu_npc: str = dataclasses.field(default_factory=str)
    # 金陵NPC
    task_point_jinling: str = dataclasses.field(default_factory=str)
    task_point_jinling_npc: str = dataclasses.field(default_factory=str)
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
class Team:
    """
    组队，离开队伍
    """
    create_team: str = dataclasses.field(default_factory=str)
    leave_team: str = dataclasses.field(default_factory=str)
    flag_team: str = dataclasses.field(default_factory=str)
    flag_team_status: str = dataclasses.field(default_factory=str)


@dataclasses.dataclass
class MapPointNum:
    """
    坐标 0-9
    """

    one: str = dataclasses.field(default_factory=str)
    two: str = dataclasses.field(default_factory=str)
    three: str = dataclasses.field(default_factory=str)
    four: str = dataclasses.field(default_factory=str)
    five: str = dataclasses.field(default_factory=str)
    six: str = dataclasses.field(default_factory=str)
    seven: str = dataclasses.field(default_factory=str)
    eight: str = dataclasses.field(default_factory=str)
    nine: str = dataclasses.field(default_factory=str)
    zero: str = dataclasses.field(default_factory=str)
    d: str = dataclasses.field(default_factory=str)  # 逗号
    f: str = dataclasses.field(default_factory=str)  # 负数


@dataclasses.dataclass
class MyFight:
    """
    我的战斗
    """
    my_fight: str = dataclasses.field(default_factory=str)  # 我的战斗
    xuan_ji_mi_jing: str = dataclasses.field(default_factory=str)  # 玄机秘境
    registration_competition: str = dataclasses.field(default_factory=str)  # 玄机秘境-个人报名


@dataclasses.dataclass
class MarketPic:
    # 世界竞拍
    main_line: str = dataclasses.field(default_factory=str)  # 查询定位竞拍界面
    follow_line: str = dataclasses.field(default_factory=str)  # 我的关注
    ok: str = dataclasses.field(default_factory=str)  #  出价后的确认按钮
    plus_price_10: str = dataclasses.field(default_factory=str)  # 加价10两
    plus_price_100: str = dataclasses.field(default_factory=str)  # 加价100两
    summit_price: str = dataclasses.field(default_factory=str)  # 确认出价
    bidding_man: str = dataclasses.field(default_factory=str)  # 竞价人
    bidder_man: str = dataclasses.field(default_factory=str)  # 成交人

    # 价格判断
    price_one: str = dataclasses.field(default_factory=str)
    price_two: str = dataclasses.field(default_factory=str)
    price_three: str = dataclasses.field(default_factory=str)
    price_four: str = dataclasses.field(default_factory=str)
    price_five: str = dataclasses.field(default_factory=str)
    price_six: str = dataclasses.field(default_factory=str)
    price_seven: str = dataclasses.field(default_factory=str)
    price_eight: str = dataclasses.field(default_factory=str)
    price_nine: str = dataclasses.field(default_factory=str)
    price_zero: str = dataclasses.field(default_factory=str)
    price_tag: str = dataclasses.field(default_factory=str)  # 银两的小图标，后面跟着的就是价格了
    price_ding: str = dataclasses.field(default_factory=str)  # 多少锭
    price_liang: str = dataclasses.field(default_factory=str)  # 多少两
    price_wen: str = dataclasses.field(default_factory=str)  # 多少文

    # 商品列表
    # 内功残卷
    bing_xin_jue: str = dataclasses.field(default_factory=str)  # 冰心诀
    du_ha_jing: str = dataclasses.field(default_factory=str)  # 毒哈经
    han_xiao_jue: str = dataclasses.field(default_factory=str)  # 寒宵诀
    hun_yuan_gong: str = dataclasses.field(default_factory=str)  # 混元功
    ruo_shui_shen_dian: str = dataclasses.field(default_factory=str)  # 若水神典
    wu_wang_shen_gong: str = dataclasses.field(default_factory=str)  # 无望神功
    xin_zhai_mi_lu: str = dataclasses.field(default_factory=str)  # 心斋秘箓
    xue_hai_dao_gang: str = dataclasses.field(default_factory=str)  # 血海刀罡
    zui_xian_lu: str = dataclasses.field(default_factory=str)  # 醉仙箓
    wu_xing_xin_fa: str =  dataclasses.field(default_factory=str)  # 醉仙箓
    can_yang: str =  dataclasses.field(default_factory=str)  # 残阳

    # 拓本碎片
    ta_ben_ruo_shui_shen_dian: str = dataclasses.field(default_factory=str)  # 若水神典拓本碎片
    ta_ben: str = dataclasses.field(default_factory=str)  # 拓本碎片

    # 武学残卷
    xing_he_jian_lv: str = dataclasses.field(default_factory=str)  # 星河剑律参悟星图
    xing_he_jian_lv_can_po: str = dataclasses.field(default_factory=str)  # 残破的星河剑律参悟星图
    da_gou_ba_jue: str = dataclasses.field(default_factory=str)  # 打狗棍法
    fen_tian_ling: str = dataclasses.field(default_factory=str)  # 焚天令
    mei_ying_jian_fa: str = dataclasses.field(default_factory=str)  # 魅影剑法
    nian_hua_gong: str = dataclasses.field(default_factory=str)  # 拈花功
    tai_ji_quan: str = dataclasses.field(default_factory=str)  # 太极拳
    xue_hai_mo_dao_lu: str = dataclasses.field(default_factory=str)  # 血海魔刀

    # 其他道具
    wu_cai_huan: str = dataclasses.field(default_factory=str)  # 五彩环
    ba_zhu_ling: str = dataclasses.field(default_factory=str)  # 霸主令
    jin_yin_hua: str = dataclasses.field(default_factory=str)  # 金银花
    jiao_hua_ji: str = dataclasses.field(default_factory=str)  # 叫花鸡
    gu_pu_can_juan_jue_shi_gao_shou: str = dataclasses.field(default_factory=str)  # 古朴残卷-绝世高手
    jue_meng_dan: str = dataclasses.field(default_factory=str)  # 觉梦丹