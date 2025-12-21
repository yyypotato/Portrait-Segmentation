from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QScrollArea, QFrame)
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
        
        # 记录当前选中的调节工具 key (例如 'brightness')
        self.current_adjust_key = "brightness" 
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #1e272e;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 顶部栏 (保持简洁) ---
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #1e272e;") # 纯黑背景
        top_layout = QHBoxLayout(top_bar)
        
        btn_back = QPushButton("取消")
        btn_back.setStyleSheet("color: #b2bec3; border: none; font-size: 14px;")
        btn_back.clicked.connect(self.go_back.emit)
        
        btn_save = QPushButton("保存")
        btn_save.setStyleSheet("background-color: #0984e3; color: white; border-radius: 15px; padding: 5px 15px; font-weight: bold;")
        btn_save.clicked.connect(self.save_image)

        top_layout.addWidget(btn_back)
        top_layout.addStretch()
        top_layout.addWidget(btn_save)

        # --- 2. 中间画布区 ---
        self.canvas = EditorCanvas()
        
        # --- 3. 底部面板 (三层结构) ---
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(220) # 紧凑高度
        bottom_panel.setStyleSheet("background-color: #1e272e; border-top: 1px solid #2d3436;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 10)
        bottom_layout.setSpacing(5)

        # Layer 1: 滑块层 (默认隐藏，只有调节时显示)
        self.slider_panel = ModernSlider()
        self.slider_panel.value_changed.connect(self.on_slider_change)
        self.slider_panel.hide() # 初始隐藏

        # Layer 2: 子工具层 (例如 亮度、对比度...)
        self.sub_tool_stack = QStackedWidget()
        self.sub_tool_stack.setFixedHeight(80)
        
        # -> Page 0: Crop Tools (占位)
        self.sub_tool_stack.addWidget(QLabel("")) 
        
        # -> Page 1: Adjust Tools (核心)
        self.sub_tool_stack.addWidget(self.create_adjust_tools())
        
        # -> Page 2+: Others
        for _ in range(6): self.sub_tool_stack.addWidget(QLabel(""))

        # Layer 3: 主类别导航栏 (Crop, Adjust, Filter...)
        category_scroll = QScrollArea()
        category_scroll.setFixedHeight(90)
        category_scroll.setWidgetResizable(True)
        category_scroll.setStyleSheet("background: transparent; border: none;")
        category_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        category_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(10, 0, 10, 0)
        cat_layout.setSpacing(15)

        # 2. 确保这里的名字与 get_icons.py 中的 key 一致
        categories = [
            ("crop", "裁剪", 0),
            ("adjust", "调节", 1),
            ("filter", "滤镜", 2),
            ("doodle", "涂鸦", 3),
            ("mosaic", "马赛克", 4),
            ("label", "标签", 5),
            ("sticker", "贴纸", 6),
            ("frame", "边框", 7)
        ]

        self.cat_btns = []
        for icon, name, idx in categories:
            # 3. 使用 IconButton
            btn = IconButton(icon, name, is_small=False)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self.switch_category(i, b))
            cat_layout.addWidget(btn)
            self.cat_btns.append(btn)
        
        cat_layout.addStretch()
        category_scroll.setWidget(cat_widget)

        # 组装底部
        bottom_layout.addWidget(self.slider_panel)
        bottom_layout.addWidget(self.sub_tool_stack)
        bottom_layout.addWidget(category_scroll)

        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(bottom_panel)

        # 默认选中 Adjust
        self.switch_category(1, self.cat_btns[1])
        # 默认选中 Brightness
        self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def create_adjust_tools(self):
        """创建调节工具栏 (横向滚动)"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)

        # 4. 确保这里的名字与 get_icons.py 中的 key 一致
        tools = [
            ("brightness", "亮度", "brightness"),
            ("contrast", "对比度", "contrast"),
            ("saturation", "饱和度", "saturation"),
            ("sharpness", "锐化", "sharpness"),
            ("highlights", "高光", "highlights"),
            ("shadows", "阴影", "shadows"),
            ("hue", "色相", "hue")
        ]

        self.adjust_btns = []
        for icon, name, key in tools:
            # 5. 使用 IconButton
            btn = IconButton(icon, name, is_small=True)
            btn.clicked.connect(lambda c, k=key, b=btn: self.switch_adjust_tool(k, b))
            layout.addWidget(btn)
            self.adjust_btns.append(btn)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def switch_category(self, index, btn_sender):
        """切换主类别"""
        self.sub_tool_stack.setCurrentIndex(index)
        
        # UI 状态更新
        for btn in self.cat_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        # 只有在 Adjust 页面才显示滑块
        if index == 1:
            self.slider_panel.show()
        else:
            self.slider_panel.hide()

    def switch_adjust_tool(self, key, btn_sender):
        """切换调节子工具"""
        self.current_adjust_key = key
        
        # UI 状态更新
        for btn in self.adjust_btns: btn.setChecked(False)
        btn_sender.setChecked(True)
        
        # 更新滑块数值
        val = self.engine.params.get(key, 0)
        self.slider_panel.set_value(val)
        
        # 根据工具类型调整滑块范围
        if key in ["sharpness"]:
            self.slider_panel.slider.setRange(0, 100)
        elif key in ["hue"]:
            self.slider_panel.slider.setRange(-180, 180)
        else:
            self.slider_panel.slider.setRange(-100, 100)

    def on_slider_change(self, value):
        """滑块拖动回调"""
        self.engine.update_param(self.current_adjust_key, value)
        res = self.engine.render_final()
        self.canvas.set_image(res)

    def open_image(self):
        # ... (保持不变)
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.jpg *.png)")
        if path:
            img = self.engine.load_image(path)
            self.canvas.set_image(img)
            self.canvas.fit_in_view()
            # 重置
            self.switch_adjust_tool("brightness", self.adjust_btns[0])

    def save_image(self):
        # ... (保持不变)
        if self.engine.original_image is None: return
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", "edited_result.jpg", "Images (*.jpg *.png)")
        if not path: return
        
        final_image = self.engine.render(use_preview=False)
        if final_image is None: return

        try:
            save_img = cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR)
            ext = os.path.splitext(path)[1]
            is_success, im_buf = cv2.imencode(ext, save_img)
            if is_success:
                im_buf.tofile(path)
                print(f"图片已保存至: {path}")
        except Exception as e:
            print(f"保存失败: {e}")