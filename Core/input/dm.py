from typing import Optional

from Core.input.dm_operation import GetKeyBordAndMouse, GetWindows
from Core.input.dm_regsvr import reg_dm_soft


class GetDM:

    dm = None

    def __init__(self, dm_reg_path: str, dm_path: str):
        """
        免注册调用大漠插件
        :param dm_reg_path: DmReg.dll的路径
        :param dm_path: dm.dll的路径
        """
        self.__class__.dm = reg_dm_soft(dm_reg_path, dm_path)

    def get_version(self) -> Optional[str]:
        """
        打印版本号
        :return:
        """
        if self.__class__.dm is not None:
            return self.__class__.dm.Ver()
        else:
            return None


class GetKeyBoardMouse(GetKeyBordAndMouse):
    """
    重载键盘鼠标模块
    """
    def __init__(self):
        super().__init__()
        self.get_dm_driver(dm=GetDM.dm)


class GetWindowsOPT(GetWindows):
    def __init__(self):
        super().__init__()
        self.get_dm_driver(dm=GetDM.dm)
