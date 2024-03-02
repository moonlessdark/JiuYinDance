from DeskPageV2.DeskTools.DmSoft.dm_operation import GetKeyBordAndMouse, GetWindows
from DeskPageV2.DeskTools.DmSoft.regsvr import reg_dm_soft


class getDM:

    dm = None

    def __init__(self, dm_reg_path: str, dm_path: str):
        """
        免注册调用大漠插件
        :param dm_reg_path: DmReg.dll的路径
        :param dm_path: dm.dll的路径
        """
        self.__class__.dm = reg_dm_soft(dm_reg_path, dm_path)

    def get_version(self) -> str or None:
        """
        打印版本号
        :return:
        """
        if self.__class__.dm is not None:
            return self.__class__.dm.Ver()
        else:
            return None


class getKeyBoardMouse(GetKeyBordAndMouse):
    """
    重载键盘鼠标模块
    """
    def __init__(self):
        super(getKeyBoardMouse).__init__()
        self.get_dm_driver(dm=getDM.dm)


class getWindows(GetWindows):
    def __init__(self):
        super(getWindows).__init__()
        self.get_dm_driver(dm=getDM.dm)
