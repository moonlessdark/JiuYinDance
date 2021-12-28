import time
from ctypes import windll
from business.action_keyboad.button_click import buttonClick
from business.windows_screen.get_screen_windows import windowsCap
from business.get_pic_icon.get_pic import getPic
import cv2


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    import cv2
    while True:
        handle = windll.user32.FindWindowW(None, "九阴真经  武侠服专区-侠骨丹心")
        image = windowsCap().capture(handle)
        # cv2.imwrite("10.png", image)
        # cv2.imshow("Capture Test", image)
        # cv2.waitKey()
        # image = cv2.imread("E:/9.png")
        # print("开始 %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        key_list = getPic().get_screen_pic(image)
        if key_list is not None:
            buttonClick().click_key(key_list)
            # print("结束 %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        time.sleep(1)