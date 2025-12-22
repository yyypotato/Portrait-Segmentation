from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QGraphicsOpacityEffect, 
                             QScroller, QScrollerProperties)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QColor

class HelpCard(QFrame):
    """
    带有淡入动画效果的说明卡片
    """
    def __init__(self, title, content, icon_text="💡", parent=None, delay=0):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: #1f2435;
                border-radius: 12px;
                border: 1px solid #2b3042;
            }
            QLabel#Title {
                color: #00f2ea;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
            QLabel#Content {
                color: #a0a5b5;
                font-size: 14px;
                line-height: 1.6;
                background: transparent;
            }
            QLabel#Icon {
                font-size: 24px;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 标题栏
        header_layout = QHBoxLayout()
        icon_lbl = QLabel(icon_text)
        icon_lbl.setObjectName("Icon")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("Title")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        
        # 内容文本
        content_lbl = QLabel(content)
        content_lbl.setObjectName("Content")
        content_lbl.setWordWrap(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(content_lbl)
        
        # 动画初始化 (初始透明)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(600) # 动画时长 600ms
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 关键优化：动画结束后移除特效，避免滚动卡顿
        self.anim.finished.connect(self.on_anim_finished)
        
        self.delay = delay # 启动延迟

    def start_animation(self):
        """延迟启动淡入动画"""
        # 如果特效已被移除（之前播放过），则重新添加
        if self.graphicsEffect() is None:
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            
            # 重新创建动画对象
            self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim.setDuration(600)
            self.anim.setStartValue(0)
            self.anim.setEndValue(1)
            self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.anim.finished.connect(self.on_anim_finished)

        self.opacity_effect.setOpacity(0)
        QTimer.singleShot(self.delay, self.anim.start)

    def on_anim_finished(self):
        """动画结束清理"""
        # 移除 GraphicsEffect 可以显著提升滚动性能，防止残影
        self.setGraphicsEffect(None)

class HelpPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #141824;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 顶部导航栏
        self.setup_top_bar(main_layout)

        # 2. 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #141824;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #2b3042;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        # 3. 配置平滑滚动 (支持鼠标拖拽和惯性)
        scroller = QScroller.scroller(scroll.viewport())
        props = scroller.scrollerProperties()
        # 设置拖拽触发距离和减速因子（惯性）
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.001)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.5) 
        scroller.setScrollerProperties(props)
        
        # 启用触摸和鼠标左键拖拽滚动
        # 修复：PyQt6 中枚举名称为 ScrollerGestureType
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(40, 20, 40, 40)
        self.content_layout.setSpacing(20)

        # 添加说明卡片
        self.add_help_cards()

        self.content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def setup_top_bar(self, parent_layout):
        nav_bar = QWidget()
        nav_bar.setFixedHeight(60)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(30, 0, 30, 0)

        btn_back = QPushButton(" 返回菜单")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a5b5;
                font-size: 14px;
                font-weight: bold;
                border: none;
                text-align: left;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        btn_back.clicked.connect(self.go_back.emit)
        
        arrow = QLabel("‹")
        arrow.setStyleSheet("color: #00f2ea; font-size: 24px; font-weight: bold; margin-right: 5px;")

        back_container = QHBoxLayout()
        back_container.setSpacing(0)
        back_container.addWidget(arrow)
        back_container.addWidget(btn_back)
        
        nav_layout.addLayout(back_container)
        nav_layout.addStretch()
        
        title = QLabel("使用指南")
        title.setStyleSheet("font-size: 16px; color: #5c6375; font-weight: bold;")
        nav_layout.addWidget(title)

        parent_layout.addWidget(nav_bar)

    def add_help_cards(self):
        cards_data = [
            ("快速开始", 
             "1. 在主菜单点击 '开始分割' 进入工作台。\n"
             "2. 点击 '上传图片' 选择您的人像照片。\n"
             "3. 选择合适的 AI 模型（推荐 MobileNetV3 用于快速预览）。\n"
             "4. 点击 '开始分割' 获取透明背景结果。", 
             "🚀"),
            
            ("图像编辑", 
             "进入 '图片编辑' 页面，您可以：\n"
             "• 裁剪与旋转：调整图片构图。\n"
             "• 滤镜调色：使用 20+ 种预设滤镜美化照片。\n"
             "• 创意涂鸦：自由绘制线条或几何图形。\n"
             "• 隐私保护：使用马赛克工具遮挡敏感信息。\n"
             "• 贴纸与相框：添加趣味贴纸和精美边框。", 
             "🎨"),
             
            ("模型说明", 
             "• DeepLabV3+ (ResNet101): 精度最高，边缘细节好，但速度较慢，显存占用高。\n"
             "• DeepLabV3+ (MobileNetV3): 速度极快，适合笔记本或低配置电脑，边缘可能略粗糙。", 
             "🧠"),
             
            ("常见问题", 
             "Q: 提示显存不足怎么办？\n"
             "A: 请在分割页面将推理精度设置为 '限制 512px' 或更低。\n\n"
             "Q: 为什么背景合成没有效果？\n"
             "A: 需要先完成分割（生成 Mask），然后上传背景图，系统会自动进行光影融合。", 
             "❓")
        ]

        self.cards = []
        for i, (title, content, icon) in enumerate(cards_data):
            card = HelpCard(title, content, icon, delay=i*150) 
            self.content_layout.addWidget(card)
            self.cards.append(card)

    def showEvent(self, event):
        """页面显示时触发动画"""
        super().showEvent(event)
        for card in self.cards:
            card.start_animation()