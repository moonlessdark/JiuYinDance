# coding: utf-8
"""
资源路径配置（由原 Resources/FilePath.yaml 迁移而来）。

设计说明：
1. 所有图片、dll 路径集中在本文件中以 Python 对象保存，不再在运行时解析 YAML。
2. ResourcesConfig 只在首次调用 get_resources() 时创建一次，避免各业务类重复
   读取配置文件和重复创建大量 dataclass。
3. 路径统一基于 PathUtil().get_root_path()，兼容源码运行与 PyInstaller 打包运行。
4. 原来的 GetConfig 仍保留在 Utils/loadResources.py 中作为兼容层，业务代码无需
   一次性全部修改。
"""
from __future__ import annotations

from typing import Optional

from Utils.dataClass import (
    BackpackItem,
    ChallengePoint2LuckyMoney,
    DancePicGreen,
    DancePicGrey,
    DancePicWhz,
    DmDll,
    FindTruckCarTaskNPC,
    GhostDll,
    GoodsOptStatus,
    MapPic,
    MapPointNum,
    MarketPic,
    MyFight,
    PersonStatusAndBuff,
    Team,
    TruckCarPic,
    TruckCarReceiveTask,
)
from Core.config.paths import PathUtil

_RESOURCES: Optional["ResourcesConfig"] = None


def _project_root() -> str:
    """获取项目根路径，末尾统一带斜杠。"""
    return PathUtil().get_root_path()


def _res(relative_path: str) -> str:
    """
    将资源相对路径转换为绝对路径。

    :param relative_path: 以斜杠开头，或以 Resources/ 开头的相对路径
    :return: 可直接交给 OpenCV / Win32 读取的绝对路径
    """
    if not relative_path:
        return ""
    path = relative_path.strip().replace("\\", "/")
    # 兼容原 YAML 中同时存在 "/Resources/xx" 和 "Resources/xx" 两种写法
    path = path.lstrip("/")
    return _project_root() + path


