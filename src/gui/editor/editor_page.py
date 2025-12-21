from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QScrollArea, QFrame, 
                             QScroller, QScrollerProperties, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent, QPointF # 1. 补充导入 QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from .canvas import EditorCanvas
from .processor import ImageEditorEngine
from .ui_components import IconButton, ModernSlider 
from .crop_overlay import CropOverlay
import cv2
import numpy as np
import os

# --- 刻度尺滑块 (优化视觉) ---
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
        
        # 绘制底部基线
        painter.setPen(QPen(QColor("#636e72"), 1))
        painter.drawLine(0, h-1, w, h-1)

        # 绘制中心指示器 (黄色三角形)
        painter.setBrush(QColor("#f1c40f"))
        painter.setPen(Qt.PenStyle.NoPen)
        triangle = [QPointF(center_x, h), QPointF(center_x-6, h-10), QPointF(center_x+6, h-10)]
        painter.drawPolygon(triangle)
        
        # 绘制刻度
        val = self.value()
        spacing = 15 # 刻度间距
        
        painter.setPen(QPen(QColor("#b2bec3"), 1))
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        # 绘制范围内的刻度
        # 优化：只绘制可见区域
        visible_range = int(w / 2 / spacing) + 5
        start_i = val - visible_range
        end_i = val + visible_range
        
        for i in range(start_i, end_i + 1):
            if i < -45 or i > 45: continue
            
            offset = (i - val) * spacing
            x = center_x + offset
            
            if i % 5 == 0:
                # 长刻度 + 数字
                painter.setPen(QPen(QColor("#dfe6e9"), 2))
                painter.drawLine(int(x), h-25, int(x), h-12)
                if i % 15 == 0:
                    painter.drawText(int(x)-15, h-45, 30, 20, Qt.AlignmentFlag.AlignCenter, str(i))
            else:
                # 短刻度
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
            QScrollBar:horizontal {
                border: none; background: #2d3436; height: 6px; border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #636e72; min-width: 20px; border-radius: 3px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 顶部栏 ---
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1e272e; border-bottom: 1px solid #2d3436;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)
        
        btn_back = QPushButton(" 返回菜单")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("color: #b2bec3; border: none; font-size: 14px; font-weight: bold;")
        btn_back.clicked.connect(self.go_back.emit)
        
        btn_open = QPushButton("打开图片")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet("""
            QPushButton {
                background-color: #2d3436; color: white; border: 1px solid #636e72;
                border-radius: 15px; padding: 5px 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #636e72; }
        """)
        btn_open.clicked.connect(self.open_image)

        btn_save = QPushButton("保存结果")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0984e3; color: white; border-radius: 15px; 
                padding: 5px 15px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74b9ff; }
        """)
        btn_save.clicked.connect(self.save_image)

        top_layout.addWidget(btn_back)
        top_layout.addStretch()
        top_layout.addWidget(btn_open)
        top_layout.addSpacing(10)
        top_layout.addWidget(btn_save)

        # --- 2. 中间画布区 ---
        canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(canvas_container)
        self.canvas_layout.setContentsMargins(0,0,0,0)
        
        self.canvas = EditorCanvas()
        self.canvas_layout.addWidget(self.canvas)
        
        # 安装事件过滤器，监听 Canvas 大小变化
        self.canvas.installEventFilter(self)
        
        # 初始化 CropOverlay (作为 Canvas 的子控件)
        self.crop_overlay = CropOverlay(self.canvas)
        self.crop_overlay.hide() # 默认隐藏
        self.crop_overlay.crop_changed.connect(self.on_crop_rect_change)

        # --- 3. 底部面板 ---
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(240) # 稍微增高以容纳裁剪工具
        bottom_panel.setStyleSheet("background-color: #1e272e; border-top: 1px solid #2d3436;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 10)
        bottom_layout.setSpacing(5)

        # Layer 1: 滑块 (通用)
        self.slider_panel = ModernSlider()
        self.slider_panel.value_changed.connect(self.on_slider_change)
        self.slider_panel.hide()

        # Layer 2: 子工具层 (Stack)
        self.sub_tool_stack = QStackedWidget()
        self.sub_tool_stack.setFixedHeight(100) # 增加高度给裁剪工具
        
        self.sub_tool_stack.addWidget(self.create_crop_tools())   # Page 0: Crop
        self.sub_tool_stack.addWidget(self.create_adjust_tools()) # Page 1: Adjust
        self.sub_tool_stack.addWidget(self.create_filter_tools()) # Page 2: Filter
        for _ in range(5): self.sub_tool_stack.addWidget(QLabel(""))

        # Layer 3: 主类别
        category_scroll = self.create_scroll_area()
        category_scroll.setFixedHeight(90)
        
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(10, 0, 10, 0)
        cat_layout.setSpacing(15)

        categories = [
            ("crop", "裁剪", 0), ("adjust", "调节", 1), ("filter", "滤镜", 2),
            ("doodle", "涂鸦", 3), ("mosaic", "马赛克", 4), ("label", "标签", 5),
            ("sticker", "贴纸", 6), ("frame", "边框", 7)
        ]

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
        main_layout.addWidget(canvas_container, 1) # 使用 container
        main_layout.addWidget(bottom_panel)

        # 默认选中 Adjust
        if len(self.cat_btns) > 1:
            self.switch_category(1, self.cat_btns[1])
        if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
            self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def eventFilter(self, source, event):
        """监听 Canvas 大小变化，同步 Overlay"""
        if source == self.canvas and event.type() == QEvent.Type.Resize:
            # 只有在裁剪模式下才更新几何信息，节省资源
            if not self.crop_overlay.isHidden():
                self.update_overlay_geometry()
        return super().eventFilter(source, event)

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
        except Exception as e: print(f"QScroller Error: {e}")
        return scroll
    
    def create_crop_tools(self):
        """创建裁剪工具栏 (仿照截图布局)"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        # 1. 上半部分：[左旋] -- [刻度尺] -- [翻转]
        rotate_ctrl_layout = QHBoxLayout()
        
        # 左旋按钮 (90度)
        btn_rotate = IconButton("rotate_left", "", is_small=True)
        btn_rotate.clicked.connect(self.rotate_90_ccw)
        
        # 刻度尺 (中间)
        self.ruler = RulerSlider()
        self.ruler.valueChanged.connect(self.on_rotate_angle_change)
        
        # 翻转按钮 (水平)
        btn_flip = IconButton("flip", "", is_small=True)
        btn_flip.clicked.connect(self.flip_horizontal)
        
        rotate_ctrl_layout.addWidget(btn_rotate)
        rotate_ctrl_layout.addWidget(self.ruler, 1) # 伸缩因子1，占据中间
        rotate_ctrl_layout.addWidget(btn_flip)
        
        # 2. 下半部分：比例选择 (横向滚动)
        ratio_scroll = self.create_scroll_area()
        ratio_scroll.setFixedHeight(50)
        
        ratio_widget = QWidget()
        ratio_layout = QHBoxLayout(ratio_widget)
        ratio_layout.setContentsMargins(0, 0, 0, 0)
        ratio_layout.setSpacing(15)
        
        ratios = [
            ("自由", "ratio_custom", None),
            ("原图", "ratio_full", "full"),
            ("1:1", "ratio_1_1", 1.0),
            ("3:4", "ratio_3_4", 3/4),
            ("4:3", "ratio_4_3", 4/3),
            ("16:9", "ratio_16_9", 16/9)
        ]
        
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
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #b2bec3;
                border: 1px solid #636e72; border-radius: 15px; font-size: 11px;
            }
            QPushButton:checked {
                background-color: #dfe6e9; color: #2d3436; border: 1px solid white;
            }
            QPushButton:hover { border: 1px solid #dfe6e9; }
        """)
        btn.clicked.connect(lambda: self.set_aspect_ratio(val, btn))
        return btn
    
    def create_adjust_tools(self):
        scroll = self.create_scroll_area()
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)
        tools = [
            ("brightness", "亮度", "brightness"), ("contrast", "对比度", "contrast"),
            ("saturation", "饱和度", "saturation"), ("sharpness", "锐化", "sharpness"),
            ("highlights", "高光", "highlights"), ("shadows", "阴影", "shadows"),
            ("hue", "色相", "hue")
        ]
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
        filters = [
            ("original", "原图", "f_original"), ("classic", "经典", "f_classic"),
            ("dawn", "晨光", "f_dawn"), ("pure", "纯净", "f_pure"),
            ("mono", "黑白", "f_mono"), ("metallic", "金属", "f_metallic"),
            ("blue", "蓝调", "f_blue"), ("cool", "清凉", "f_cool"),
            ("netural", "中性", "f_netural"), ("blossom", "桃花", "f_blossom"),
            ("fair", "白皙", "f_fair"), ("pink", "粉嫩", "f_pink"),
            ("caramel", "焦糖", "f_caramel"), ("soft", "柔和", "f_soft"),
            ("impact", "冲击", "f_impact"), ("moody", "情绪", "f_moody"),
            ("valencia", "瓦伦", "f_valencia"), ("memory", "回忆", "f_memory"),
            ("vintage", "复古", "f_vintage"), ("childhood", "童年", "f_childhood"),
            ("halo", "光晕", "f_halo"), ("sweet", "甜美", "f_sweet"),
            ("handsome", "帅气", "f_handsome"), ("sentimental", "感性", "f_sentimental"),
            ("individuality", "个性", "f_individuality"), ("demist", "去雾", "f_demist"),
        ]
        self.filter_btns = []
        for key, name, icon_key in filters:
            btn = IconButton(icon_key, name, is_small=True)
            btn.clicked.connect(lambda c, k=key, b=btn: self.switch_filter(k, b))
            layout.addWidget(btn)
            self.filter_btns.append(btn)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def switch_category(self, index, btn_sender):
        self.sub_tool_stack.setCurrentIndex(index)
        for btn in self.cat_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        # 2. 优化切换逻辑：仅在 index == 0 (裁剪) 时显示 Overlay
        if index == 0: # Crop
            self.crop_overlay.show()
            self.update_overlay_geometry()
            self.slider_panel.hide()
        elif index == 1: # Adjust
            self.crop_overlay.hide()
            self.slider_panel.show()
        else:
            self.crop_overlay.hide()
            self.slider_panel.hide()

    def update_overlay_geometry(self):
        """同步 Overlay 大小到 Canvas 显示的图片区域"""
        # 确保 Overlay 覆盖整个 Canvas 控件
        self.crop_overlay.setGeometry(self.canvas.rect())
        
        # 尝试获取图片实际显示区域
        if hasattr(self.canvas, 'get_image_rect'):
            rect = self.canvas.get_image_rect()
            self.crop_overlay.set_image_rect(rect)
        else:
            # 如果 Canvas 没有实现 get_image_rect，则默认填满
            self.crop_overlay.set_image_rect(self.canvas.rect())

    def on_crop_rect_change(self, norm_rect):
        x, y, w, h = norm_rect.getRect()
        self.engine.update_geo_param("crop_rect", (x, y, w, h))

    def on_rotate_angle_change(self, angle):
        self.engine.update_geo_param("rotate_angle", angle)
        res = self.engine.render(use_preview=True)
        self.canvas.set_image(res)
        # 旋转后图片尺寸改变，必须强制更新 Overlay
        self.update_overlay_geometry()

    def rotate_90_ccw(self):
        current = self.engine.geo_params["rotate_90"]
        self.engine.update_geo_param("rotate_90", current + 1)
        res = self.engine.render(use_preview=True)
        self.canvas.set_image(res)
        self.update_overlay_geometry()

    def flip_horizontal(self):
        current = self.engine.geo_params["flip_h"]
        self.engine.update_geo_param("flip_h", not current)
        res = self.engine.render(use_preview=True)
        self.canvas.set_image(res)

    def set_aspect_ratio(self, ratio, btn_sender):
        for btn in self.ratio_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        if ratio == "full":
            self.crop_overlay.norm_rect = QRectF(0,0,1,1)
            self.crop_overlay.set_aspect_ratio(None)
            self.engine.update_geo_param("crop_rect", None)
        else:
            self.crop_overlay.set_aspect_ratio(ratio)
        
        self.crop_overlay.update()
        
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
        res = self.engine.render(use_preview=True)
        self.canvas.set_image(res)

    def on_slider_change(self, value):
        self.engine.update_param(self.current_adjust_key, value)
        res = self.engine.render(use_preview=True)
        self.canvas.set_image(res)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.jpg *.png *.jpeg *.bmp)")
        if path:
            img = self.engine.load_image(path)
            self.canvas.set_image(img)
            self.canvas.fit_in_view()
            
            # 图片加载后，强制更新 Overlay
            self.update_overlay_geometry()
            
            if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
                self.switch_category(1, self.cat_btns[1])
                self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def save_image(self):
        if self.engine.original_image is None: return
        final_image = self.engine.render(use_preview=False)
        if final_image is None: return
        
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(root_dir, "output")
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        default_path = os.path.join(output_dir, "edited_result.jpg")

        path, _ = QFileDialog.getSaveFileName(self, "保存图片", default_path, "Images (*.jpg *.png)")
        if path:
            try:
                save_img = cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR)
                ext = os.path.splitext(path)[1]
                is_success, im_buf = cv2.imencode(ext, save_img)
                if is_success: im_buf.tofile(path)
            except Exception as e: print(f"保存失败: {e}")