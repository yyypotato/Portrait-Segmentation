from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QScrollArea, QFrame, 
                             QScroller, QMessageBox, QScrollerProperties, QSlider, QColorDialog, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent, QPointF, QSize
# 修复：添加 QImage, QPixmap 导入
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QImage, QPixmap, QIcon
from .canvas import EditorCanvas
from .processor import ImageEditorEngine
from .ui_components import IconButton, ModernSlider 
from .crop_overlay import CropOverlay
from .doodle_overlay import DoodleOverlay
from .mosaic_overlay import MosaicOverlay
from .label_overlay import LabelOverlay 
from .sticker_overlay import StickerOverlay
from ..workbench_page import WorkbenchPage
import cv2
import numpy as np
import os

class RulerSlider(QSlider):
    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        self.setRange(-45, 45)
        self.setValue(0)
        self.setFixedHeight(60)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        center_x = w / 2
        painter.setPen(QPen(QColor("#636e72"), 1))
        painter.drawLine(0, h-1, w, h-1)
        painter.setBrush(QColor("#f1c40f"))
        painter.setPen(Qt.PenStyle.NoPen)
        triangle = [QPointF(center_x, h), QPointF(center_x-6, h-10), QPointF(center_x+6, h-10)]
        painter.drawPolygon(triangle)
        val = self.value()
        spacing = 15
        painter.setPen(QPen(QColor("#b2bec3"), 1))
        painter.setFont(QFont("Arial", 9))
        visible_range = int(w / 2 / spacing) + 5
        for i in range(val - visible_range, val + visible_range + 1):
            if i < -45 or i > 45: continue
            offset = (i - val) * spacing
            x = center_x + offset
            if i % 5 == 0:
                painter.setPen(QPen(QColor("#dfe6e9"), 2))
                painter.drawLine(int(x), h-25, int(x), h-12)
                if i % 15 == 0: painter.drawText(int(x)-15, h-45, 30, 20, Qt.AlignmentFlag.AlignCenter, str(i))
            else:
                painter.setPen(QPen(QColor("#636e72"), 1))
                painter.drawLine(int(x), h-20, int(x), h-12)

class EditorPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.engine = ImageEditorEngine()
        self.current_adjust_key = "brightness" 
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #1e272e; }
            QScrollBar:horizontal { border: none; background: #2d3436; height: 6px; border-radius: 3px; }
            QScrollBar::handle:horizontal { background: #636e72; min-width: 20px; border-radius: 3px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #141824; color: white;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)
        
        self.btn_back = QPushButton(" 返回菜单")
        self.btn_back.setStyleSheet("color: #b2bec3; border: none; font-size: 14px; font-weight: bold;")
        self.btn_back.clicked.connect(self.go_back.emit)
        
        btn_open = QPushButton("打开图片")
        btn_open.setStyleSheet("QPushButton { background-color: #2d3436; color: white; border: 1px solid #636e72; border-radius: 15px; padding: 5px 15px; font-weight: bold; } QPushButton:hover { background-color: #636e72; }")
        btn_open.clicked.connect(self.open_image)

        btn_save = QPushButton("保存结果")
        btn_save.setStyleSheet("QPushButton { background-color: #0984e3; color: white; border-radius: 15px; padding: 5px 15px; font-weight: bold; } QPushButton:hover { background-color: #74b9ff; }")
        btn_save.clicked.connect(self.save_image)

        top_layout.addWidget(self.btn_back)
        top_layout.addStretch()
        top_layout.addWidget(btn_open)
        top_layout.addSpacing(10)
        top_layout.addWidget(btn_save)

        # Canvas
        canvas_container = QWidget()
        canvas_container.setStyleSheet("background-color: #141824; color: white;")
        self.canvas_layout = QVBoxLayout(canvas_container)
        self.canvas_layout.setContentsMargins(0,0,0,0)
        self.canvas = EditorCanvas()
        self.canvas_layout.addWidget(self.canvas)
        self.canvas.installEventFilter(self)
        
        self.crop_overlay = CropOverlay(self.canvas)
        self.crop_overlay.hide()
        self.crop_overlay.crop_changed.connect(self.on_crop_rect_change)
        
        # 初始化 DoodleOverlay
        self.doodle_overlay = DoodleOverlay(self.canvas)
        self.doodle_overlay.hide()

        # 初始化 MosaicOverlay
        self.mosaic_overlay = MosaicOverlay(self.canvas)
        self.mosaic_overlay.hide()

        # 初始化 LabelOverlay (新增)
        self.label_overlay = LabelOverlay(self.canvas)
        self.label_overlay.hide()
        
        # 初始化 StickerOverlay (新增)
        self.sticker_overlay = StickerOverlay(self.canvas)
        self.sticker_overlay.hide()

        # Bottom Panel
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(240)
        bottom_panel.setStyleSheet("background-color: #141824; color: white;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 10)
        bottom_layout.setSpacing(5)

        self.slider_panel = ModernSlider()
        self.slider_panel.value_changed.connect(self.on_slider_change)
        self.slider_panel.hide()

        self.sub_tool_stack = QStackedWidget()
        self.sub_tool_stack.setFixedHeight(120)
        self.sub_tool_stack.addWidget(self.create_crop_tools())   
        self.sub_tool_stack.addWidget(self.create_adjust_tools()) 
        self.sub_tool_stack.addWidget(self.create_filter_tools()) 
        self.sub_tool_stack.addWidget(self.create_doodle_tools()) # 3
        self.sub_tool_stack.addWidget(self.create_mosaic_tools()) # 4
        self.sub_tool_stack.addWidget(self.create_label_tools())  # 5 (新增)
        self.sub_tool_stack.addWidget(self.create_sticker_tools()) # 6 (新增)
        self.sub_tool_stack.addWidget(self.create_frame_tools()) # 7 (新增)


        category_scroll = self.create_scroll_area()
        category_scroll.setFixedHeight(90)
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(10, 0, 10, 0)
        cat_layout.setSpacing(15)

        categories = [("crop", "裁剪", 0), ("adjust", "调节", 1), ("filter", "滤镜", 2),
                      ("doodle", "涂鸦", 3), ("mosaic", "马赛克", 4), ("label", "标签", 5),
                      ("sticker", "贴纸", 6), ("frame", "边框", 7)]

        self.cat_btns = []
        for icon, name, idx in categories:
            btn = IconButton(icon, name, is_small=False)
            btn.clicked.connect(lambda c, i=idx, b=btn: self.switch_category(i, b))
            cat_layout.addWidget(btn)
            self.cat_btns.append(btn)
        
        cat_layout.addStretch()
        category_scroll.setWidget(cat_widget)

        bottom_layout.addWidget(self.slider_panel)
        bottom_layout.addWidget(self.sub_tool_stack)
        bottom_layout.addWidget(category_scroll)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(canvas_container, 1)
        main_layout.addWidget(bottom_panel)

        if len(self.cat_btns) > 1: self.switch_category(1, self.cat_btns[1])
        if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
            self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def eventFilter(self, source, event):
        if source == self.canvas and event.type() == QEvent.Type.Resize:
            if not self.crop_overlay.isHidden():
                self.update_overlay_geometry()
            if not self.doodle_overlay.isHidden():
                self.update_doodle_geometry()
            if not self.mosaic_overlay.isHidden():
                self.update_mosaic_geometry()
            if not self.label_overlay.isHidden(): # 新增
                self.update_label_geometry()
            if not self.sticker_overlay.isHidden(): # 新增
                self.update_sticker_geometry()
        return super().eventFilter(source, event)

    def create_sticker_tools(self):
        """创建贴纸工具栏"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用 TabWidget 分类显示贴纸
        tab_widget = QTabWidget()
        # 设置图标大小
        tab_widget.setIconSize(QSize(28, 28))
        
        # 优化样式：增加 Tab 宽度，确保图标居中，增加内边距
        tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { 
                background: transparent; 
                padding: 8px 12px; 
                min-width: 40px; 
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background: rgba(255, 255, 255, 0.1); 
                border-radius: 4px; 
            }
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
        """)
        
        categories = ["time", "location", "food", "drink", "mood", "text"]
        base_path = os.path.join("resources", "images", "stickers")
        icon_base_path = os.path.join("resources", "icons") 
        
        for cat in categories:
            cat_path = os.path.join(base_path, cat)
            if not os.path.exists(cat_path): continue
            
            scroll = self.create_scroll_area()
            scroll.setFixedHeight(90)
            
            content_widget = QWidget()
            grid = QHBoxLayout(content_widget) 
            grid.setSpacing(10)
            grid.setContentsMargins(10, 5, 10, 5)
            
            # 加载贴纸图片
            images = [f for f in os.listdir(cat_path) if f.endswith(('.png', '.jpg'))]
            for img_file in images:
                img_path = os.path.join(cat_path, img_file)
                btn = QPushButton()
                btn.setFixedSize(70, 70)
                btn.setIcon(QIcon(img_path))
                btn.setIconSize(QSize(60, 60))
                btn.setStyleSheet("QPushButton { border: none; background: rgba(255,255,255,0.05); border-radius: 5px; } QPushButton:hover { background: rgba(255,255,255,0.15); }")
                btn.clicked.connect(lambda c, p=img_path: self.sticker_overlay.add_sticker(p))
                grid.addWidget(btn)
                
            grid.addStretch()
            scroll.setWidget(content_widget)
            
            # --- 修复：加载图标逻辑增强 ---
            # 优先查找小写文件名，如果不存在则查找首字母大写文件名
            icon_path = os.path.join(icon_base_path, f"cat_{cat}.png")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(icon_base_path, f"{cat.capitalize()}.png")
            
            if os.path.exists(icon_path):
                # 使用图标，不显示文字
                themed_icon = self.load_themed_icon(icon_path, "#b2bec3") 
                idx = tab_widget.addTab(scroll, themed_icon, "")
                tab_widget.setTabToolTip(idx, cat.capitalize())
            else:
                # 回退到文字
                tab_widget.addTab(scroll, cat.capitalize())
            # --------------------
            
        layout.addWidget(tab_widget)
        return container
    
    def load_themed_icon(self, path, color="#b2bec3"):
        """加载图片并将其非透明区域着色为指定颜色"""
        if not os.path.exists(path): return QIcon()
        
        pixmap = QPixmap(path)
        if pixmap.isNull(): return QIcon()
        
        # 使用 Painter 对图标进行着色
        painter = QPainter(pixmap)
        # SourceIn 模式：只在原图非透明区域绘制颜色
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()
        
        return QIcon(pixmap)
    def create_scroll_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        try:
            QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGesture.LeftMouseButtonGesture)
            scroller = QScroller.scroller(scroll.viewport())
            props = scroller.scrollerProperties()
            props.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.001)
            props.setScrollMetric(QScrollerProperties.ScrollMetric.MousePressEventDelay, 0.05)
            scroller.setScrollerProperties(props)
        except Exception: pass
        return scroll
    
    def create_crop_tools(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        rotate_ctrl_layout = QHBoxLayout()
        btn_rotate = IconButton("rotate_left", "", is_small=True)
        btn_rotate.clicked.connect(self.rotate_90_ccw)
        self.ruler = RulerSlider()
        self.ruler.valueChanged.connect(self.on_rotate_angle_change)
        btn_flip = IconButton("flip", "", is_small=True)
        btn_flip.clicked.connect(self.flip_horizontal)
        
        rotate_ctrl_layout.addWidget(btn_rotate)
        rotate_ctrl_layout.addWidget(self.ruler, 1)
        rotate_ctrl_layout.addWidget(btn_flip)
        
        ratio_scroll = self.create_scroll_area()
        ratio_scroll.setFixedHeight(50)
        ratio_widget = QWidget()
        ratio_layout = QHBoxLayout(ratio_widget)
        ratio_layout.setContentsMargins(0, 0, 0, 0)
        ratio_layout.setSpacing(15)
        
        ratios = [("自由", "ratio_custom", None), ("原图", "ratio_full", "reset"),
                  ("1:1", "ratio_1_1", 1.0), ("3:4", "ratio_3_4", 3/4),
                  ("4:3", "ratio_4_3", 4/3), ("16:9", "ratio_16_9", 16/9)]
        
        self.ratio_btns = []
        for text, icon, val in ratios:
            btn = self.create_ratio_btn(text, icon, val)
            ratio_layout.addWidget(btn)
            self.ratio_btns.append(btn)
            
        ratio_layout.addStretch()
        ratio_scroll.setWidget(ratio_widget)
        layout.addLayout(rotate_ctrl_layout)
        layout.addWidget(ratio_scroll)
        return container

    def create_ratio_btn(self, text, icon_key, val):
        btn = QPushButton(text)
        btn.setFixedSize(50, 30)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QPushButton { background-color: transparent; color: #b2bec3; border: 1px solid #636e72; border-radius: 15px; font-size: 11px; } QPushButton:checked { background-color: #dfe6e9; color: #2d3436; border: 1px solid white; } QPushButton:hover { border: 1px solid #dfe6e9; }")
        btn.clicked.connect(lambda: self.set_aspect_ratio(val, btn))
        return btn

    def create_label_tools(self):
        """创建标签工具栏 (包含 Text box 和 Style 两个 Tab)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 使用 TabWidget 模拟截图中的 "Text box | Style" 切换
        self.label_tabs = QTabWidget()
        self.label_tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: transparent; color: #b2bec3; padding: 8px 20px; font-size: 14px; }
            QTabBar::tab:selected { color: white; border-bottom: 2px solid white; }
        """)
        
        # Tab 1: Text box (选择气泡样式)
        tab_box = QWidget()
        box_layout = QHBoxLayout(tab_box)
        box_scroll = self.create_scroll_area()
        box_scroll.setFixedHeight(80)
        box_widget = QWidget()
        box_inner_layout = QHBoxLayout(box_widget)
        box_inner_layout.setSpacing(15)
        
        # 读取 resources/images/labels 下的图片
        label_dir = os.path.join("resources", "images", "labels")
        if os.path.exists(label_dir):
            for f in os.listdir(label_dir):
                if f.endswith(".png"):
                    path = os.path.join(label_dir, f)
                    # 创建图片按钮
                    btn = QPushButton()
                    btn.setFixedSize(60, 60)
                    btn.setIcon(QIcon(path)) # 需要导入 QIcon
                    btn.setIconSize(QSize(50, 50)) # 需要导入 QSize
                    btn.setStyleSheet("background: transparent; border: 1px solid #636e72; border-radius: 5px;")
                    btn.clicked.connect(lambda c, p=path: self.label_overlay.add_label(p))
                    box_inner_layout.addWidget(btn)
        
        box_inner_layout.addStretch()
        box_scroll.setWidget(box_widget)
        box_layout.addWidget(box_scroll)
        
        # Tab 2: Style (字体样式)
        tab_style = QWidget()
        style_layout = QHBoxLayout(tab_style)
        style_layout.setSpacing(15)
        
        # 字体大小滑块
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 72)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setFixedWidth(100)
        self.font_size_slider.valueChanged.connect(lambda v: self.label_overlay.set_current_font_size(v))
        
        # 样式按钮
        btn_bold = IconButton("style_bold", "", is_small=True)
        btn_bold.setCheckable(True)
        btn_bold.toggled.connect(lambda c: self.label_overlay.set_current_font_bold(c))
        
        btn_italic = IconButton("style_italic", "", is_small=True)
        btn_italic.setCheckable(True)
        btn_italic.toggled.connect(lambda c: self.label_overlay.set_current_font_italic(c))
        
        btn_shadow = IconButton("style_shadow", "", is_small=True)
        btn_shadow.setCheckable(True)
        btn_shadow.toggled.connect(lambda c: self.label_overlay.set_current_shadow(c))
        
        btn_color = IconButton("style_color", "", is_small=True)
        btn_color.clicked.connect(self.pick_label_color)
        
        style_layout.addWidget(QLabel("Size:"))
        style_layout.addWidget(self.font_size_slider)
        style_layout.addWidget(btn_bold)
        style_layout.addWidget(btn_italic)
        style_layout.addWidget(btn_shadow)
        style_layout.addWidget(btn_color)
        style_layout.addStretch()
        
        self.label_tabs.addTab(tab_box, "Text box")
        self.label_tabs.addTab(tab_style, "Style")
        
        layout.addWidget(self.label_tabs)
        return container

    def pick_label_color(self):
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "选择文字颜色")
        if color.isValid():
            self.label_overlay.set_current_color(color)

    def create_adjust_tools(self):
        scroll = self.create_scroll_area()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)
        tools = [("brightness", "亮度", "brightness"), ("contrast", "对比度", "contrast"),
                 ("saturation", "饱和度", "saturation"), ("sharpness", "锐化", "sharpness"),
                 ("highlights", "高光", "highlights"), ("shadows", "阴影", "shadows"), ("hue", "色相", "hue")]
        self.adjust_btns = []
        for icon, name, key in tools:
            btn = IconButton(icon, name, is_small=True)
            btn.clicked.connect(lambda c, k=key, b=btn: self.switch_adjust_tool(k, b))
            layout.addWidget(btn)
            self.adjust_btns.append(btn)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def create_filter_tools(self):
        scroll = self.create_scroll_area()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)
        filters = [("f_original", "原图", "f_original"), ("f_classic", "经典", "f_classic"),
                   ("f_dawn", "晨光", "f_dawn"), ("f_pure", "纯净", "f_pure"), ("f_mono", "黑白", "f_mono"),
                   ("f_metallic", "金属", "f_metallic"), ("f_blue", "蓝调", "f_blue"), ("f_cool", "清凉", "f_cool"),
                   ("f_netural", "中性", "f_netural"), ("f_blossom", "桃花", "f_blossom"), ("f_fair", "白皙", "f_fair"),
                   ("f_pink", "粉嫩", "f_pink"), ("f_caramel", "焦糖", "f_caramel"), ("f_soft", "柔和", "f_soft"),
                   ("f_impact", "冲击", "f_impact"), ("f_moody", "情绪", "f_moody"), ("f_valencia", "瓦伦", "f_valencia"),
                   ("f_memory", "回忆", "f_memory"), ("f_vintage", "复古", "f_vintage"), ("f_childhood", "童年", "f_childhood"),
                   ("f_halo", "光晕", "f_halo"), ("f_sweet", "甜美", "f_sweet"), ("f_handsome", "帅气", "f_handsome"),
                   ("f_sentimental", "感性", "f_sentimental"), ("f_individuality", "个性", "f_individuality"), ("f_demist", "去雾", "f_demist")]
        self.filter_btns = []
        for key, name, icon_key in filters:
            btn = IconButton(icon_key, name, is_small=True)
            btn.clicked.connect(lambda c, k=key, b=btn: self.switch_filter(k, b))
            layout.addWidget(btn)
            self.filter_btns.append(btn)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_doodle_tools(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        slider_layout = QHBoxLayout()
        self.doodle_slider = QSlider(Qt.Orientation.Horizontal)
        self.doodle_slider.setRange(1, 30)
        self.doodle_slider.setValue(5)
        self.doodle_slider.setFixedWidth(200)
        self.doodle_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #636e72; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        self.doodle_slider.valueChanged.connect(lambda v: self.doodle_overlay.set_width(v))
        slider_layout.addStretch()
        slider_layout.addWidget(self.doodle_slider)
        slider_layout.addStretch()

        tools_scroll = self.create_scroll_area()
        tools_scroll.setFixedHeight(70)
        
        tools_widget = QWidget()
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(20)
        
        doodle_tools = [
            ("eraser", "doodle_eraser"),
            ("curve", "doodle_curve"),
            ("arrow", "doodle_arrow"),
            ("line", "doodle_line"),
            ("rect", "doodle_rect"),
            ("circle", "doodle_circle")
        ]
        
        self.doodle_btns = []
        for key, icon in doodle_tools:
            btn = IconButton(icon, "", is_small=True)
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda c, k=key, b=btn: self.set_doodle_tool(k, b))
            tools_layout.addWidget(btn)
            self.doodle_btns.append(btn)
            
        tools_layout.addStretch()
        tools_scroll.setWidget(tools_widget)

        layout.addLayout(slider_layout)
        layout.addWidget(tools_scroll)
        
        return container

    def create_mosaic_tools(self):
        """创建马赛克工具栏"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        # 1. 粗细滑块
        slider_layout = QHBoxLayout()
        self.mosaic_slider = QSlider(Qt.Orientation.Horizontal)
        self.mosaic_slider.setRange(5, 50)
        self.mosaic_slider.setValue(20)
        self.mosaic_slider.setFixedWidth(200)
        self.mosaic_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #636e72; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ffffff; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
        """)
        self.mosaic_slider.valueChanged.connect(lambda v: self.mosaic_overlay.set_brush_size(v))
        slider_layout.addStretch()
        slider_layout.addWidget(self.mosaic_slider)
        slider_layout.addStretch()

        # 2. 样式选择
        tools_scroll = self.create_scroll_area()
        tools_scroll.setFixedHeight(70)
        
        tools_widget = QWidget()
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(20)
        
        mosaic_types = [
            ("pixel", "mosaic_pixel"),
            ("blur", "mosaic_blur"),
            ("triangle", "mosaic_triangle"),
            ("hexagon", "mosaic_hexagon"),
            ("eraser", "mosaic_eraser")
        ]
        
        self.mosaic_btns = []
        for key, icon in mosaic_types:
            btn = IconButton(icon, "", is_small=True)
            btn.setFixedSize(50, 50)
            btn.clicked.connect(lambda c, k=key, b=btn: self.set_mosaic_tool(k, b))
            tools_layout.addWidget(btn)
            self.mosaic_btns.append(btn)
            
        tools_layout.addStretch()
        tools_scroll.setWidget(tools_widget)

        layout.addLayout(slider_layout)
        layout.addWidget(tools_scroll)
        return container
        
    def switch_category(self, index, btn_sender):
        self.sub_tool_stack.setCurrentIndex(index)
        for btn in self.cat_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        # 隐藏所有 Overlay 和 Slider
        self.crop_overlay.hide()
        self.doodle_overlay.hide()
        self.mosaic_overlay.hide()
        self.label_overlay.hide() 
        self.sticker_overlay.hide()
        self.slider_panel.hide()
        
        if index == 0: # Crop
            img = self.engine.render(use_preview=True, include_crop=False)
            if img is not None:
                self.canvas.set_image(img)
                self.crop_overlay.show()
                self.update_overlay_geometry()
            
        elif index == 3: # Doodle
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
                self.doodle_overlay.clear_canvas()
                self.doodle_overlay.show()
                self.update_doodle_geometry()
                if self.doodle_btns:
                    self.set_doodle_tool("curve", self.doodle_btns[1])
                self.show_action_bar("Doodle", self.save_doodle, self.cancel_doodle)

        elif index == 4: # Mosaic
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
                self.mosaic_overlay.clear_mask()
                self.mosaic_overlay.show()
                self.update_mosaic_geometry()
                if self.mosaic_btns:
                    self.set_mosaic_tool("pixel", self.mosaic_btns[0])
                self.show_action_bar("Mosaic", self.save_mosaic, self.cancel_mosaic)

        elif index == 5: # Label (新增)
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
                self.label_overlay.show()
                self.update_label_geometry()
                self.show_action_bar("Label", self.save_label, self.cancel_label)

        elif index == 6: # Sticker (新增)
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
                self.sticker_overlay.show()
                self.update_sticker_geometry()
                self.show_action_bar("Sticker", self.save_sticker, self.cancel_sticker)

        elif index == 7: # Frame (新增)
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
                # 默认选中第一个（无相框）
                if hasattr(self, 'frame_btns') and self.frame_btns:
                    self.apply_frame_preview("none", self.frame_btns[0])
                else:
                    self.show_action_bar("Frame", self.save_frame, self.cancel_frame)

        else: # Adjust, Filter, etc.
            img = self.engine.render(use_preview=True, include_crop=True)
            if img is not None:
                self.canvas.set_image(img)
            self.hide_action_bar()
            
            if index == 1: self.slider_panel.show()

    def update_sticker_geometry(self):
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.sticker_overlay.set_image_rect(rect)
        else:
            self.sticker_overlay.set_image_rect(self.canvas.rect())

    def save_sticker(self):
        if self.engine.original_image is None:
            self.cancel_sticker()
            return
            
        # 1. 获取贴纸层图片 (QImage ARGB32)
        sticker_img_qt = self.sticker_overlay.get_result_image(self.sticker_overlay.size())
        
        # 2. 转换为 Numpy 格式
        # QImage.bits() 返回的数据在 Windows 上通常是 BGRA 顺序
        ptr = sticker_img_qt.bits()
        ptr.setsize(sticker_img_qt.height() * sticker_img_qt.width() * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((sticker_img_qt.height(), sticker_img_qt.width(), 4))
        
        # 3. 获取当前底图 (RGB)
        current_img = self.engine.render(use_preview=True, include_crop=True)
        if current_img is None: return
        
        # 4. 颜色空间修正与混合
        # arr 是 BGRA，current_img 是 RGB
        # 我们需要将 arr 转换为 RGBA 以匹配 current_img 的通道顺序
        sticker_rgba = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGBA)
        
        # 调整尺寸
        if sticker_rgba.shape[:2] != current_img.shape[:2]:
            sticker_rgba = cv2.resize(sticker_rgba, (current_img.shape[1], current_img.shape[0]))
            
        # 分离通道
        r, g, b, a = cv2.split(sticker_rgba)
        overlay_rgb = cv2.merge((r, g, b))
        
        # 归一化 Alpha
        mask = a / 255.0
        
        # 混合
        src = current_img.astype(float)
        ovr = overlay_rgb.astype(float)
        
        # 逐通道混合
        for c in range(3):
            src[:, :, c] = src[:, :, c] * (1.0 - mask) + ovr[:, :, c] * mask
            
        merged_img = src.astype(np.uint8)
        
        # 5. 更新 Engine
        self.engine.preview_image = merged_img
        self.engine.original_image = cv2.resize(merged_img, 
                                                (self.engine.original_image.shape[1], self.engine.original_image.shape[0]))
        
        self.canvas.set_image(merged_img)
        self.sticker_overlay.clear()
        self.sticker_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def cancel_sticker(self):
        self.sticker_overlay.clear()
        self.sticker_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def create_frame_tools(self):
        """创建相框工具栏"""
        scroll = self.create_scroll_area()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)
        
        # 定义相框类型：(图标key, 显示名称, 内部逻辑key)
        frames = [
            ("frame_none", "无", "none"),
            ("frame_white", "白边", "white"),
            ("frame_black", "黑边", "black"),
            ("frame_polaroid", "拍立得", "polaroid"),
            ("frame_wood", "木质", "wood"),
            ("frame_film", "胶卷", "film"), # 新增胶卷风格
            ("frame_line", "线条", "line")  # 新增简约线条风格
        ]
        
        self.frame_btns = []
        for icon, name, key in frames:
            btn = IconButton(icon, name, is_small=True)
            # 修复：确保图标颜色正确
            if icon == "frame_white":
                # 白边图标如果是白色的，在深色背景下可能看不清，这里不做特殊处理，依赖 IconButton 的样式
                pass
            btn.clicked.connect(lambda c, k=key, b=btn: self.apply_frame_preview(k, b))
            layout.addWidget(btn)
            self.frame_btns.append(btn)
            
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def apply_frame_preview(self, frame_type, btn_sender):
        """应用相框预览"""
        for btn in self.frame_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        self.current_frame_type = frame_type
        
        # 获取当前渲染图像
        current_img = self.engine.render(use_preview=True, include_crop=True)
        if current_img is None: return
        
        # 生成带相框的图像
        framed_img = self.generate_framed_image(current_img, frame_type)
        
        # 显示预览
        self.canvas.set_image(framed_img)
        self.show_action_bar("Frame", self.save_frame, self.cancel_frame)

    def generate_framed_image(self, img, frame_type):
        """
        生成带相框的图像逻辑
        :param img: 原始图像 (RGB numpy array)
        :param frame_type: 相框类型字符串
        :return: 处理后的图像
        """
        if frame_type == "none":
            return img.copy()
            
        h, w = img.shape[:2]
        min_dim = min(w, h)
        
        if frame_type == "white":
            # 添加 5% 白色边框
            border = int(min_dim * 0.05)
            return cv2.copyMakeBorder(img, border, border, border, border, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            
        elif frame_type == "black":
            # 添加 5% 黑色边框
            border = int(min_dim * 0.05)
            return cv2.copyMakeBorder(img, border, border, border, border, cv2.BORDER_CONSTANT, value=[0, 0, 0])
            
        elif frame_type == "polaroid":
            # 拍立得风格：四周白边，底部留宽白边用于写字
            border_side = int(min_dim * 0.05)
            border_bottom = int(min_dim * 0.25)
            return cv2.copyMakeBorder(img, border_side, border_bottom, border_side, border_side, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            
        elif frame_type == "wood":
            # 木质边框：使用深棕色填充
            border = int(min_dim * 0.08)
            # RGB 颜色 [139, 69, 19] (SaddleBrown)
            return cv2.copyMakeBorder(img, border, border, border, border, cv2.BORDER_CONSTANT, value=[139, 69, 19])
            
        elif frame_type == "film":
            # 胶卷风格：上下黑色电影边框，模拟胶片孔
            border_y = int(h * 0.12) # 上下边框较宽
            border_x = int(w * 0.02) # 左右微边
            
            # 1. 扩展黑色边框
            res = cv2.copyMakeBorder(img, border_y, border_y, border_x, border_x, cv2.BORDER_CONSTANT, value=[20, 20, 20])
            
            # 2. 绘制胶卷孔 (白色小矩形)
            hole_h = int(border_y * 0.5)
            hole_w = int(hole_h * 0.7)
            hole_margin_top = int((border_y - hole_h) / 2)
            hole_gap = int(hole_w * 0.8) # 孔间距
            
            # 绘制上方孔洞
            for x in range(0, res.shape[1], hole_w + hole_gap):
                cv2.rectangle(res, (x, hole_margin_top), (x + hole_w, hole_margin_top + hole_h), (220, 220, 220), -1)
                
            # 绘制下方孔洞
            hole_margin_bottom = res.shape[0] - border_y + hole_margin_top
            for x in range(0, res.shape[1], hole_w + hole_gap):
                cv2.rectangle(res, (x, hole_margin_bottom), (x + hole_w, hole_margin_bottom + hole_h), (220, 220, 220), -1)
                
            return res

        elif frame_type == "line":
            # 简约线条：外层宽白边 + 内层细黑线
            border_outer = int(min_dim * 0.1)
            # 1. 加宽白边
            res = cv2.copyMakeBorder(img, border_outer, border_outer, border_outer, border_outer, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            
            # 2. 绘制内框线
            line_thickness = max(1, int(min_dim * 0.003))
            margin = int(border_outer * 0.4)
            
            # 计算内框坐标
            pt1 = (margin, margin)
            pt2 = (res.shape[1] - margin, res.shape[0] - margin)
            cv2.rectangle(res, pt1, pt2, (80, 80, 80), line_thickness)
            
            return res
        
        return img
    def save_frame(self):
        if self.engine.original_image is None: return
        
        # 1. 备份当前的非几何参数 (滤镜、调节数值)
        # 这样我们可以在应用相框后恢复它们，而不是重置为0
        saved_filter = self.engine.current_filter
        saved_params = self.engine.params.copy()
        
        # 2. 临时重置滤镜和调节参数
        # 目的是获取一张“干净”的、只应用了裁剪/旋转的底图
        self.engine.update_filter("f_original")
        for k in self.engine.params:
            self.engine.params[k] = 0
            
        # 3. 获取基础图像 (包含裁剪/旋转，但不含滤镜/调节)
        # 这样生成的图片是纯净的，不会带有之前的滤镜效果
        base_img = self.engine.render(use_preview=True, include_crop=True)
        
        # 4. 应用相框
        if hasattr(self, 'current_frame_type'):
            final_img = self.generate_framed_image(base_img, self.current_frame_type)
            
            # 5. 更新 Engine 底图
            # 将“几何变换+相框”后的图作为新的底图
            self.engine.original_image = final_img
            self.engine.preview_image = final_img.copy()
            
            # 6. 重置几何参数 (因为裁剪/旋转已经烘焙到新底图里了)
            self.engine.geo_params["crop_rect"] = None
            self.engine.geo_params["rotate_angle"] = 0
            self.engine.geo_params["rotate_90"] = 0
            self.engine.geo_params["flip_h"] = False
            
            # 7. 恢复滤镜和调节参数 (关键步骤)
            # 恢复之前的设置，这样用户看到的界面数值不变，且效果是应用在带相框的图上
            self.engine.current_filter = saved_filter
            self.engine.params = saved_params
            
            # 8. 刷新显示
            # 重新渲染，将滤镜/调节应用到新的带相框底图上
            new_render = self.engine.render(use_preview=True, include_crop=True)
            self.canvas.set_image(new_render)
            
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def cancel_frame(self):
        # 恢复原图显示
        img = self.engine.render(use_preview=True, include_crop=True)
        if img is not None:
            self.canvas.set_image(img)
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def update_label_geometry(self):
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.label_overlay.set_image_rect(rect)
        else:
            self.label_overlay.set_image_rect(self.canvas.rect())

    def save_label(self):
        if self.engine.original_image is None:
            self.cancel_label()
            return
            
        # 1. 获取标签层图片
        label_img = self.label_overlay.get_result_image(self.label_overlay.size())
        
        # 2. 获取当前底图
        current_img = self.engine.render(use_preview=True, include_crop=True)
        if current_img is None: return
        
        # 3. 合并
        merged_img = self.engine.apply_label_layer(label_img, current_img)
        
        # 4. 更新 Engine
        self.engine.preview_image = merged_img
        self.engine.original_image = cv2.resize(merged_img, 
                                                (self.engine.original_image.shape[1], self.engine.original_image.shape[0]))
        
        self.canvas.set_image(merged_img)
        self.label_overlay.items.clear() # 清空标签
        self.label_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def cancel_label(self):
        self.label_overlay.items.clear()
        self.label_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def update_doodle_geometry(self):
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.doodle_overlay.set_image_rect(rect)
        else:
            self.doodle_overlay.set_image_rect(self.canvas.rect())

    def update_mosaic_geometry(self):
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.mosaic_overlay.set_image_rect(rect)
        else:
            self.mosaic_overlay.set_image_rect(self.canvas.rect())

    def set_doodle_tool(self, tool, btn_sender):
        for btn in self.doodle_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        self.doodle_overlay.set_tool(tool)

    def set_mosaic_tool(self, tool_type, btn_sender):
        for btn in self.mosaic_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        if tool_type == "eraser":
            self.mosaic_overlay.set_mode("eraser")
        else:
            self.mosaic_overlay.set_mode("draw")
            current_img = self.engine.render(use_preview=True, include_crop=True)
            if current_img is not None:
                mosaic_img = self.engine.generate_mosaic_image(current_img, style=tool_type)
                h, w, ch = mosaic_img.shape
                bytes_per_line = ch * w
                qimg = QImage(mosaic_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.mosaic_overlay.set_mosaic_pixmap(QPixmap.fromImage(qimg))
                self.current_mosaic_img_numpy = mosaic_img

    # --- 底部操作栏逻辑 ---
    def show_action_bar(self, title, on_save, on_cancel):
        if not hasattr(self, 'action_bar'):
            self.action_bar = QWidget(self)
            self.action_bar.setFixedHeight(60)
            self.action_bar.setStyleSheet("background-color: #1e272e;")
            layout = QHBoxLayout(self.action_bar)
            layout.setContentsMargins(20, 0, 20, 0)
            
            self.btn_cancel = IconButton("action_close", "", is_small=True)
            self.btn_cancel.setFixedSize(40, 40)
            
            self.lbl_action_title = QLabel(title)
            self.lbl_action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_action_title.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            
            self.btn_save = IconButton("action_check", "", is_small=True)
            self.btn_save.setFixedSize(40, 40)
            
            layout.addWidget(self.btn_cancel)
            layout.addWidget(self.lbl_action_title, 1)
            layout.addWidget(self.btn_save)
            
            bottom_layout = self.layout().itemAt(2).widget().layout()
            bottom_layout.addWidget(self.action_bar)
            
        try: self.btn_cancel.clicked.disconnect()
        except TypeError: pass
        
        try: self.btn_save.clicked.disconnect()
        except TypeError: pass
        
        self.btn_cancel.clicked.connect(on_cancel)
        self.btn_save.clicked.connect(on_save)
        self.lbl_action_title.setText(title)
        
        self.findChild(QScrollArea).hide() 
        self.action_bar.show()

    def hide_action_bar(self):
        if hasattr(self, 'action_bar'):
            self.action_bar.hide()
            bottom_layout = self.layout().itemAt(2).widget().layout()
            for i in range(bottom_layout.count()):
                w = bottom_layout.itemAt(i).widget()
                if isinstance(w, QScrollArea): w.show()

    def save_doodle(self):
        if self.engine.original_image is None:
            self.cancel_doodle()
            return

        doodle_pix = self.doodle_overlay.get_result()
        current_img = self.engine.render(use_preview=True, include_crop=True)
        if current_img is None: return
        
        merged_img = self.engine.apply_doodle_layer(doodle_pix, current_img)
        
        self.engine.preview_image = merged_img
        self.engine.original_image = cv2.resize(merged_img, 
                                                (self.engine.original_image.shape[1], self.engine.original_image.shape[0]))
        
        self.canvas.set_image(merged_img)
        self.doodle_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def cancel_doodle(self):
        self.doodle_overlay.clear_canvas()
        self.doodle_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def save_mosaic(self):
        if self.engine.original_image is None:
            self.cancel_mosaic()
            return

        mask_qimg = self.mosaic_overlay.get_mask()
        current_img = self.engine.render(use_preview=True, include_crop=True)
        if current_img is None: return
        
        if not hasattr(self, 'current_mosaic_img_numpy'):
             self.current_mosaic_img_numpy = self.engine.generate_mosaic_image(current_img, "pixel")

        merged_img = self.engine.apply_mosaic_mask(current_img, self.current_mosaic_img_numpy, mask_qimg)
        
        self.engine.preview_image = merged_img
        self.engine.original_image = cv2.resize(merged_img, 
                                                (self.engine.original_image.shape[1], self.engine.original_image.shape[0]))
        
        self.canvas.set_image(merged_img)
        self.mosaic_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])

    def cancel_mosaic(self):
        self.mosaic_overlay.clear_mask()
        self.mosaic_overlay.hide()
        self.hide_action_bar()
        self.switch_category(1, self.cat_btns[1])
        
    def update_overlay_geometry(self):
        self.crop_overlay.setGeometry(self.canvas.rect())
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.crop_overlay.set_image_rect(rect)
        else:
            self.crop_overlay.set_image_rect(self.canvas.rect())

    def on_crop_rect_change(self, norm_rect):
        x, y, w, h = norm_rect.getRect()
        self.engine.update_geo_param("crop_rect", (x, y, w, h))

    def on_rotate_angle_change(self, angle):
        self.engine.update_geo_param("rotate_angle", angle)
        res = self.engine.render(use_preview=True, include_crop=False)
        if res is not None:
            self.canvas.set_image(res)
            self.update_overlay_geometry()

    def rotate_90_ccw(self):
        current = self.engine.geo_params["rotate_90"]
        self.engine.update_geo_param("rotate_90", current + 1)
        res = self.engine.render(use_preview=True, include_crop=False)
        if res is not None:
            self.canvas.set_image(res)
            self.update_overlay_geometry()

    def flip_horizontal(self):
        current = self.engine.geo_params["flip_h"]
        self.engine.update_geo_param("flip_h", not current)
        res = self.engine.render(use_preview=True, include_crop=False)
        if res is not None:
            self.canvas.set_image(res)

    def set_aspect_ratio(self, ratio, btn_sender):
        for btn in self.ratio_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        if ratio == "reset":
            self.crop_overlay.reset_crop()
            self.engine.update_geo_param("crop_rect", None)
        else:
            self.crop_overlay.set_aspect_ratio(ratio)
        
    def switch_adjust_tool(self, key, btn_sender):
        self.current_adjust_key = key
        for btn in self.adjust_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        val = self.engine.params.get(key, 0)
        self.slider_panel.set_value(val)
        if key in ["sharpness"]: self.slider_panel.slider.setRange(0, 100)
        elif key in ["hue"]: self.slider_panel.slider.setRange(-180, 180)
        else: self.slider_panel.slider.setRange(-100, 100)

    def switch_filter(self, key, btn_sender):
        for btn in self.filter_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        self.engine.update_filter(key)
        res = self.engine.render(use_preview=True, include_crop=True)
        if res is not None:
            self.canvas.set_image(res)

    def on_slider_change(self, value):
        self.engine.update_param(self.current_adjust_key, value)
        res = self.engine.render(use_preview=True, include_crop=True)
        if res is not None:
            self.canvas.set_image(res)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.jpg *.png *.jpeg *.bmp)")
        if path:
            img = self.engine.load_image(path)
            if img is not None:
                self.canvas.set_image(img)
                self.canvas.fit_in_view()
                self.update_overlay_geometry()
                if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
                    self.switch_category(1, self.cat_btns[1])
                    self.switch_adjust_tool("brightness", self.adjust_btns[0])

    # [新增] 供主窗口调用的加载方法
    def load_image_from_path(self, file_path):
        """从文件路径加载图片到编辑器"""
        # 错误修复：这里原本写的是 self.processor，改为 self.engine
        img = self.engine.load_image(file_path)
        
        if img is not None:
            self.canvas.set_image(img)
            self.canvas.fit_in_view()
            self.update_overlay_geometry()
            
            # 重置工具栏状态到默认
            if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
                self.switch_category(1, self.cat_btns[1])
                self.switch_adjust_tool("brightness", self.adjust_btns[0])
            print(f"已加载: {file_path}")
        else:
            QMessageBox.warning(self, "错误", "无法读取图片文件")



    def save_image(self):
        if self.engine.original_image is None: return
        final_image = self.engine.render(use_preview=False, include_crop=True)
        if final_image is None: return
        
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        output_dir = os.path.join(root_dir, "output")

        if not os.path.exists(output_dir): os.makedirs(output_dir)
        default_path = os.path.join(output_dir, "edited_result.jpg")

        path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_path, "Images (*.jpg *.png)")
        if path:
            try:
                WorkbenchPage.add_recent_record(path)
                save_img = cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR)
                ext = os.path.splitext(path)[1]
                is_success, im_buf = cv2.imencode(ext, save_img)
                if is_success: im_buf.tofile(path)
            except Exception as e: print(f"保存失败: {e}")