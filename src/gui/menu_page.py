from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QGraphicsDropShadowEffect, QLineEdit, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QDir, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PyQt6.QtGui import QIcon, QColor, QPixmap, QPainter, QPainterPath, QRegion
import random

class GallerySlice(QWidget):
    """
    单个图片切片控件
    功能：显示图片的一部分，鼠标悬停时变宽
    """
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap(image_path)
        # 默认策略：可伸缩
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(50) # 最小宽度
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 鼠标悬停动画
        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def paintEvent(self, event):
        if self.pixmap.isNull(): return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. 计算 Cover 模式的绘制区域 (保持比例填满)
        rect = self.rect()
        img_size = self.pixmap.size()
        
        # 计算缩放比例 (取宽比和高比中较大的，保证填满)
        if img_size.width() > 0 and img_size.height() > 0:
            scale = max(rect.width() / img_size.width(), rect.height() / img_size.height())
        else:
            scale = 1
        
        new_w = int(img_size.width() * scale)
        new_h = int(img_size.height() * scale)
        
        # 居中裁剪
        x = (rect.width() - new_w) // 2
        y = (rect.height() - new_h) // 2
        
        # 2. 绘制图片
        painter.drawPixmap(x, y, new_w, new_h, self.pixmap)
        
        # 3. 绘制边框 (分割线效果)
        painter.setPen(QColor("#141824")) # 与背景色相同，形成分割线
        painter.drawRect(rect)

        # 4. 悬停高亮遮罩 (可选，让未选中的稍微暗一点)
        if not self.underMouse():
            painter.fillRect(rect, QColor(0, 0, 0, 40)) # 未选中时压暗

    def enterEvent(self, event):
        # 鼠标进入：变宽
        self.anim.stop()
        self.anim.setEndValue(300) # 展开宽度
        self.anim.start()
        self.update() # 触发重绘以移除压暗遮罩

    def leaveEvent(self, event):
        # 鼠标离开：恢复默认
        self.anim.stop()
        self.anim.setEndValue(50) # 恢复收缩宽度
        self.anim.start()
        self.update()

class GalleryPanel(QFrame):
    """
    画廊容器
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(160) 
        self.setObjectName("GalleryPanel")
        # 样式表只负责背景色和边框颜色，圆角裁剪由 resizeEvent 处理
        self.setStyleSheet("""
            QFrame#GalleryPanel {
                background-color: #1f2435; 
                border: 1px solid #2b3042;
                border-radius: 16px; 
            }
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0) # 切片之间无间隙
        
        self.init_images()

    def init_images(self):
        output_dir = QDir("output")
        image_files = []
        if output_dir.exists():
            filters = ["*.png", "*.jpg", "*.jpeg"]
            all_files = [output_dir.filePath(f) for f in output_dir.entryList(filters, QDir.Filter.Files)]
            # 随机抓取 4-5 张
            count = min(len(all_files), 5)
            if count > 0:
                image_files = random.sample(all_files, count)
        
        if not image_files:
            lbl = QLabel("暂无作品，快去创作吧！")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #5c6375; font-size: 14px;")
            self.layout.addWidget(lbl)
            return

        for img_path in image_files:
            slice_widget = GallerySlice(img_path)
            self.layout.addWidget(slice_widget)

    def resizeEvent(self, event):
        """
        使用 setMask 实现真正的子控件圆角裁剪
        """
        path = QPainterPath()
        # 创建一个圆角矩形路径
        path.addRoundedRect(QRectF(self.rect()), 16, 16)
        
        # 将路径转换为 Region 并设置为遮罩
        # 注意：toFillPolygon().toPolygon() 将浮点路径转为整数多边形
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
        super().resizeEvent(event)

