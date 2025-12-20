from typing import Optional, Tuple

from Utils.FindWindowsImage import WindowsCapture, PicCapture
from Utils.ImageUtils.FindImageOCR import FindPicOCR
from Utils.loadResources import get_skill_group_list


class FindDaySkillDance:
    """
    隐士、势力的每日演练
    就是使用本门派的武学，跟着NPC出招
    """
    def __init__(self):
        self.ocr = FindPicOCR()
        self._skill_obj: dict = get_skill_group_list().get("演练套路")  # 当前正在使用的技能组
        self.windows_cap = WindowsCapture()

    def find_day_skill_dance(self, hwnd: int) -> Optional[Tuple[str, str, bool]]:
        """
        看看图片中有没有技能名称

        Returns:
            tuple: 包含(press_key, text, need_ground)的三元组，如果未找到则返回None
            - press_key (str): 技能按键
            - text (str): 技能名称
            - need_ground (bool): 是否需要选中地面
        """
        pic: PicCapture = self.windows_cap.capture(hwnd)
        if pic is None:
            return None
        pic_text_list: list = self.ocr.find_ocr_all(pic.pic_content)
        if pic_text_list is None:
            return None
        for pic_text_dict in pic_text_list:
            text = pic_text_dict.ocr_text
            skill_dict: dict = self._skill_obj.get(text)
            if skill_dict is None:
                continue
            press_key: str = skill_dict.get("key")  # 拿到技能明此
            need_ground: bool = skill_dict.get("need_ground")
            return press_key, text, need_ground
        return None

    def find_skill_num(self) -> int:
        """
        看看这个套路有几个技能，技能出完了，任务就可以停止了
        """
        skill_num: int = len(self._skill_obj)
        return skill_num

    def get_skill_group_list(self) -> dict:
        """
        获取技能组
        """
        return self._skill_obj