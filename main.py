import ctypes
import sys

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect
from PySide6.QtWidgets import QMessageBox
import configparser
import os


def load_dpi_config():
    """加载DPI配置"""
    config = configparser.ConfigParser()
    config_file = "app_config.ini"

    if os.path.exists(config_file):
        config.read(config_file)
        return config.getint('display', 'dpi_mode', fallback=2)
    else:
        # 配置文件不存在时弹窗提示用户选择
        return prompt_dpi_mode_selection()


def prompt_dpi_mode_selection():
    """使用tkinter弹窗提示用户选择DPI模式"""
    try:
        import tkinter as tk
        from tkinter import font

        # 创建独立的对话框窗口
        dialog = tk.Tk()
        dialog.title("DPI模式选择")
        dialog.geometry("420x180")
        dialog.resizable(False, False)
        dialog.configure(bg='#f0f0f0')  # 设置背景色

        # 居中显示对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (420 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"420x180+{x}+{y}")

        # 设置窗口为模态
        dialog.attributes('-topmost', True)
        dialog.focus_force()

        # 设置字体
        default_font = font.Font(family="微软雅黑", size=10)
        dialog.option_add("*Font", default_font)

        # 添加消息文本
        label = tk.Label(dialog,
                        text="此选择将影响截图功能的准确性\n游戏默认为'经典模式'\n具体情况请打开游戏启动界面，右下角的'游戏设置'中查看",
                        wraplength=380,
                        justify="left",
                        bg='#f0f0f0',
                        fg='#333333')
        label.pack(pady=(20, 15))

        # 按钮框架
        button_frame = tk.Frame(dialog, bg='#f0f0f0')
        button_frame.pack(pady=15)

        # 返回值变量
        result = tk.IntVar(value=0)

        # 经典模式按钮
        def choose_classic():
            result.set(0)
            dialog.quit()
            dialog.destroy()

        # 极致模式按钮
        def choose_extreme():
            result.set(2)
            dialog.quit()
            dialog.destroy()

        # 创建样式化的按钮
        classic_btn = tk.Button(button_frame,
                               text="经典模式(默认)",
                               command=choose_classic,
                               width=12,
                               height=1,
                               bg='#4CAF50',
                               fg='white',
                               relief='raised',
                               bd=2)
        classic_btn.pack(side=tk.LEFT, padx=15)

        extreme_btn = tk.Button(button_frame,
                               text="极致模式",
                               command=choose_extreme,
                               width=12,
                               height=1,
                               bg='#2196F3',
                               fg='white',
                               relief='raised',
                               bd=2)
        extreme_btn.pack(side=tk.LEFT, padx=15)

        # 处理窗口关闭事件
        def on_closing():
            result.set(0)  # 默认选择经典模式
            dialog.quit()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_closing)

        # 启动事件循环
        dialog.mainloop()

        # 获取用户选择的模式
        mode = result.get()

        # 保存用户选择
        save_dpi_config(mode)
        return mode
    except Exception as e:
        # 如果tkinter不可用，默认返回经典模式
        print(f"创建选择对话框失败: {e}")
        save_dpi_config(0)
        return 0




def save_dpi_config(mode):
    """保存DPI配置"""
    config = configparser.ConfigParser()
    config['display'] = {'dpi_mode': str(mode)}

    with open("app_config.ini", "w") as f:
        config.write(f)


# def switch_dpi_mode(self, mode):
#     """
#     切换DPI模式
#     :param mode: 0=经典模式, 2=极致模式
#     """
#     current_mode = self.get_current_dpi_mode()
#     if current_mode == mode:
#         return
#
#     reply = QMessageBox.question(
#         self, '重启确认',
#         '更改DPI模式需要重启应用才能生效，是否现在重启？',
#         QMessageBox.Yes | QMessageBox.No,
#         QMessageBox.No
#     )
#
#     if reply == QMessageBox.Yes:
#         save_dpi_config(mode)
#         self.restart_application()


def get_current_dpi_mode(self):
    """获取当前DPI模式"""
    return load_dpi_config()


def restart_application(self):
    """重启应用程序"""
    import subprocess
    subprocess.Popen([sys.executable] + sys.argv)
    QApplication.quit()


if __name__ == '__main__':


    # 加载配置并设置DPI感知模式
    dpi_mode: int = load_dpi_config()

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(dpi_mode)
    except Exception as e:
        print(f"设置DPI模式失败: {e}")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = TaskConnect()

    # 可以在界面中显示当前DPI模式
    mode_name = "极致模式" if dpi_mode == 2 else "经典模式"

    w.setWindowTitle(f"九阴日常助手({mode_name})")

    w.log_print(f"更新日期: 2025-12-21\n"
                "更新内容: \n"
                "   新增农夫自动种植(测试版)\n")

    w.show()
    app.exec()