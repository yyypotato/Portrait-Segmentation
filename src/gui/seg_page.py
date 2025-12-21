from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFileDialog, QFrame, QSizePolicy, 
                             QApplication, QMessageBox, QGroupBox, QFormLayout, QSlider) 
from PyQt6.QtWidgets import QCheckBox
import torch
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QIcon
from .styles import Styles
import cv2
import numpy as np
from src.models.factory import ModelFactory
from src.gui.custom_widgets import InteractiveLabel
from src.utils.image_processor import ImageProcessor

class SegPage(QWidget):
    go_back = pyqtSignal() # 返回菜单信号

    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.model = None
        self.current_model_name = ""
        
        # 数据缓存
        self.original_rgb = None
        self.mask_raw = None
        self.bg_rgb = None
        self.result_rgba = None
        self.composite_rgb = None
        
        # 缩略图缓存 (用于快速预览)
        self.preview_fg = None
        self.preview_bg = None
        self.preview_mask = None
        self.preview_scale = 1.0

        self.params = {
            "use_harmonize": False, # 改动
            "use_light_wrap": False, # 改动
            "brightness": 0,
            "roi_rects": []
        }

        # --- 防抖定时器 (解决卡顿的关键) ---
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(50) # 50ms 延迟
        self.update_timer.timeout.connect(self.perform_update)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_top_bar(main_layout)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f6fa;")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(20)

        # 1. 原始图像
        col_orig = self.create_image_column("原始图像", "btn_upload", "📂 上传图像", self.load_image)
        self.lbl_original = col_orig["label"]
        self.btn_upload = col_orig["btn"]

        # 2. 处理控制
        col_proc = self.create_process_column()

        # 3. 分割结果
        col_res = self.create_image_column("分割结果", "btn_save_seg", "💾 保存透明图", self.save_result)
        self.lbl_result = col_res["label"]
        self.btn_save_res = col_res["btn"]
        self.btn_save_res.setEnabled(False)

        # --- 4. 场景合成与精修 (合并了原来的逻辑列和显示列) ---
        col_comp_layout = QVBoxLayout()
        col_comp_layout.setSpacing(10)
        
        # 标题
        lbl_comp_title = QLabel("场景合成与精修")
        lbl_comp_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2f3640;")
        lbl_comp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 合成预览图 (使用自定义 InteractiveLabel)
        self.lbl_composite = InteractiveLabel()
        self.lbl_composite.setFixedSize(350, 400) # 稍微宽一点
        self.lbl_composite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_composite.setText("场景合成预览\n(支持鼠标框选虚化)")
        self.lbl_composite.setStyleSheet("background: white; border: 2px dashed #dcdde1; border-radius: 10px; color: #a4b0be;")
        self.lbl_composite.selection_made.connect(self.add_roi_blur) # 连接框选信号

        # 调节面板
        self.adjust_panel = self.create_adjust_panel()
        self.adjust_panel.setEnabled(False)

        # 按钮组
        btn_layout = QHBoxLayout()
        self.btn_bg = QPushButton("🖼️ 选择背景")
        self.btn_bg.clicked.connect(self.select_background)
        self.btn_bg.setEnabled(False)
        # 复用之前的样式逻辑，或者直接设置
        self.btn_bg.setStyleSheet("background-color: #6c5ce7; color: white; border-radius: 20px; font-weight: bold; padding: 8px;")

        self.btn_save_comp = QPushButton("💾 保存合成")
        self.btn_save_comp.clicked.connect(self.save_composite)
        self.btn_save_comp.setEnabled(False)
        self.btn_save_comp.setStyleSheet("background-color: #00b894; color: white; border-radius: 20px; font-weight: bold; padding: 8px;")

        btn_layout.addWidget(self.btn_bg)
        btn_layout.addWidget(self.btn_save_comp)

        col_comp_layout.addWidget(lbl_comp_title)
        col_comp_layout.addWidget(self.lbl_composite)
        col_comp_layout.addWidget(self.adjust_panel)
        col_comp_layout.addLayout(btn_layout)
        col_comp_layout.addStretch()

        # 添加所有列
        content_layout.addStretch(1)
        content_layout.addLayout(col_orig["layout"])
        content_layout.addLayout(col_proc)
        content_layout.addLayout(col_res["layout"])
        content_layout.addLayout(col_comp_layout)
        content_layout.addStretch(1)

        main_layout.addWidget(content_widget)

    def setup_top_bar(self, parent_layout):
        """设置顶部导航栏"""
        nav_bar = QWidget()
        nav_bar.setStyleSheet("background-color: white; border-bottom: 1px solid #dcdde1;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(20, 10, 20, 10)

        btn_back = QPushButton("← 返回菜单")
        btn_back.setFixedWidth(120)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        # 使用样式表覆盖默认样式，使其更简洁
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2f3640;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f1f2f6;
                color: #0984e3;
                border-color: #0984e3;
            }
        """)
        btn_back.clicked.connect(self.go_back.emit)

        nav_layout.addWidget(btn_back)
        nav_layout.addStretch() # 占满右边
        
        parent_layout.addWidget(nav_bar)

    def create_image_column(self, title_text, btn_obj_name, btn_text, btn_callback):
        """辅助函数：创建标准的图像显示列 (标题 + 图片框 + 按钮)"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # 标题
        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2f3640;")
        
        # 图片框 (卡片样式)
        lbl_image = QLabel()
        lbl_image.setFixedSize(280, 350) # 固定大小，保持整齐
        lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_image.setText("暂无图像")
        lbl_image.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px dashed #dcdde1;
                border-radius: 10px;
                color: #a4b0be;
            }
        """)
        
        # 按钮
        btn = QPushButton(btn_text)
        btn.setObjectName(btn_obj_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.clicked.connect(btn_callback)
        # 默认按钮样式
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 20px;
                color: #2f3640;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f1f2f6;
                border-color: #b2bec3;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(lbl_image)
        layout.addWidget(btn)
        
        return {"layout": layout, "label": lbl_image, "btn": btn}

    def create_process_column(self):
        """创建中间的处理列 (箭头 -> 模型 -> 按钮)"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # 垂直居中

        # 箭头
        arrow = QLabel("➜")
        arrow.setStyleSheet("font-size: 40px; color: #bdc3c7; font-weight: bold;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 模型选择
        self.combo_model = QComboBox()
        # 【修改点1】将 DeepLabV3+ 放在第一个，作为默认选项
        self.combo_model.addItems([
            "DeepLabV3+ (MobileNetV3)", # 推荐默认选这个，不容易崩
            "DeepLabV3+ (ResNet101)", 
            "U-Net"
        ])
        self.combo_model.setFixedWidth(180)
        
        # 【修改点2】强制设置文字颜色 (color)，防止白底白字
        self.combo_model.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                color: #2f3640;  /* 关键：强制深色文字 */
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QComboBox QAbstractItemView {
                background: white;
                color: #2f3640;
                selection-background-color: #dfe6e9;
            }
        """)
        # --- 新增：输入尺寸选择 ---
        self.combo_size = QComboBox()
        self.combo_size.addItems([
            "原图尺寸 (显存大)",
            "限制 1024px (均衡)",
            "限制 512px (省显存)",
            "限制 256px (极速)"
        ])
        self.combo_size.setFixedWidth(180)
        self.combo_size.setToolTip("降低输入尺寸可以大幅减少显存占用，\n让 ResNet101 也能在普通显卡上运行。")
        self.combo_size.setStyleSheet(self.combo_model.styleSheet()) # 复用样式
        
        # 默认选中 "限制 512px" (比较稳妥)
        self.combo_size.setCurrentIndex(2) 

        # 分割按钮 (主要操作，用醒目的颜色)
        self.btn_run = QPushButton("⚡ 开始分割")
        self.btn_run.setFixedWidth(120)
        self.btn_run.setFixedHeight(40)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.run_segmentation)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74b9ff;
            }
            QPushButton:disabled {
                background-color: #b2bec3;
            }
        """)

        layout.addStretch()
        layout.addWidget(arrow)
        layout.addWidget(self.combo_model)
        layout.addWidget(QLabel("推理尺寸:")) # 建议加个标签提示
        layout.addWidget(self.combo_size) 
        layout.addWidget(self.btn_run)
        layout.addStretch()
        
        return layout

    def create_adjust_panel(self):
        group = QGroupBox("智能合成控制")
        group.setMinimumHeight(200)
        group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #bdc3c7; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 20px; 
                background: white; 
                color: #2d3436; /* 强制标题颜色为深灰 */
                font-size: 14px;
            }
            QCheckBox { 
                font-size: 14px; 
                padding: 5px; 
                color: #2d3436; /* 强制复选框文字颜色 */
                font-weight: bold;
            }
            QLabel {
                color: #2d3436; /* 强制标签文字颜色 */
                font-weight: bold;
                font-size: 13px;
            }
            QCheckBox::indicator { width: 20px; height: 20px; }
        """)
        
        layout = QFormLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 25, 15, 15)

        # 1. 自动色彩融合 (取代复杂的调色)
        self.chk_harmonize = QCheckBox("🎨 自动色彩融合")
        self.chk_harmonize.setToolTip("自动调整人像色调以匹配背景")
        self.chk_harmonize.stateChanged.connect(lambda v: self.update_params("use_harmonize", v == 2))
        layout.addRow(self.chk_harmonize)

        # 2. 环境光溢出 (取代羽化)
        self.chk_wrap = QCheckBox("💡 环境光溢出")
        self.chk_wrap.setToolTip("让背景光线照射到人像边缘，消除抠图感")
        self.chk_wrap.stateChanged.connect(lambda v: self.update_params("use_light_wrap", v == 2))
        layout.addRow(self.chk_wrap)

        # 3. 简单亮度
        self.slider_bright = QSlider(Qt.Orientation.Horizontal)
        self.slider_bright.setRange(-50, 50)
        self.slider_bright.valueChanged.connect(lambda v: self.update_params("brightness", v))
        layout.addRow("人像亮度:", self.slider_bright)

        # 4. 清除
        btn_clear = QPushButton("清除局部虚化")
        btn_clear.clicked.connect(self.clear_roi)
        layout.addRow("", btn_clear)

        group.setLayout(layout)
        return group
    
    def create_composite_logic_column(self):
        """创建合成逻辑列 (箭头 -> 选择背景)"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 箭头
        arrow = QLabel("➜")
        arrow.setStyleSheet("font-size: 40px; color: #bdc3c7; font-weight: bold;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 选择背景按钮
        self.btn_bg = QPushButton("🖼️ 选择背景")
        self.btn_bg.setFixedWidth(120)
        self.btn_bg.setFixedHeight(40)
        self.btn_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bg.clicked.connect(self.select_background)
        self.btn_bg.setEnabled(False) # 需要先有分割结果才能选背景
        self.btn_bg.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a29bfe;
            }
            QPushButton:disabled {
                background-color: #b2bec3;
            }
        """)

        layout.addStretch()
        layout.addWidget(arrow)
        layout.addWidget(self.btn_bg)
        layout.addStretch()

        return layout

    # --- 逻辑功能区 (保持原有逻辑并扩展) ---

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.current_image_path = file_name
            
            # 1. 读取并保存原始数据
            stream = np.fromfile(file_name, dtype=np.uint8)
            bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            self.original_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            
            # 2. 显示图片
            h, w, c = self.original_rgb.shape
            qimg = QImage(self.original_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.lbl_original.setPixmap(pixmap.scaled(self.lbl_original.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_original.setStyleSheet("border: 2px solid #0984e3; border-radius: 10px;")
            
            # 3. 激活分割按钮
            self.btn_run.setEnabled(True)
            
            # 4. 重置显示状态
            self.lbl_result.clear(); self.lbl_result.setText("等待处理...")
            self.lbl_composite.clear(); self.lbl_composite.setText("等待合成...")
            
            self.btn_bg.setEnabled(False)
            self.btn_save_res.setEnabled(False)
            self.btn_save_comp.setEnabled(False)
            
            # 5. 重置调节面板 (修复报错的关键步骤)
            self.adjust_panel.setEnabled(False)
            self.params["roi_rects"] = [] 
            
            # --- 修复点：重置新的控件，而不是旧的滑块 ---
            if hasattr(self, 'chk_harmonize'): self.chk_harmonize.setChecked(False)
            if hasattr(self, 'chk_wrap'): self.chk_wrap.setChecked(False)
            if hasattr(self, 'slider_bright'): self.slider_bright.setValue(0)
            
            # 6. 清空缓存
            self.mask_raw = None
            self.bg_rgb = None
            self.result_rgba = None
            self.composite_rgb = None

    def run_segmentation(self):
        """执行分割逻辑"""
        if not self.current_image_path:
            return
        
        # 1. 获取用户选择的模型名称
        selected_model_name = self.combo_model.currentText()
        
        # 更新界面提示
        self.lbl_result.setText("正在加载模型...")
        self.lbl_result.setStyleSheet("border: 2px dashed #dcdde1; background-color: #f5f6fa; color: #636e72;")
        QApplication.processEvents() # 强制刷新界面，防止卡死

        try:
            # 2. 获取/切换模型
            # 如果模型还没加载，或者用户切换了下拉框，就重新创建模型
            if self.model is None or self.current_model_name != selected_model_name:
                self.model = ModelFactory.create_model(selected_model_name)
                self.current_model_name = selected_model_name
            
            self.lbl_result.setText("正在推理中...")
            QApplication.processEvents()

            # 3. 读取图像 (处理中文路径)
            # 使用 numpy 读取文件流，再用 cv2 解码，可以完美支持中文路径
            img_stream = np.fromfile(self.current_image_path, dtype=np.uint8)
            image_bgr = cv2.imdecode(img_stream, cv2.IMREAD_COLOR)
            # OpenCV 默认是 BGR，模型需要 RGB
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            # 获取用户选择的尺寸限制
            size_text = self.combo_size.currentText()
            max_size = None
            if "1024" in size_text: max_size = 1024
            elif "512" in size_text: max_size = 512
            elif "256" in size_text: max_size = 256
            # "原图尺寸" 则 max_size 为 None

            # 4. 模型推理
            # 返回的是 (H, W) 的掩码，0是背景，255是人像
            mask = self.model.predict(image_rgb,max_size=max_size)

            # 【重要修复】保存原始 mask，否则后续合成功能无法使用！
            self.mask_raw = mask 

            # 5. 后处理：生成透明背景图 (RGBA)
            h, w, c = image_rgb.shape
            rgba_image = np.zeros((h, w, 4), dtype=np.uint8)
            rgba_image[:, :, :3] = image_rgb # 填充 RGB
            rgba_image[:, :, 3] = mask       # 填充 Alpha 通道 (掩码)

            # 保存结果数据供后续使用
            self.result_rgba = rgba_image

            # 6. 显示结果
            # 注意：QImage 必须保持数据引用，否则会崩溃，所以这里直接转 pixmap
            qimg = QImage(rgba_image.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
            result_pix = QPixmap.fromImage(qimg)
            
            self.lbl_result.setPixmap(result_pix.scaled(self.lbl_result.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_result.setStyleSheet("border: 2px solid #00b894; border-radius: 10px;") # 变绿表示成功
            
            # 激活后续按钮
            self.btn_save_res.setEnabled(True)
            self.btn_bg.setEnabled(True)

        except torch.cuda.OutOfMemoryError:
            # 【新增】专门捕获显存不足错误
            print("捕获到显存不足错误！")
            torch.cuda.empty_cache() # 清理显存碎片
            
            QMessageBox.critical(
                self, 
                "显存不足 (Out of Memory)", 
                "您的显卡显存不足以运行当前模型。\n\n"
                "建议方案：\n"
                "1. 请在下拉框中切换为 'DeepLabV3+ (MobileNetV3)'。\n"
                "2. 或者尝试使用分辨率较小的图片。"
            )
            self.lbl_result.setText("显存不足")

        except Exception as e:
            # 其他错误
            print(f"分割出错: {e}")
            self.lbl_result.setText("运行出错")
            QMessageBox.warning(self, "错误", f"运行过程中发生错误：\n{str(e)}")
            import traceback
            traceback.print_exc()

    def select_background(self):
        """选择背景图，并触发首次合成"""
        path, _ = QFileDialog.getOpenFileName(self, "选择背景", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            stream = np.fromfile(path, dtype=np.uint8)
            bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            self.bg_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            
            # 激活调整面板和保存按钮
            self.adjust_panel.setEnabled(True)
            self.btn_save_comp.setEnabled(True)
            
            # 执行合成
            self.update_composite()

    # --- 新增以下方法 ---

    def update_params(self, key, value):
        """滑块回调：只更新参数，启动定时器"""
        self.params[key] = value
        # 重置定时器，只有当用户停止拖动 50ms 后才真正计算
        self.update_timer.start()

    def perform_update(self):
        """真正的合成逻辑 (由定时器触发)"""
        self.update_composite()

    def add_roi_blur(self, rect):
        if self.composite_rgb is None: return
        self.params["roi_rects"].append(rect)
        self.update_composite() # 框选不需要防抖，直接更新

    def clear_roi(self):
        self.params["roi_rects"] = []
        self.update_composite()

    def update_composite(self):
        if self.original_rgb is None or self.mask_raw is None or self.bg_rgb is None: return
        
        self.composite_rgb = ImageProcessor.composite_images(
            self.original_rgb, 
            self.mask_raw, 
            self.bg_rgb,
            use_harmonize=self.params["use_harmonize"], # 传参变化
            use_light_wrap=self.params["use_light_wrap"], # 传参变化
            brightness=self.params["brightness"],
            roi_rects=self.params["roi_rects"],
            display_size=(self.lbl_composite.width(), self.lbl_composite.height())
        )
        
        # 显示
        h, w, c = self.composite_rgb.shape
        qimg = QImage(self.composite_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.lbl_composite.setPixmap(pix.scaled(self.lbl_composite.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))

    def save_result(self):
        """保存透明背景的分割结果"""
        if self.result_rgba is None:
            return
        self._save_image_data(self.result_rgba, "segmentation_result.png", is_rgba=True)

    def save_composite(self):
        """保存合成后的图片"""
        if not hasattr(self, 'composite_rgb'):
            return
        self._save_image_data(self.composite_rgb, "composite_result.jpg", is_rgba=False)

    def _save_image_data(self, img_data, default_name, is_rgba=False):
        """辅助保存函数"""
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(root_dir, "output")
        default_path = os.path.join(output_dir, default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", default_path, "PNG Images (*.png);;JPEG Images (*.jpg)"
        )

        if file_path:
            # OpenCV 保存需要 BGR 格式
            if is_rgba:
                save_img = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGRA)
            else:
                save_img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            
            # cv2.imencode 支持中文路径保存
            ext = os.path.splitext(file_path)[1]
            is_success, im_buf = cv2.imencode(ext, save_img)
            if is_success:
                im_buf.tofile(file_path)
                print(f"保存成功: {file_path}")