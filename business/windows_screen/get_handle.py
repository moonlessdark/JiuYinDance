import win32gui


class findHandle(object):

    def find_idx_sub_handle(self, pHandle, winClass, index=0):
        assert type(index) == int and index >= 0
        handle = win32gui.FindWindowEx(pHandle, 0, winClass, None)
        while index > 0:
            handle = win32gui.FindWindowEx(pHandle, handle, winClass, None)
            index -= 1
        return handle

    def find_sub_handle(self, pHandle, winClassList):
        assert type(winClassList) == list
        if len(winClassList) == 1:
            return self.find_idx_sub_handle(pHandle, winClassList[0][0], winClassList[0][1])
        else:
            pHandle = self.find_idx_sub_handle(pHandle, winClassList[0][0], winClassList[0][1])
            return self.find_sub_handle(pHandle, winClassList[1:])


if __name__ == "__main__":
    # my_handle = win32gui.FindWindow("FxMain", None)
    # handle = win32gui.FindWindowEx(None, my_handle, None, "九阴真经  武侠服专区-侠骨丹心")
    my_handle = win32gui.FindWindow(None, '关键字符串.txt - 记事本')
    handle = win32gui.FindWindowEx(None, my_handle, None, '关键字符串.txt - 记事本')
    handle2 = win32gui.FindWindowEx(None, handle, None, '关键字符串.txt - 记事本')
    print(handle)
