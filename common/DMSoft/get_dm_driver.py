from common.DMSoft.DmOperation import GetKeyBordAndMouse, GetWindows
from common.DMSoft.regsvr import reg_dm_soft


class getDM:

    dm = None

    def __init__(self, dm_reg_path: str, dm_path: str):
        """
        免注册调用大漠插件
        :param dm_reg_path: DmReg.dll的路径
        :param dm_path: dm.dll的路径
        """
        self.__class__.dm = reg_dm_soft(dm_reg_path, dm_path)


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
