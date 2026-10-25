from PySide6.QtCore import QThread, Signal
from pynput import mouse


class GlobalMouseListener(QThread):
    middle_clicked = Signal()  # 信号，当检测到中键点击时发出

    def __init__(self):
        super().__init__()
        self.listener = None

    def run(self):
        # 创建鼠标监听器
        # print("开始监听")
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        self.listener.join()

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.middle and pressed:
            # print("中键被点击")
            self.middle_clicked.emit()  # 发出信号

    def stop(self):
        if self.listener:
            self.listener.stop()
