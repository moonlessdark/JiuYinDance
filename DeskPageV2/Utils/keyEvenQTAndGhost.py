from enum import Enum

key_even: any = [
    {"key_name": 1, "key_value": 49, "qt_key": 1, "qt_key_value": 49},
    {"key_name": 2, "key_value": 50, "qt_key": 2, "qt_key_value": 50},
    {"key_name": 3, "key_value": 51, "qt_key": 3, "qt_key_value": 51},
    {"key_name": 4, "key_value": 52, "qt_key": 4, "qt_key_value": 52},
    {"key_name": 5, "key_value": 53, "qt_key": 5, "qt_key_value": 53},
    {"key_name": 6, "key_value": 54, "qt_key": 6, "qt_key_value": 54},
    {"key_name": 7, "key_value": 55, "qt_key": 7, "qt_key_value": 55},
    {"key_name": 8, "key_value": 56, "qt_key": 8, "qt_key_value": 56},
    {"key_name": 9, "key_value": 57, "qt_key": 9, "qt_key_value": 57},
    {"key_name": 0, "key_value": 48, "qt_key": 0, "qt_key_value": 48},

    {"key_name": "A", "key_value": 65, "qt_key": "A", "qt_key_value": 65},
    {"key_name": "B", "key_value": 66, "qt_key": "B", "qt_key_value": 66},
    {"key_name": "C", "key_value": 67, "qt_key": "C", "qt_key_value": 67},
    {"key_name": "D", "key_value": 68, "qt_key": "D", "qt_key_value": 68},
    {"key_name": "E", "key_value": 69, "qt_key": "E", "qt_key_value": 69},
    {"key_name": "F", "key_value": 70, "qt_key": "F", "qt_key_value": 70},
    {"key_name": "G", "key_value": 71, "qt_key": "G", "qt_key_value": 71},
    {"key_name": "H", "key_value": 72, "qt_key": "H", "qt_key_value": 72},
    {"key_name": "I", "key_value": 73, "qt_key": "I", "qt_key_value": 73},
    {"key_name": "J", "key_value": 74, "qt_key": "J", "qt_key_value": 74},
    {"key_name": "K", "key_value": 75, "qt_key": "K", "qt_key_value": 75},
    {"key_name": "L", "key_value": 76, "qt_key": "L", "qt_key_value": 76},
    {"key_name": "M", "key_value": 77, "qt_key": "M", "qt_key_value": 77},
    {"key_name": "N", "key_value": 78, "qt_key": "N", "qt_key_value": 78},
    {"key_name": "O", "key_value": 79, "qt_key": "O", "qt_key_value": 79},
    {"key_name": "P", "key_value": 80, "qt_key": "P", "qt_key_value": 80},
    {"key_name": "Q", "key_value": 81, "qt_key": "Q", "qt_key_value": 81},
    {"key_name": "R", "key_value": 82, "qt_key": "R", "qt_key_value": 82},
    {"key_name": "S", "key_value": 83, "qt_key": "S", "qt_key_value": 83},
    {"key_name": "T", "key_value": 84, "qt_key": "T", "qt_key_value": 84},
    {"key_name": "U", "key_value": 85, "qt_key": "U", "qt_key_value": 85},
    {"key_name": "V", "key_value": 86, "qt_key": "V", "qt_key_value": 86},
    {"key_name": "W", "key_value": 87, "qt_key": "W", "qt_key_value": 87},
    {"key_name": "X", "key_value": 88, "qt_key": "X", "qt_key_value": 88},
    {"key_name": "T", "key_value": 89, "qt_key": "Y", "qt_key_value": 89},
    {"key_name": "Z", "key_value": 90, "qt_key": "Z", "qt_key_value": 90},

    {"key_name": "Space", "key_value": 32, "qt_key": "KEY_SPACE", "qt_key_value": 32},
    {"key_name": "Enter", "key_value": 13, "qt_key": "KEY_RETURN", "qt_key_value": 16777220},
    {"key_name": "Esc", "key_value": 27, "qt_key": "KEY_ESC", "qt_key_value": 16777216},
    {"key_name": "BackSpace", "key_value": 8, "qt_key": "KEY_BACKSPACE", "qt_key_value": 16777219},
    {"key_name": "Tab", "key_value": 9, "qt_key": "KEY_TAB", "qt_key_value": 16777217},

    {"key_name": "Ctrl", "key_value": 17, "qt_key": "KEY_CONTROL", "qt_key_value": 16777249},
    {"key_name": "Shift", "key_value": 16, "qt_key": "KEY_SHIFT", "qt_key_value": 16777248},
    {"key_name": "Alt", "key_value": 18, "qt_key": "KEY_ALT", "qt_key_value": 16777251},
    {"key_name": "Win", "key_value": 18, "qt_key": "KEY_META", "qt_key_value": 16777250},  # 单击是不显示的

    {"key_name": "Up", "key_value": 38, "qt_key": "KEY_UP", "qt_key_value": 16777235},
    {"key_name": "Down", "key_value": 40, "qt_key": "KEY_DOWN", "qt_key_value": 16777237},
    {"key_name": "Left", "key_value": 37, "qt_key": "KEY_LEFT", "qt_key_value": 16777234},
    {"key_name": "Right", "key_value": 39, "qt_key": "KEY_RIGHT", "qt_key_value": 16777236},

    {"key_name": "F1", "key_value": 112, "qt_key": "KEY_F1", "qt_key_value": 16777264},
    {"key_name": "F2", "key_value": 113, "qt_key": "KEY_F2", "qt_key_value": 16777265},
    {"key_name": "F3", "key_value": 114, "qt_key": "KEY_F3", "qt_key_value": 16777266},
    {"key_name": "F4", "key_value": 115, "qt_key": "KEY_F4", "qt_key_value": 16777267},
    {"key_name": "F5", "key_value": 116, "qt_key": "KEY_F5", "qt_key_value": 16777268},
    {"key_name": "F6", "key_value": 117, "qt_key": "KEY_F6", "qt_key_value": 16777269},
    {"key_name": "F7", "key_value": 118, "qt_key": "KEY_F7", "qt_key_value": 16777270},
    {"key_name": "F8", "key_value": 119, "qt_key": "KEY_F8", "qt_key_value": 16777271},
    {"key_name": "F9", "key_value": 120, "qt_key": "KEY_F9", "qt_key_value": 16777272},
    {"key_name": "F10", "key_value": 121, "qt_key": "KEY_F10", "qt_key_value": 16777273},
    {"key_name": "F11", "key_value": 122, "qt_key": "KEY_F11", "qt_key_value": 16777274},
    {"key_name": "F12", "key_value": 123, "qt_key": "KEY_F12", "qt_key_value": 16777275}
]


