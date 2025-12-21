from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QColor
from .styles import Styles

class MenuPage(QWidget):
    # 定义信号，用于通知主窗口切换页面
    go_to_seg = pyqtSignal()
    go_to_editor = pyqtSignal()
    go_to_help = pyqtSignal()
    exit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 使用垂直布局管理器
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # 顶部弹簧
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # 标题
        title = QLabel("人像分割小工具")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(title)

        # 标题下方留白
        layout.addSpacerItem(QSpacerItem(20, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # 按钮容器
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)
        
        # 按钮 1: 进入分割
        self.btn_seg = QPushButton("🚀 开始分割")
        self.btn_seg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_seg.setStyleSheet(Styles.MENU_BUTTON_STYLE)
        self.btn_seg.clicked.connect(self.go_to_seg.emit)

        self.btn_editor = QPushButton("🖌️ 进入编辑器")
        self.btn_editor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editor.setStyleSheet(Styles.MENU_BUTTON_STYLE)
        self.btn_editor.clicked.connect(self.go_to_editor.emit)

        # 按钮 2: 说明
        self.btn_help = QPushButton("📖 使用说明")
        self.btn_help.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_help.setStyleSheet(Styles.MENU_BUTTON_STYLE)
        self.btn_help.clicked.connect(self.go_to_help.emit)

        # 按钮 3: 退出
        self.btn_exit = QPushButton("❌ 退出程序")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.setStyleSheet(Styles.MENU_BUTTON_STYLE)
        self.btn_exit.clicked.connect(self.exit_app.emit)

        # 限制按钮宽度
        btn_container = QWidget()
        btn_container_layout = QVBoxLayout(btn_container)
        btn_container_layout.addWidget(self.btn_seg)
        btn_container_layout.addWidget(self.btn_editor)
        btn_container_layout.addWidget(self.btn_help)
        btn_container_layout.addWidget(self.btn_exit)
        # 让按钮在中间，不要太宽
        btn_container.setFixedWidth(300) 
        
        # 将按钮容器居中添加到主布局
        layout.addWidget(btn_container, 0, Qt.AlignmentFlag.AlignCenter)

        # 底部弹簧
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def paintEvent(self, event):
        """绘制深色渐变背景"""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor("#2d3436"))
        gradient.setColorAt(1.0, QColor("#000000"))
        painter.fillRect(self.rect(), gradient)