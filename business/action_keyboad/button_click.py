from pydamo_0 import Time, DM, Mouse, Key, vk


class buttonClick(object):

    def click_key(self, key_list):
        pass
        # dm = DM()
        # # dm.reg()     # 后台按键需要注册
        # # dm.reg_infos.unreg_dm()
        #
        # self.ms = Mouse(dm)
        # self.kk = Key(dm)
        # self.tt = Time()
        # if key_list is not None:
        #     for i in range(len(key_list)):
        #         key = key_list[i]
        #         if key == 'j':
        #             self.kk.dp('j')
        #         elif key == 'k':
        #             self.kk.dp('k')
        #         elif key == 'up':
        #             self.kk.dp(38)
        #         elif key == 'down':
        #             self.kk.dp(40)
        #         elif key == 'left':
        #             self.kk.dp(37)
        #         elif key == 'right':
        #             self.kk.dp(39)
        #         else:
        #             self.kk.dp("w")


# dm.Beep()       # 蜂鸣器

if __name__ == "__main__":
    dm = DM()
    ms = Mouse(dm)
    kk = Key(dm)
    tt = Time()
    tt.sleep(3)
    print("开始")
    kk.dp(37)  # 按下a键
    tt.sleep(1)