def _get_ghost_key_code(*args):
    """

    :param args: key
    :return:
    """
    ghost_code: list = []
    if args is not None:
        key_even_input = args[0]
        for key in key_even_input:
            for item in key_even:
                if key in item.values():
                    ghost_code.append(item.get("key_value"))
                    break
                """
                如果上面的方法没找到，那么就换个姿势
                """
                key_format: str = key.replace("KEY_", "")
                if key_format.isdigit():
                    key_format = int(key_format)
                if key_format in item.values():
                    ghost_code.append(item.get("key_value"))
                    break
    return ghost_code


def qt_key_get_ghost_key_code(key: str):
    """
    通过Pyside6获取的键盘key_name获取对应 幽灵键鼠的 code
    :param key:
    :return:
    """

    res_list: list = []
    if "+" in key:
        key = key.split("+")
    if type(key) is str:
        key = [key]
    res_key: list = _get_ghost_key_code(key)
    if len(res_key) == len(key):
        res_list = res_key
    return res_list


def check_ghost_code_is_def(key_list: list) -> list:
    """
    检查QT输入的key是否存在于我的表格
    :return: 全部都在就返回个空数组
    """
    res_list: list = []

    for key_line in key_list:
        if "+" in key_line:
            key_line = key_line.split("+")
        if type(key_line) is str:
            key_line = [key_line]
        for key_name in key_line:
            res_key: list = _get_ghost_key_code(key_name)
            if len(res_key) == 0:
                res_list.append(key_name)
    return res_list


if __name__ == '__main__':
    print(qt_key_get_ghost_key_code("KEY_CONTROL+KEY_2"))