class ResourcesConfig:
    """
    全部静态资源路径对象。

    所有 dataclass 只创建一次，字段在创建后不再修改，业务侧只读使用。
    """

    def __init__(self):
        # 幽灵键鼠和大漠驱动
        self.dm_dll = DmDll(
            dll_dm=_res("/Resources/FileDll/dm.dll"),
            dll_dm_reg=_res("/Resources/FileDll/DmReg.dll"),
        )
        self.ghost_dll = GhostDll(
            dll_ghost=_res("/Resources/FileDll/gbild64.dll"),
        )

        # 团练授业按钮
        self.dance_grey = DancePicGrey(
            dance_J=_res("/Resources/ImageTemplate/PicDance/pic_dance_J.png"),
            dance_K=_res("/Resources/ImageTemplate/PicDance/pic_dance_K.png"),
            dance_Down=_res("/Resources/ImageTemplate/PicDance/pic_dance_down_grey.png"),
            dance_Up=_res("/Resources/ImageTemplate/PicDance/pic_dance_up_grey.png"),
            dance_Left=_res("/Resources/ImageTemplate/PicDance/pic_dance_left_grey.png"),
            dance_Right=_res("/Resources/ImageTemplate/PicDance/pic_dance_right_grey.png"),
        )

        # 绿色上下左右（漠西风涛）
        self.dance_green = DancePicGreen(
            dance_Down=_res("/Resources/ImageTemplate/PicDance/pic_dance_down_green.png"),
            dance_Up=_res("/Resources/ImageTemplate/PicDance/pic_dance_up_green.png"),
            dance_Left=_res("/Resources/ImageTemplate/PicDance/pic_dance_left_green.png"),
            dance_Right=_res("/Resources/ImageTemplate/PicDance/pic_dance_right_green.png"),
        )

        # 绿色上下左右（挖宝、隐士、势力任务）
        self.dance_whz = DancePicWhz(
            dance_whz_Down=_res("/Resources/ImageTemplate/PicDance/whz_dance_down.png"),
            dance_whz_Up=_res("/Resources/ImageTemplate/PicDance/whz_dance_up.png"),
            dance_whz_Left=_res("/Resources/ImageTemplate/PicDance/whz_dance_left.png"),
            dance_whz_Right=_res("/Resources/ImageTemplate/PicDance/whz_dance_right.png"),
        )

        # 物品背包
        self.backpack = BackpackItem(
            goods_bag_tag_clickable=_res("/Resources/ImageTemplate/PicItemBackpack/物品-未点击.png"),
            goods_bag_tag_clicked=_res("/Resources/ImageTemplate/PicItemBackpack/物品-已点击.png"),
            material_bag_tag_clickable=_res("/Resources/ImageTemplate/PicItemBackpack/材料-未点击.png"),
            material_bag_tag_clicked=_res("/Resources/ImageTemplate/PicItemBackpack/材料-已点击.png"),
            gift_card=_res("/Resources/ImageTemplate/PicItemBackpack/礼卡.png"),
            run_goods=_res("/Resources/ImageTemplate/PicItemBackpack/御风神水.png"),
            seed=_res("/Resources/ImageTemplate/PicItemBackpack/种子.png"),
            fertilizer=_res("/Resources/ImageTemplate/PicItemBackpack/肥料.png"),
            hidden_realm_item_package=_res("/Resources/ImageTemplate/PicItemBackpack/禁地物品包.png"),
            material_item_package=_res("/Resources/ImageTemplate/PicItemBackpack/杂物包.png"),
        )

        # 人物状态和 buff
        self.person_buff = PersonStatusAndBuff(
            run_goods_ready=_res("/Resources/ImageTemplate/PicPersonBuff/御风神水ready.png"),
            run_goods_buff=_res("/Resources/ImageTemplate/PicPersonBuff/御风神水buff.png"),
            sit_blood=_res("/Resources/ImageTemplate/PicPersonBuff/满血.png"),
            null_blood=_res("/Resources/ImageTemplate/PicPersonBuff/空血条.png"),
        )

        # 物品操作状态
        self.opt_status = GoodsOptStatus(
            open_loading=_res("/Resources/ImageTemplate/PicOptStatus/打开中.png"),
            get_all_goods=_res("/Resources/ImageTemplate/PicOptStatus/全部拾取.png"),
        )

        # 地图
        self.map_pic = MapPic(
            pos_x=_res("/Resources/ImageTemplate/PicMap/pox_x.png"),
            pos_y=_res("/Resources/ImageTemplate/PicMap/pox_y.png"),
            plus_map=_res("/Resources/ImageTemplate/PicMap/plus_map.png"),
            search_pos=_res("/Resources/ImageTemplate/PicMap/search_pos.png"),
            result_point=_res("/Resources/ImageTemplate/PicMap/result_point.png"),
        )

        # 组队
        self.team = Team(
            create_team=_res("/Resources/ImageTemplate/PicTeam/创建队伍.png"),
            leave_team=_res("/Resources/ImageTemplate/PicTeam/离开队伍.png"),
            flag_team=_res("/Resources/ImageTemplate/PicTeam/team_mark.png"),
            flag_team_status=_res("/Resources/ImageTemplate/PicTeam/队伍标志.png"),
        )

        # 右上角坐标数字
        self.person_point = MapPointNum(
            zero=_res("/Resources/ImageTemplate/PicPointNum/0.png"),
            one=_res("/Resources/ImageTemplate/PicPointNum/1.png"),
            two=_res("/Resources/ImageTemplate/PicPointNum/2.png"),
            three=_res("/Resources/ImageTemplate/PicPointNum/3.png"),
            four=_res("/Resources/ImageTemplate/PicPointNum/4.png"),
            five=_res("/Resources/ImageTemplate/PicPointNum/5.png"),
            six=_res("/Resources/ImageTemplate/PicPointNum/6.png"),
            seven=_res("/Resources/ImageTemplate/PicPointNum/7.png"),
            eight=_res("/Resources/ImageTemplate/PicPointNum/8.png"),
            nine=_res("/Resources/ImageTemplate/PicPointNum/9.png"),
            d=_res("/Resources/ImageTemplate/PicPointNum/点.png"),
            f=_res("/Resources/ImageTemplate/PicPointNum/负数.png"),
        )

        # 世界竞拍
        self.market_pic = MarketPic(
            main_line=_res("/Resources/ImageTemplate/PicWorldMarket/Border/main_line.png"),
            follow_line=_res("/Resources/ImageTemplate/PicWorldMarket/Border/my_follow_page.png"),
            ok=_res("/Resources/ImageTemplate/PicWorldMarket/Border/ok.png"),
            plus_price_10=_res("/Resources/ImageTemplate/PicWorldMarket/Border/plus_10.png"),
            plus_price_100=_res("/Resources/ImageTemplate/PicWorldMarket/Border/plus_100.png"),
            summit_price=_res("/Resources/ImageTemplate/PicWorldMarket/Border/summit.png"),
            bidding_man=_res("/Resources/ImageTemplate/PicWorldMarket/Border/竞价者.png"),
            bidder_man=_res("/Resources/ImageTemplate/PicWorldMarket/Border/成交者.png"),
            # 售价数字
            price_zero=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/0.png"),
            price_one=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/1.png"),
            price_two=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/2.png"),
            price_three=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/3.png"),
            price_four=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/4.png"),
            price_five=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/5.png"),
            price_six=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/6.png"),
            price_seven=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/7.png"),
            price_eight=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/8.png"),
            price_nine=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/9.png"),
            price_tag=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/银锭.png"),
            price_ding=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/锭.png"),
            price_liang=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/两.png"),
            price_wen=_res("/Resources/ImageTemplate/PicWorldMarket/SellPrice/文.png"),
            # 残卷
            bing_xin_jue=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/冰心诀残卷.png"),
            gu_pu_can_juan_jue_shi_gao_shou=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/古朴残卷绝世高手.png"),
            tai_ji_quan=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/太极拳残卷.png"),
            han_xiao_jue=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/寒宵诀残卷.png"),
            xin_zhai_mi_lu=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/心斋秘禄残卷.png"),
            da_gou_ba_jue=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/打狗八绝残卷.png"),
            nian_hua_gong=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/拈花功残卷.png"),
            ta_ben=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/拓本碎片.png"),
            wu_wang_shen_gong=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/无妄神功残卷.png"),
            xing_he_jian_lv=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/星河剑律参悟星图.png"),
            xing_he_jian_lv_can_po=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/残破星图.png"),
            du_ha_jing=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/毒哈经残卷.png"),
            hun_yuan_gong=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/混元功残卷.png"),
            fen_tian_ling=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/焚天令残卷.png"),
            ta_ben_ruo_shui_shen_dian=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/若水神典拓本碎片.png"),
            ruo_shui_shen_dian=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/若水神典残卷.png"),
            xue_hai_dao_gang=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/血海刀罡残卷.png"),
            xue_hai_mo_dao_lu=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/血海魔刀录残卷.png"),
            zui_xian_lu=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/醉仙禄残卷.png"),
            mei_ying_jian_fa=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/魅影减法残卷.png"),
            wu_xing_xin_fa=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/五行心法.png"),
            can_yang=_res("/Resources/ImageTemplate/PicWorldMarket/BookFragments/残阳残卷.png"),
            # 道具
            wu_cai_huan=_res("/Resources/ImageTemplate/PicWorldMarket/Props/五彩环.png"),
            ba_zhu_ling=_res("/Resources/ImageTemplate/PicWorldMarket/Props/咫尺烽烟-霸主令.png"),
            jin_yin_hua=_res("/Resources/ImageTemplate/PicWorldMarket/Props/金银花.png"),
            jue_meng_dan=_res("/Resources/ImageTemplate/PicWorldMarket/Props/觉梦丹礼包.png"),
            jiao_hua_ji=_res("/Resources/ImageTemplate/PicWorldMarket/Props/叫花鸡.png"),
        )

        # 挑战点兑换幸运硬币
        self.challenge_point_2_lucky_money = ChallengePoint2LuckyMoney(
            challenge_point_shop_book=_res("/Resources/ImageTemplate/PicLuckyMoney/夺魄勾心刺.png"),
            challenge_point_book_page=_res("/Resources/ImageTemplate/PicLuckyMoney/武学书页.png"),
            challenge_point_exchange_button=_res("/Resources/ImageTemplate/PicLuckyMoney/兑换.png"),
            backpack_item_pic=_res("/Resources/ImageTemplate/PicLuckyMoney/背包中的书页.png"),
            recycle_box=_res("/Resources/ImageTemplate/PicLuckyMoney/回收物品存放栏.png"),
            recycle_box_result=_res("/Resources/ImageTemplate/PicLuckyMoney/可获得的幸运硬币.png"),
            exchange_ok=_res("/Resources/ImageTemplate/PicLuckyMoney/确定兑换幸运硬币.png"),
            exchange_re_ok=_res("/Resources/ImageTemplate/PicLuckyMoney/兑换时的二次确认.png"),
        )


def get_resources() -> ResourcesConfig:
    """
    获取全局唯一的资源路径对象。

    使用单例的原因：资源路径是静态数据，业务层会频繁创建各类查找器，
    如果每次都重新构造会浪费 IO 与对象分配。
    """
    global _RESOURCES
    if _RESOURCES is None:
        _RESOURCES = ResourcesConfig()
    return _RESOURCES
