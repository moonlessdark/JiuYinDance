import os
from enum import Enum
from common.tools.path_tools.project_path import pathUtil


class iconEnum(Enum):
    j = pathUtil().resource_path(os.path.join('res', 'j.png'))
    k = pathUtil().resource_path(os.path.join('res', 'k.png'))
    up = pathUtil().resource_path(os.path.join('res', 'up.png'))
    down = pathUtil().resource_path(os.path.join('res', 'down.png'))
    left = pathUtil().resource_path(os.path.join('res', 'left.png'))
    right = pathUtil().resource_path(os.path.join('res', 'right.png'))
    end_tl = pathUtil().resource_path(os.path.join('res', 'end_icon_by_tl.png'))
    end_sy = pathUtil().resource_path(os.path.join('res', 'end_icon_by_sy.png'))

    # j = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/j.png'
    # k = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/k.png'
    # up = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/up.png'
    # down = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/down.png'
    # left = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/left.png'
    # right = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/right.png'
    # end_tl = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/end_icon_by_tl.png'
    # end_sy = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/end_icon_by_sy.png'


class damo_tools(Enum):
    dm = pathUtil().resource_path(os.path.join('res', 'dm.dll'))
    dm_reg = pathUtil().resource_path(os.path.join('res', 'DmReg.dll'))
    # dm = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/dm.dll'
    # dm_reg = 'D:/SoftWare/SystemTools/dev/project/JiuYinYaBiao/resources/DmReg.dll'
