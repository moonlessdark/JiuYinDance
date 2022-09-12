from ctypes import windll
from comtypes.client import CreateObject
# from win32com.client import Dispatch


def reg_dm_soft(dm_reg_path: str, dm_path: str):
    """
    免注册调用大漠插件
    :param dm_reg_path: DmReg.dll的路径
    :param dm_path: dm.dll的路径
    """
    # try:
    #     dm = Dispatch('dm.dmsoft')
    #     return dm
    # except:
    #     if dm_reg_path is None or dm_path is None:
    #         return None
    #     try:
    #         dms = windll.LoadLibrary(dm_reg_path)
    #         dms.SetDllPathW(dm_path, 0)
    #         dm = CreateObject('dm.dmsoft')
    #         # print('免注册调用成功 版本号为:', dm.Ver())
    #         return dm
    #     except Exception as e:
    #         return None
    if dm_reg_path is None or dm_path is None:
        return None
    try:
        dms = windll.LoadLibrary(dm_reg_path)
        dms.SetDllPathW(dm_path, 0)
        dm = CreateObject('dm.dmsoft')
        # print('免注册调用成功 版本号为:', dm.Ver())
        return dm
    except Exception as e:
        return None
