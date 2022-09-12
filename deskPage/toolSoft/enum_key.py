import os
from enum import Enum

from deskPage.toolSoft.project_path import pathUtil

project_path = "D:/SoftWare/SystemTools/dev/project/JiuYin222/deskPage"


class iconEnum(Enum):
    j = pathUtil().resource_path(os.path.join('res', 'j.png'))
    k = pathUtil().resource_path(os.path.join('res', 'k.png'))
    up = pathUtil().resource_path(os.path.join('res', 'up.png'))
    down = pathUtil().resource_path(os.path.join('res', 'down.png'))
    left = pathUtil().resource_path(os.path.join('res', 'left.png'))
    right = pathUtil().resource_path(os.path.join('res', 'right.png'))

    logo = pathUtil().resource_path(os.path.join('res', 'logo.ico'))

    # j = project_path+'/resources/j.png'
    # k = project_path+'/resources/k.png'
    # up = project_path+'/resources/up.png'
    # down = project_path+'/resources/down.png'
    # left = project_path+'/resources/left.png'
    # right = project_path+'/resources/right.png'
    # logo = project_path+'/resources/logo.ico'


class damo_tools(Enum):
    dm: str = pathUtil().resource_path(os.path.join('res', 'dm.dll'))
    dm_reg: str = pathUtil().resource_path(os.path.join('res', 'DmReg.dll'))

    # dm = project_path+'/resources/dm.dll'
    # dm_reg = project_path+'/resources/DmReg.dll'
