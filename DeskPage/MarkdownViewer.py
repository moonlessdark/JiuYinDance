import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QTextBrowser, QWidget, QDialog
from markdown import markdown as md_parser


class MarkdownViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("操作说明")

        self.resize(650, 600)

        self.text_browser = QTextBrowser(self)
        self.text_browser.setReadOnly(True)
        self.text_browser.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_browser)
        self.load_markdown('.\\_internal\\Resources\\Readme\\HelpManual.md')
        #  self.load_markdown(r'D:\SoftWare\Developed\Projected\JiuYinDnaceRemake\HelpManual.md')

    def load_markdown(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = md_parser(md_content)
            self.text_browser.setHtml(html_content)


def main():
    app = QApplication(sys.argv)
    viewer = MarkdownViewer()
    viewer.load_markdown(r'D:\SoftWare\Developed\Projected\JiuYinDnaceRemake\README.md')  # 替换为你的markdown文件路径
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
