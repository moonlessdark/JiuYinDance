import ctypes
import sys

from PySide6.QtWidgets import QApplication
from DeskFunc.QtConnect.connect import TaskConnect
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
        import ttkbootstrap as ttk
        from ttkbootstrap import Style

        # 创建样式，但不使用会创建主窗口的 Style.master
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        style = Style(theme='flatly')

        # 创建独立的对话框窗口
        dialog = tk.Toplevel(root)
        dialog.title("DPI模式选择")
        dialog.resizable(False, False)

        # 设置窗口为模态
        dialog.transient()
        dialog.grab_set()

        # 居中显示对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (420 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"420x300+{x}+{y}")

        # 主框架
        main_frame = ttk.Frame(dialog, padding="20 20 20 10")
        main_frame.pack(fill="both", expand=True)
        # 添加消息文本
        message_text = ("【特别注意】：\n"
                        "此脚本只支持【经典模式】\n"
                        "【极致模式】将无法使用涉及鼠标相关的功能。谨慎选择。\n\n"
                        "【如何查看自己的游戏设置】：\n"
                        "1： 游戏默认为“经典模式”\n"
                        "2：打开游戏登录界面-->右下角“游戏设置”-->“游戏窗口缩放设置”\n"
                        "游戏的缩放设置需要与此脚本的DPI设置保持一致。不然脚本的识别会出现误差。")
        label = ttk.Label(main_frame,
                          text=message_text,
                          wraplength=380,
                          justify="left",
                          font=("微软雅黑", 10))
        label.pack(pady=(0, 20))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        # 返回值变量
        result = tk.IntVar(value=0)

        # 经典模式按钮
        def choose_classic():
            result.set(0)
            root.quit()
            root.destroy()

        # 极致模式按钮
        def choose_extreme():
            result.set(2)
            root.quit()
            root.destroy()

        # 创建样式化的按钮
        classic_btn = ttk.Button(button_frame,
                                 text="经典模式(推荐使用)",
                                 command=choose_classic,
                                 width=15,
                                 bootstyle="success")  # 绿色主题
        classic_btn.pack(side="left", padx=10)
        extreme_btn = ttk.Button(button_frame,
                                 text="极致模式(不推荐)",
                                 command=choose_extreme,
                                 width=15,
                                 bootstyle="primary")  # 蓝色主题
        extreme_btn.pack(side="left", padx=10)
        # 处理窗口关闭事件
        def on_closing():
            result.set(0)  # 默认选择经典模式
            root.quit()
            root.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_closing)

        # 启动事件循环
        root.mainloop()

        # 获取用户选择的模式
        mode = result.get()

        # 销毁根窗口
        try:
            root.destroy()
        except tk.TclError:
            pass  # 窗口可能已经销毁

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

    w.log_print(f"当前DPI模式: 【{mode_name}】\n请确保游戏游戏设置与此脚本的DPI缩放设置一致。\n")

    w.log_print(f"更新日期: 2026-01-01\n"
                "更新内容: \n"
                "1、修复漠西等级三挖宝识别失败的问题\n"
                "2、修复双开时，9点第一次开卡会失败的问题")

    w.show()
    app.exec()
