import os
from enum import Enum

from DeskPage.DeskTools.KeyEnumSoft.project_path import pathUtil

project_path = "D:\\SoftWare\\Dev\\Project\\JiuYinDancingPyside6\\DeskPage"

dev_mode = "Prod"


class IconEnum(Enum):
    if dev_mode == "Debug":
        app_logo = project_path + '/resources/app_logo.ico'
        logo = project_path + '/resources/logo.ico'
        j = project_path+'/resources/j.png'
        k = project_path+'/resources/k.png'
        L = project_path + '/resources/L.png'
        up = project_path+'/resources/up.png'
        down = project_path+'/resources/down.png'
        left = project_path+'/resources/left.png'
        right = project_path+'/resources/right.png'
        whz_dance_up = project_path+'/resources/whzDance_UP.png'
        whz_dance_down = project_path+'/resources/whzDance_Down.png'
        whz_dance_left = project_path+'/resources/whzDance_left.png'
        whz_dance_right = project_path+'/resources/whzDance_right.png'
    else:
        logo = pathUtil().resource_path(os.path.join('res', 'logo.ico'))
        app_logo = pathUtil().resource_path(os.path.join('res', 'app_logo.ico'))
        j = pathUtil().resource_path(os.path.join('res', 'j.png'))
        k = pathUtil().resource_path(os.path.join('res', 'k.png'))
        L = pathUtil().resource_path(os.path.join('res', 'L.png'))
        up = pathUtil().resource_path(os.path.join('res', 'up.png'))
        down = pathUtil().resource_path(os.path.join('res', 'down.png'))
        left = pathUtil().resource_path(os.path.join('res', 'left.png'))
        right = pathUtil().resource_path(os.path.join('res', 'right.png'))
        whz_dance_up = pathUtil().resource_path(os.path.join('res', 'whzDance_UP.png'))
        whz_dance_down = pathUtil().resource_path(os.path.join('res', 'whzDance_Down.png'))
        whz_dance_left = pathUtil().resource_path(os.path.join('res', 'whzDance_left.png'))
        whz_dance_right = pathUtil().resource_path(os.path.join('res', 'whzDance_right.png'))


class DamoTools(Enum):
    if dev_mode == "Debug":
        dm = project_path + '/resources/dm.dll'
        dm_reg = project_path + '/resources/DmReg.dll'
        ghost_dll: str = project_path + '/resources/gbild64.dll'
    else:
        dm: str = pathUtil().resource_path(os.path.join('res', 'dm.dll'))
        dm_reg: str = pathUtil().resource_path(os.path.join('res', 'DmReg.dll'))
        ghost_dll: str = pathUtil().resource_path(os.path.join('res', 'gbild64.dll'))