class MenuPage(QWidget):
    go_to_seg = pyqtSignal()
    go_to_editor = pyqtSignal()
    go_to_help = pyqtSignal()
    exit_app = pyqtSignal()
    
    go_to_workbench = pyqtSignal()
    go_to_history = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setObjectName("MenuPage")
        self.setStyleSheet("""
            QWidget#MenuPage {
                background-color: #141824; 
            }
            QLabel {
                font-family: 'Microsoft YaHei', 'Segoe UI';
                color: #ffffff;
                background: transparent;
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

        # --- 1. 顶部导航栏 ---
        top_bar = QHBoxLayout()
        
        logo_box = QHBoxLayout()
        logo_box.setSpacing(12)
        logo_icon = QLabel("◎"); logo_icon.setStyleSheet("color: #00f2ea; font-size: 36px; font-weight: bold;")
        title_box = QVBoxLayout(); title_box.setSpacing(2)
        title = QLabel("人像分割工具箱"); title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        subtitle = QLabel("AI PORTRAIT STUDIO"); subtitle.setStyleSheet("font-size: 10px; font-weight: bold; color: #5c6375;")
        title_box.addWidget(title); title_box.addWidget(subtitle)
        logo_box.addWidget(logo_icon); logo_box.addLayout(title_box)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        self.btn_nav_home = self.create_nav_btn("首页", active=True)
        self.btn_nav_work = self.create_nav_btn("工作台")
        self.btn_nav_hist = self.create_nav_btn("云端历史")
        
        self.btn_nav_work.clicked.connect(self.go_to_workbench.emit)
        self.btn_nav_hist.clicked.connect(self.go_to_history.emit)
        
        nav_layout.addWidget(self.btn_nav_home)
        nav_layout.addWidget(self.btn_nav_work)
        nav_layout.addWidget(self.btn_nav_hist)

        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 搜索功能...")
        search_bar.setFixedSize(240, 40)

        top_bar.addLayout(logo_box)
        top_bar.addSpacing(60)
        top_bar.addLayout(nav_layout)
        top_bar.addStretch()
        top_bar.addWidget(search_bar)

        # --- 2. 中间卡片区 ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        self.card_seg = self.create_gamer_card(
            "智能抠图", "AI 自动移除背景\n发丝级精细分割", "resources/icons/seg_icon.png", is_primary=True
        )
        self.card_seg.clicked.connect(self.go_to_seg.emit)

        self.card_edit = self.create_gamer_card(
            "图像精修", "专业调色 / 滤镜\n光效合成工作台", "resources/icons/edit_icon.png", is_primary=False
        )
        self.card_edit.clicked.connect(self.go_to_editor.emit)

        cards_layout.addWidget(self.card_seg)
        cards_layout.addWidget(self.card_edit)

        # --- 3. 底部功能块 (静态画廊) ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(25)

        # 使用新的画廊面板
        self.gallery_panel = GalleryPanel()
        
        # 底部右侧按钮组
        btns_layout = QVBoxLayout()
        btns_layout.setSpacing(15)
        btn_help = self.create_bottom_btn("使用说明", "resources/icons/help_icon.png", "#2d3347", "#eab308")
        btn_help.clicked.connect(self.go_to_help.emit)
        btn_exit = self.create_bottom_btn("退出程序", "resources/icons/exit_icon.png", "#2d3347", "#00f2ea")
        btn_exit.clicked.connect(self.exit_app.emit)
        btns_layout.addWidget(btn_help)
        btns_layout.addWidget(btn_exit)

        bottom_layout.addWidget(self.gallery_panel, 3)
        bottom_layout.addLayout(btns_layout, 1)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(cards_layout, 1)
        main_layout.addLayout(bottom_layout)

    def create_nav_btn(self, text, active=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        color = "#ffffff" if active else "#7d8394"
        border = "border-bottom: 3px solid #00f2ea;" if active else "border: none;"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                font-size: 16px;
                font-weight: bold;
                padding: 8px 15px;
                {border}
            }}
            QPushButton:hover {{
                color: #ffffff;
            }}
        """)
        return btn

    def create_gamer_card(self, title, desc, icon_path, is_primary=False):
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(350)
        
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(0, 50, 0, 50)
        layout.setSpacing(25)
        
        icon_bg = QLabel()
        icon_bg.setFixedSize(120, 120)
        icon_bg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_color = "rgba(0, 242, 234, 0.1)" if is_primary else "rgba(255, 255, 255, 0.05)"
        icon_bg.setStyleSheet(f"background-color: {bg_color}; border-radius: 60px;")
        
        pix = self.recolor_icon(icon_path, "#00f2ea" if is_primary else "#ffffff")
        icon_bg.setPixmap(pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 26px; font-weight: bold; color: white; background: transparent;")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 14px; color: #a0a5b5; background: transparent;")
        
        layout.addWidget(icon_bg, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addStretch()

        border_color = "#00f2ea" if is_primary else "#3e4559"
        gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a3042, stop:1 #1f2435)"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {gradient};
                border: 2px solid #2b3042;
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background-color: #262b3d;
                border: 2px solid {border_color};
                margin-top: -5px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        btn.setGraphicsEffect(shadow)
        
        return btn

    def create_bottom_btn(self, text, icon_path, bg_color, icon_color):
        btn = QPushButton()
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(20, 0, 20, 0)
        
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(24, 24)
        lbl_icon.setPixmap(self.recolor_icon(icon_path, icon_color).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lbl_icon.setStyleSheet("background: transparent;")
        
        lbl_text = QLabel(text)
        lbl_text.setStyleSheet("font-size: 15px; font-weight: bold; color: white; background: transparent;")
        
        layout.addWidget(lbl_icon); layout.addSpacing(10); layout.addWidget(lbl_text); layout.addStretch()
        arrow = QLabel("›"); arrow.setStyleSheet("color: #5c6375; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(arrow)

        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {bg_color}; border-radius: 10px; border: 1px solid transparent; }}
            QPushButton:hover {{ background-color: #353b50; border: 1px solid {icon_color}; }}
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