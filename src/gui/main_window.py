from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from .menu_page import MenuPage
from .seg_page import SegPage
from .help_page import HelpPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portrait Segmentation Tool v1.0")
        self.resize(1000, 700)

        # 堆叠窗口部件，用于管理多页面
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 初始化各个页面
        self.menu_page = MenuPage()
        self.seg_page = SegPage()
        self.help_page = HelpPage()

        # 将页面添加到堆叠窗口
        self.stack.addWidget(self.menu_page) # Index 0
        self.stack.addWidget(self.seg_page)  # Index 1
        self.stack.addWidget(self.help_page) # Index 2

        # 连接信号与槽（页面跳转逻辑）
        self.connect_signals()

        # 默认显示菜单页
        self.stack.setCurrentIndex(0)

    def connect_signals(self):
        # 菜单页信号
        self.menu_page.go_to_seg.connect(lambda: self.stack.setCurrentIndex(1))
        self.menu_page.go_to_help.connect(lambda: self.stack.setCurrentIndex(2))
        self.menu_page.exit_app.connect(self.close)

        # 分割页信号
        self.seg_page.go_back.connect(lambda: self.stack.setCurrentIndex(0))

        # 说明页信号
        self.help_page.go_back.connect(lambda: self.stack.setCurrentIndex(0))