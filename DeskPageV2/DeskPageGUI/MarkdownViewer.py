import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextBrowser, QWidget
from markdown import markdown as md_parser


class MarkdownViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("操作说明")

        self.resize(500, 600)

        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.text_browser)
        central_widget.setLayout(layout)

        self.load_markdown('.\\_internal\\README.md')

    def load_markdown(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = md_parser(md_content)
            self.text_browser.setHtml(html_content)


def main():
    app = QApplication(sys.argv)
    viewer = MarkdownViewer()
    viewer.load_markdown('D:\\SoftWare\\Developed\\Projected\\JiuYinDance\\README.md')  # 替换为你的markdown文件路径
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()