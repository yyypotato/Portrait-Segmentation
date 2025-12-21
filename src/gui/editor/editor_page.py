from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFileDialog, QFrame)
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
        # 全局深色背景
        self.setStyleSheet("background-color: #1e272e;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 顶部栏 ---
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #2d3436; border-bottom: 1px solid #636e72;")
        top_layout = QHBoxLayout(top_bar)
        
        btn_back = QPushButton("← 退出编辑")
        btn_back.setStyleSheet("color: white; border: none; font-weight: bold;")
        btn_back.clicked.connect(self.go_back.emit)
        
        btn_open = QPushButton("📂 打开图片")
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
        
        # --- 3. 底部控制区 (仿手机 UI) ---
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(220) # 固定高度
        bottom_panel.setStyleSheet("background-color: #2d3436; border-top: 1px solid #636e72;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 3.1 参数调节滑块区
        self.slider_stack = QStackedWidget()
        
        # -> 调节页 (Light)
        page_light = QWidget()
        l_layout = QHBoxLayout(page_light)
        self.sl_bright = SliderControl("亮度", -100, 100)
        self.sl_bright.value_changed.connect(lambda v: self.update_img("brightness", v))
        self.sl_contrast = SliderControl("对比度", -100, 100)
        self.sl_contrast.value_changed.connect(lambda v: self.update_img("contrast", v))
        self.sl_sat = SliderControl("饱和度", -100, 100)
        self.sl_sat.value_changed.connect(lambda v: self.update_img("saturation", v))
        l_layout.addWidget(self.sl_bright); l_layout.addWidget(self.sl_contrast); l_layout.addWidget(self.sl_sat)
        
        # -> 色彩页 (Color) - 新增
        page_color = QWidget()
        c_layout = QHBoxLayout(page_color)
        self.sl_temp = SliderControl("色温", -50, 50)
        self.sl_temp.value_changed.connect(lambda v: self.update_img("temperature", v))
        self.sl_tint = SliderControl("色调", -50, 50)
        self.sl_tint.value_changed.connect(lambda v: self.update_img("tint", v))
        c_layout.addWidget(self.sl_temp); c_layout.addWidget(self.sl_tint)

        # -> 细节页 (Detail)
        page_detail = QWidget()
        d_layout = QHBoxLayout(page_detail)
        self.sl_sharp = SliderControl("锐化", 0, 100)
        self.sl_sharp.value_changed.connect(lambda v: self.update_img("sharpness", v))
        self.sl_vig = SliderControl("暗角", 0, 100) # 新增
        self.sl_vig.value_changed.connect(lambda v: self.update_img("vignette", v))
        d_layout.addWidget(self.sl_sharp); d_layout.addWidget(self.sl_vig)

        self.slider_stack.addWidget(page_light)  # 0
        self.slider_stack.addWidget(page_color)  # 1
        self.slider_stack.addWidget(page_detail) # 2

        # 3.2 底部菜单栏 (一级菜单)
        menu_bar = QWidget()
        menu_bar.setFixedHeight(80)
        menu_layout = QHBoxLayout(menu_bar)
        menu_layout.setSpacing(20)
        menu_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_light = ToolButton("光效", "☀️")
        self.btn_light.setChecked(True)
        self.btn_light.clicked.connect(lambda: self.switch_tab(0, self.btn_light))
        
        self.btn_color = ToolButton("色彩", "🎨") # 新增
        self.btn_color.clicked.connect(lambda: self.switch_tab(1, self.btn_color))

        self.btn_detail = ToolButton("细节", "🔺")
        self.btn_detail.clicked.connect(lambda: self.switch_tab(2, self.btn_detail))

        menu_layout.addWidget(self.btn_light)
        menu_layout.addWidget(self.btn_color)
        menu_layout.addWidget(self.btn_detail)

        bottom_layout.addWidget(self.slider_stack)
        bottom_layout.addWidget(menu_bar)

        # 组装
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.canvas, 1) # 画布占满剩余空间
        main_layout.addWidget(bottom_panel)

        # 按钮组管理
        self.menu_btns = [self.btn_light, self.btn_color, self.btn_detail]

    def switch_tab(self, index, btn_sender):
        self.slider_stack.setCurrentIndex(index)
        for btn in self.menu_btns:
            btn.setChecked(False)
        btn_sender.setChecked(True)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", "Images (*.jpg *.png)")
        if path:
            img = self.engine.load_image(path)
            self.canvas.set_image(img)
            self.canvas.fit_in_view()
            # 重置滑块
            self.sl_bright.set_value(0)
            self.sl_contrast.set_value(0)
            self.sl_sat.set_value(0)

    def update_img(self, key, value):
        """实时更新图像"""
        self.engine.update_param(key, value)
        # 渲染最终图 (包含饱和度等)
        res = self.engine.render_final()
        self.canvas.set_image(res)

    def save_image(self):
        """保存编辑后的高清大图"""
        if self.engine.original_image is None: return
        
        # 1. 获取保存路径
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", "edited_result.jpg", "Images (*.jpg *.png)")
        if not path: return

        # 2. 渲染全分辨率图像 (关键：use_preview=False)
        # 这会应用所有当前的参数到原始高清图上
        final_image = self.engine.render(use_preview=False)
        
        if final_image is None: return
        # 3. 保存图像
        try:
            save_img = cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR)
            ext = os.path.splitext(path)[1]
            is_success, im_buf = cv2.imencode(ext, save_img)
            if is_success:
                im_buf.tofile(path)
                print(f"图片已保存到: {path}")
        except Exception as e:
            print(f"保存图片失败: {e}")