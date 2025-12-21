from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QGraphicsDropShadowEffect, QLineEdit, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QColor, QPixmap, QPainter

class MenuPage(QWidget):
    go_to_seg = pyqtSignal()
    go_to_editor = pyqtSignal()
    go_to_help = pyqtSignal()
    exit_app = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MenuPage")
        # 全局样式
        self.setStyleSheet("""
            QWidget#MenuPage {
                background-color: #141824; 
            }
            QLabel {
                font-family: 'Microsoft YaHei', 'Segoe UI';
                color: #ffffff;
            }
            QLineEdit {
                background-color: #1f2435;
                border: 1px solid #2b3042;
                border-radius: 18px;
                color: #a0a5b5;
                padding: 0 15px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00f2ea;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(30)

        # --- 1. 顶部导航栏 (优化版) ---
        top_bar = QHBoxLayout()
        top_bar.setSpacing(0) # 手动控制间距
        
        # Logo 区域
        logo_box = QHBoxLayout()
        logo_box.setSpacing(12)
        
        logo_icon = QLabel("◎") 
        logo_icon.setStyleSheet("color: #00f2ea; font-size: 36px; font-weight: bold;")
        
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("人像分割工具箱")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: 1px;")
        subtitle = QLabel("AI PORTRAIT STUDIO")
        subtitle.setStyleSheet("font-size: 10px; font-weight: bold; color: #5c6375; letter-spacing: 2px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        
        logo_box.addWidget(logo_icon)
        logo_box.addLayout(title_box)
        
        # 导航菜单 (增加间距和选中态)
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(30)
        
        nav_1 = QLabel("首页")
        nav_1.setCursor(Qt.CursorShape.PointingHandCursor)
        nav_1.setStyleSheet("""
            font-size: 16px; font-weight: bold; color: #ffffff; 
            border-bottom: 3px solid #00f2ea; padding-bottom: 6px;
        """)
        
        nav_2 = QLabel("工作台")
        nav_2.setStyleSheet("font-size: 16px; color: #7d8394; padding-bottom: 6px;")
        
        nav_3 = QLabel("云端历史")
        nav_3.setStyleSheet("font-size: 16px; color: #7d8394; padding-bottom: 6px;")
        
        nav_layout.addWidget(nav_1)
        nav_layout.addWidget(nav_2)
        nav_layout.addWidget(nav_3)

        # 搜索框
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 搜索功能 / 滤镜...")
        search_bar.setFixedSize(240, 40)

        # 组装顶部
        top_bar.addLayout(logo_box)
        top_bar.addSpacing(60) # Logo与导航的间距
        top_bar.addLayout(nav_layout)
        top_bar.addStretch()
        top_bar.addWidget(search_bar)

        # --- 2. 中间卡片区 (修复高度问题) ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        # 卡片 1
        self.card_seg = self.create_gamer_card(
            "智能抠图", 
            "AI 自动移除背景\n发丝级精细分割", 
            "resources/icons/seg_icon.png",
            is_primary=True
        )
        self.card_seg.clicked.connect(self.go_to_seg.emit)

        # 卡片 2
        self.card_edit = self.create_gamer_card(
            "图像精修", 
            "专业调色 / 滤镜\n光效合成工作台", 
            "resources/icons/edit_icon.png",
            is_primary=False
        )
        self.card_edit.clicked.connect(self.go_to_editor.emit)

        cards_layout.addWidget(self.card_seg)
        cards_layout.addWidget(self.card_edit)

        # --- 3. 底部功能块 ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(25)

        # 状态面板
        status_panel = QFrame()
        status_panel.setStyleSheet("background-color: #1f2435; border-radius: 16px;")
        status_panel.setFixedHeight(110)
        
        sp_layout = QHBoxLayout(status_panel)
        sp_layout.setContentsMargins(30, 0, 30, 0)
        
        # 状态图标
        stat_icon = QLabel("🚀")
        stat_icon.setStyleSheet("font-size: 32px;")
        
        stat_text = QLabel("AI 引擎已就绪\n<span style='color:#00f2ea;'>GPU 加速开启中 (CUDA 11.8)</span>")
        stat_text.setStyleSheet("font-size: 14px; color: #a0a5b5; line-height: 20px;")
        
        sp_layout.addWidget(stat_icon)
        sp_layout.addSpacing(15)
        sp_layout.addWidget(stat_text)
        sp_layout.addStretch()

        # 右侧按钮组
        btns_layout = QVBoxLayout()
        btns_layout.setSpacing(15)

        btn_help = self.create_bottom_btn("使用说明", "resources/icons/help_icon.png", "#2d3347", "#eab308")
        btn_help.clicked.connect(self.go_to_help.emit)

        btn_exit = self.create_bottom_btn("退出程序", "resources/icons/exit_icon.png", "#2d3347", "#00f2ea")
        btn_exit.clicked.connect(self.exit_app.emit)

        btns_layout.addWidget(btn_help)
        btns_layout.addWidget(btn_exit)

        bottom_layout.addWidget(status_panel, 3)
        bottom_layout.addLayout(btns_layout, 2)

        # --- 整体组装 ---
        main_layout.addLayout(top_bar)
        main_layout.addLayout(cards_layout, 1) # 1 表示占据剩余所有垂直空间
        main_layout.addLayout(bottom_layout)

    def create_gamer_card(self, title, desc, icon_path, is_primary=False):
        """创建游戏风格的大卡片"""
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 关键修改：设置垂直方向为 Expanding，并设置最小高度
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(350) # 确保有足够的高度显示海报效果
        
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(0, 40, 0, 40)
        layout.setSpacing(20)
        
        # 1. 图标区域
        icon_container = QLabel()
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = self.recolor_icon(icon_path, "#00f2ea" if is_primary else "#ffffff")
        # 放大图标
        icon_container.setPixmap(pix.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # 2. 文字区域
        text_container = QWidget()
        text_container.setStyleSheet("background-color: transparent;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(20, 0, 20, 0)
        text_layout.setSpacing(10)
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 14px; color: #a0a5b5;")
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)

        layout.addStretch(1)
        layout.addWidget(icon_container)
        layout.addWidget(text_container)
        layout.addStretch(1)

        # 样式表
        border_color = "#00f2ea" if is_primary else "#3e4559"
        bg_color = "#1f2435"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid transparent;
                border-radius: 20px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #262b3d;
                border: 2px solid {border_color};
                margin-top: -5px; /* 悬浮上浮效果 */
            }}
            QPushButton:pressed {{
                background-color: #1a1e2e;
                margin-top: 0px;
            }}
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        btn.setGraphicsEffect(shadow)
        
        return btn

    def create_bottom_btn(self, text, icon_path, bg_color, icon_color):
        """创建底部矩形功能按钮"""
        btn = QPushButton()
        btn.setFixedHeight(50) # 固定高度
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(20, 0, 20, 0)
        
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(24, 24)
        lbl_icon.setPixmap(self.recolor_icon(icon_path, icon_color).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        
        layout.addWidget(lbl_icon)
        layout.addSpacing(10)
        layout.addWidget(lbl_text)
        layout.addStretch()
        
        arrow = QLabel("›")
        arrow.setStyleSheet("color: #5c6375; font-size: 20px; font-weight: bold; margin-bottom: 3px;")
        layout.addWidget(arrow)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border-radius: 10px;
                border: 1px solid transparent;
            }}
            QPushButton:hover {{
                background-color: #353b50;
                border: 1px solid {icon_color};
            }}
        """)
        return btn

    def recolor_icon(self, icon_path, color_str):
        pixmap = QPixmap(icon_path)
        if pixmap.isNull(): return QPixmap(1,1)
        
        tmp = QPixmap(pixmap.size())
        tmp.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(tmp)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tmp.rect(), QColor(color_str))
        painter.end()
        return tmp