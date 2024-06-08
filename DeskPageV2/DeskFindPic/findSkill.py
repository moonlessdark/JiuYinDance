# -*- coding: utf-8 -*-
import time

from DeskPageV2.Utils.load_res import GetConfig


class SkillGroup:

    def __init__(self):
        pass

    @staticmethod
    def get_skill(skill: dict) -> str:
        """
        获取可以使用的技能
        """
        # print(f"当前的技能状态是: {skill}")
        local_time = time.time()
        _skill_top: dict = {}
        for skill_name in skill:
            _skill: dict = skill.get(skill_name)
            if _skill.get("click_time") is None:
                # 说明这个按钮还没有按过
                _skill_top.update({_skill.get("level"): skill_name})
            else:
                # 需要判断一下时间，是否CD已经好了
                cd_time = _skill.get("click_time")
                if int(local_time - cd_time) > _skill.get("CD"):
                    _skill_top.update({_skill.get("level"): skill_name})
        # print(f"找到了如下的技能可以使用:{dict(sorted(_skill_top.items()))}")
        _skill_name = None
        if len(_skill_top) > 0:
            _skill_name = _skill_top.get(min(iter(_skill_top.keys())))
        # print(f"检测到可以按下的技能是：{_skill_name}")
        return _skill_name
