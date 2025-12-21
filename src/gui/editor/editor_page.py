from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QScrollArea, QFrame, 
                             QScroller, QScrollerProperties) # 1. 补充导入 QScrollerProperties
from PyQt6.QtCore import Qt, pyqtSignal
from .canvas import EditorCanvas
from .processor import ImageEditorEngine
from .ui_components import IconButton, ModernSlider 
import cv2
import numpy as np
import os

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
                border: none;
                background: #2d3436;
                height: 6px;
                margin: 0px 0px 0px 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal {
                background: #636e72;
                min-width: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
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
        self.canvas = EditorCanvas()
        
        # --- 3. 底部面板 ---
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(220)
        bottom_panel.setStyleSheet("background-color: #1e272e; border-top: 1px solid #2d3436;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 10)
        bottom_layout.setSpacing(5)

        # Layer 1: 滑块
        self.slider_panel = ModernSlider()
        self.slider_panel.value_changed.connect(self.on_slider_change)
        self.slider_panel.hide()

        # Layer 2: 子工具层
        self.sub_tool_stack = QStackedWidget()
        self.sub_tool_stack.setFixedHeight(80)
        
        self.sub_tool_stack.addWidget(QLabel("")) # Page 0: Crop
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
        main_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(bottom_panel)

        # 默认选中 Adjust
        if len(self.cat_btns) > 1:
            self.switch_category(1, self.cat_btns[1])
        if hasattr(self, 'adjust_btns') and len(self.adjust_btns) > 0:
            self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def create_scroll_area(self):
        """创建支持鼠标拖拽的滚动区域"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        # 开启按需显示滚动条
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 2. 开启鼠标左键拖拽手势 (增加异常捕获和属性优化)
        try:
            QScroller.grabGesture(scroll.viewport(), QScroller.ScrollerGesture.LeftMouseButtonGesture)
            
            # 优化滚动参数：降低延迟，提高响应
            scroller = QScroller.scroller(scroll.viewport())
            props = scroller.scrollerProperties()
            props.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.001)
            props.setScrollMetric(QScrollerProperties.ScrollMetric.MousePressEventDelay, 0.05)
            scroller.setScrollerProperties(props)
            
        except Exception as e:
            print(f"QScroller 设置失败 (可能是 PyQt 版本兼容性问题): {e}")
            
        return scroll

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
        if index == 1: self.slider_panel.show()
        else: self.slider_panel.hide()

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