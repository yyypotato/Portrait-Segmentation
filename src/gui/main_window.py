from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QApplication)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor

from .menu_page import MenuPage
from .seg_page import SegPage
from .help_page import HelpPage
from src.gui.editor.editor_page import EditorPage
from .workbench_page import WorkbenchPage
from .history_page import HistoryPage

class CustomTitleBar(QWidget):
    """
    自定义标题栏：替代系统原本的白色标题栏
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35) # 标题栏高度
        self.setStyleSheet("background-color: #141824; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 0, 0)
        layout.setSpacing(10)

        # 窗口标题 (左侧)
        self.title_label = QLabel("PortraitSeg Tool v1.0")
        self.title_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; font-family: 'Segoe UI';")
        layout.addWidget(self.title_label)
        
        layout.addStretch()

        # 窗口控制按钮 (右侧)
        # 最小化
        self.btn_min = self.create_btn("─", "#141824", "#2d3347")
        self.btn_min.clicked.connect(self.window().showMinimized)
        
        # 最大化/还原
        self.btn_max = self.create_btn("□", "#141824", "#2d3347")
        self.btn_max.clicked.connect(self.toggle_max)
        
        # 关闭 (红色高亮)
        self.btn_close = self.create_btn("✕", "#141824", "#c0392b")
        self.btn_close.clicked.connect(QApplication.instance().quit)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def create_btn(self, text, bg, hover):
        btn = QPushButton(text)
        btn.setFixedSize(45, 35)
        # 只有关闭按钮右上角有圆角，其他没有，为了贴合边缘
        radius = "border-top-right-radius: 10px;" if text == "✕" else ""
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: #a0a5b5;
                border: none;
                font-weight: bold;
                font-size: 14px;
                {radius}
            }}
            QPushButton:hover {{
                background-color: {hover};
                color: white;
            }}
        """)
        return btn

    def toggle_max(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    # --- 核心：实现鼠标拖动窗口 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            self.window_pos = self.window().frameGeometry().topLeft()
            self.is_dragging = True

    def mouseMoveEvent(self, event):
        if hasattr(self, 'is_dragging') and self.is_dragging:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.window().move(self.window_pos + delta)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portrait Segmentation Tool v1.0")
        self.resize(1200, 800)
        
        # 1. 开启无边框模式
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # 开启透明背景 (为了实现圆角)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 2. 创建主容器 (模拟窗口背景)
        central_widget = QWidget()
        # 设置全局背景色和圆角
        central_widget.setStyleSheet("""
            QWidget {
                background-color: #141824; 
                border-radius: 10px;
            }
        """)
        self.setCentralWidget(central_widget)
        
        # 3. 垂直布局：上面是标题栏，下面是内容
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 添加自定义标题栏
        self.title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        # 堆叠窗口部件 (内容区)
        self.stack = QStackedWidget()
        # 内容区不需要圆角，或者被父容器裁切
        self.main_layout.addWidget(self.stack)

        # 初始化各页面
        self.menu_page = MenuPage()
        self.seg_page = SegPage()
        self.editor_page = EditorPage()
        self.help_page = HelpPage()
        # 新增页面初始化
        self.workbench_page = WorkbenchPage()
        self.history_page = HistoryPage()

        self.stack.addWidget(self.menu_page)
        self.stack.addWidget(self.seg_page)
        self.stack.addWidget(self.editor_page)
        self.stack.addWidget(self.help_page)
        # 添加新页面到堆叠部件
        self.stack.addWidget(self.workbench_page)
        self.stack.addWidget(self.history_page)

        self.connect_signals()

    def connect_signals(self):
        # Menu Page Signals
        self.menu_page.go_to_seg.connect(lambda: self.stack.setCurrentWidget(self.seg_page))
        self.menu_page.go_to_editor.connect(lambda: self.stack.setCurrentWidget(self.editor_page))
        self.menu_page.go_to_help.connect(lambda: self.stack.setCurrentWidget(self.help_page))
        
        # 新增：连接工作台和历史记录的跳转信号
        self.menu_page.go_to_workbench.connect(lambda: self.stack.setCurrentWidget(self.workbench_page))
        self.menu_page.go_to_history.connect(lambda: self.stack.setCurrentWidget(self.history_page))
        
        self.menu_page.exit_app.connect(self.close)

        # Seg Page Signals
        self.seg_page.go_back.connect(lambda: self.stack.setCurrentWidget(self.menu_page))

        # Editor Page Signals
        self.editor_page.go_back.connect(lambda: self.stack.setCurrentWidget(self.menu_page))

        # Help Page Signals
        self.help_page.go_back.connect(lambda: self.stack.setCurrentWidget(self.menu_page))
        
        # 新增：连接新页面的返回信号
        self.workbench_page.go_back.connect(lambda: self.stack.setCurrentWidget(self.menu_page))
        self.history_page.go_back.connect(lambda: self.stack.setCurrentWidget(self.menu_page))