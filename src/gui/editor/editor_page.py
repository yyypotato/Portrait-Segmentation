from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from .canvas import EditorCanvas
from .processor import ImageEditorEngine
from .ui_components import ToolButton, SliderControl
import cv2
import numpy as np
import os

class EditorPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.engine = ImageEditorEngine()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #1e272e;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 顶部栏 ---
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #2d3436; border-bottom: 1px solid #636e72;")
        top_layout = QHBoxLayout(top_bar)
        
        btn_back = QPushButton("← 退出")
        btn_back.setStyleSheet("color: white; border: none; font-weight: bold;")
        btn_back.clicked.connect(self.go_back.emit)
        
        btn_open = QPushButton("📂 打开")
        btn_open.setStyleSheet("color: white; border: 1px solid #636e72; padding: 5px 10px; border-radius: 15px;")
        btn_open.clicked.connect(self.open_image)

        btn_save = QPushButton("💾 保存")
        btn_save.setStyleSheet("background-color: #0984e3; color: white; border: none; padding: 5px 15px; border-radius: 15px; font-weight: bold;")
        btn_save.clicked.connect(self.save_image)

        top_layout.addWidget(btn_back)
        top_layout.addStretch()
        top_layout.addWidget(btn_open)
        top_layout.addWidget(btn_save)

        # --- 2. 中间画布区 ---
        self.canvas = EditorCanvas()
        
        # --- 3. 底部面板 (包含功能区和导航栏) ---
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(300) # 增加高度以容纳滑块列表
        bottom_panel.setStyleSheet("background-color: #2d3436; border-top: 1px solid #636e72;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        # 3.1 功能堆叠区 (根据底部菜单切换显示内容)
        self.stack_tools = QStackedWidget()
        
        # -> Page 0: Crop (占位)
        self.stack_tools.addWidget(self.create_placeholder_page("裁剪功能开发中..."))
        
        # -> Page 1: Adjust (调节 - 核心功能)
        self.stack_tools.addWidget(self.create_adjust_page())
        
        # -> Page 2-7: 其他功能 (占位)
        self.stack_tools.addWidget(self.create_placeholder_page("滤镜功能开发中..."))
        self.stack_tools.addWidget(self.create_placeholder_page("涂鸦功能开发中..."))
        self.stack_tools.addWidget(self.create_placeholder_page("马赛克功能开发中..."))
        self.stack_tools.addWidget(self.create_placeholder_page("标签功能开发中..."))
        self.stack_tools.addWidget(self.create_placeholder_page("贴纸功能开发中..."))
        self.stack_tools.addWidget(self.create_placeholder_page("相框功能开发中..."))

        # 3.2 底部类别导航栏
        category_bar = QScrollArea() # 支持横向滚动，防止按钮过多显示不下
        category_bar.setFixedHeight(80)
        category_bar.setWidgetResizable(True)
        category_bar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        category_bar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        category_bar.setStyleSheet("background: transparent; border: none;")
        
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(10, 5, 10, 5)
        cat_layout.setSpacing(15)

        # 定义类别列表
        categories = [
            ("Crop", "✂️", 0),
            ("Adjust", "🎚️", 1),
            ("Filter", "🎨", 2),
            ("Doodle", "✏️", 3),
            ("Mosaic", "▒", 4),
            ("Label", "🏷️", 5),
            ("Stickers", "😊", 6),
            ("Frame", "🖼️", 7)
        ]

        self.cat_btns = []
        for name, icon, idx in categories:
            btn = ToolButton(name, icon)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self.switch_category(i, b))
            cat_layout.addWidget(btn)
            self.cat_btns.append(btn)

        cat_layout.addStretch()
        category_bar.setWidget(cat_widget)

        bottom_layout.addWidget(self.stack_tools)
        bottom_layout.addWidget(category_bar)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(bottom_panel)

        # 默认选中 Adjust
        self.switch_category(1, self.cat_btns[1])

    def create_adjust_page(self):
        """创建调节页面的滑块列表"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        # 使用滚动区域，因为滑块比较多
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 8px; background: #2d3436; }
            QScrollBar::handle:vertical { background: #636e72; border-radius: 4px; }
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 10, 20, 10)
        content_layout.setSpacing(10)

        # 定义调节项
        adjustments = [
            ("亮度 Brightness", "brightness", -100, 100),
            ("对比度 Contrast", "contrast", -100, 100),
            ("饱和度 Saturation", "saturation", -100, 100),
            ("锐化 Sharpness", "sharpness", 0, 100),
            ("高光 Highlights", "highlights", -100, 100),
            ("阴影 Shadows", "shadows", -100, 100),
            ("色相 Hue", "hue", -180, 180)
        ]

        self.sliders = {}
        for label, key, min_v, max_v in adjustments:
            slider = SliderControl(label, min_v, max_v)
            slider.value_changed.connect(lambda v, k=key: self.update_img(k, v))
            content_layout.addWidget(slider)
            self.sliders[key] = slider

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def create_placeholder_page(self, text):
        page = QWidget()
        layout = QVBoxLayout(page)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #636e72; font-size: 14px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        return page

    def switch_category(self, index, btn_sender):
        self.stack_tools.setCurrentIndex(index)
        for btn in self.cat_btns:
            btn.setChecked(False)
        btn_sender.setChecked(True)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.jpg *.png)")
        if path:
            img = self.engine.load_image(path)
            self.canvas.set_image(img)
            self.canvas.fit_in_view()
            # 重置所有滑块
            for s in self.sliders.values():
                s.set_value(0)

    def update_img(self, key, value):
        self.engine.update_param(key, value)
        res = self.engine.render_final()
        self.canvas.set_image(res)

    def save_image(self):
        if self.engine.original_image is None: return
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", "edited_result.jpg", "Images (*.jpg *.png)")
        if not path: return
        
        final_image = self.engine.render(use_preview=False)
        if final_image is None: return

        try:
            save_img = cv2.cvtColdor(final_image, cv2.COLOR_RGB2BGR)
            ext = os.path.splitext(path)[1]
            is_success, im_buf = cv2.imencode(ext, save_img)
            if is_success:
                im_buf.tofile(path)
                print(f"图片已保存至: {path}")
        except Exception as e:
            print(f"保存失败: {e}")