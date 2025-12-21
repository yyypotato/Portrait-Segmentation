from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFileDialog, QFrame, QSizePolicy, 
                             QApplication, QMessageBox) 
import torch
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon
import cv2
import numpy as np
from src.models.factory import ModelFactory
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

        # --- 4. 智能合成 (简化版) ---
        col_comp_layout = QVBoxLayout()
        col_comp_layout.setSpacing(15)
        
        # 标题
        lbl_comp_title = QLabel("智能场景合成")
        lbl_comp_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2f3640;")
        lbl_comp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 合成预览图
        self.lbl_composite = QLabel()
        self.lbl_composite.setFixedSize(350, 400)
        self.lbl_composite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_composite.setText("合成预览\n(自动色彩融合 + 环境光溢出)")
        self.lbl_composite.setStyleSheet("background: white; border: 2px dashed #dcdde1; border-radius: 10px; color: #a4b0be;")

        # 按钮组
        btn_layout = QHBoxLayout()
        self.btn_bg = QPushButton("🖼️ 选择背景")
        self.btn_bg.clicked.connect(self.select_background)
        self.btn_bg.setEnabled(False)
        self.btn_bg.setStyleSheet("background-color: #6c5ce7; color: white; border-radius: 20px; font-weight: bold; padding: 8px;")
        self.btn_bg.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_save_comp = QPushButton("💾 保存合成")
        self.btn_save_comp.clicked.connect(self.save_composite)
        self.btn_save_comp.setEnabled(False)
        self.btn_save_comp.setStyleSheet("background-color: #00b894; color: white; border-radius: 20px; font-weight: bold; padding: 8px;")
        self.btn_save_comp.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_layout.addWidget(self.btn_bg)
        btn_layout.addWidget(self.btn_save_comp)

        col_comp_layout.addWidget(lbl_comp_title)
        col_comp_layout.addWidget(self.lbl_composite)
        # 移除了 adjust_panel
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
        nav_layout.addStretch()
        parent_layout.addWidget(nav_bar)

    def create_image_column(self, title_text, btn_obj_name, btn_text, btn_callback):
        """辅助函数：创建标准的图像显示列"""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2f3640;")
        
        lbl_image = QLabel()
        lbl_image.setFixedSize(280, 350)
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
        
        btn = QPushButton(btn_text)
        btn.setObjectName(btn_obj_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.clicked.connect(btn_callback)
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
        """创建中间的处理列"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        arrow = QLabel("➜")
        arrow.setStyleSheet("font-size: 40px; color: #bdc3c7; font-weight: bold;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "DeepLabV3+ (MobileNetV3)", 
            "DeepLabV3+ (ResNet101)", 
            "U-Net"
        ])
        self.combo_model.setFixedWidth(180)
        self.combo_model.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
                color: #2f3640;
                font-size: 14px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView {
                background: white;
                color: #2f3640;
                selection-background-color: #dfe6e9;
            }
        """)

        self.combo_size = QComboBox()
        self.combo_size.addItems([
            "原图尺寸 (显存大)",
            "限制 1024px (均衡)",
            "限制 512px (省显存)",
            "限制 256px (极速)"
        ])
        self.combo_size.setFixedWidth(180)
        self.combo_size.setCurrentIndex(2) 
        self.combo_size.setStyleSheet(self.combo_model.styleSheet())

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
            QPushButton:hover { background-color: #74b9ff; }
            QPushButton:disabled { background-color: #b2bec3; }
        """)

        layout.addStretch()
        layout.addWidget(arrow)
        layout.addWidget(self.combo_model)
        layout.addWidget(QLabel("推理尺寸:"))
        layout.addWidget(self.combo_size) 
        layout.addWidget(self.btn_run)
        layout.addStretch()
        return layout

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.current_image_path = file_name
            
            stream = np.fromfile(file_name, dtype=np.uint8)
            bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            self.original_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            
            h, w, c = self.original_rgb.shape
            qimg = QImage(self.original_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.lbl_original.setPixmap(pixmap.scaled(self.lbl_original.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_original.setStyleSheet("border: 2px solid #0984e3; border-radius: 10px;")
            
            self.btn_run.setEnabled(True)
            
            self.lbl_result.clear(); self.lbl_result.setText("等待处理...")
            self.lbl_composite.clear(); self.lbl_composite.setText("合成预览\n(自动色彩融合 + 环境光溢出)")
            
            self.btn_bg.setEnabled(False)
            self.btn_save_res.setEnabled(False)
            self.btn_save_comp.setEnabled(False)
            
            # 清空缓存
            self.mask_raw = None
            self.bg_rgb = None
            self.result_rgba = None
            self.composite_rgb = None

    def run_segmentation(self):
        if not self.current_image_path: return
        
        selected_model_name = self.combo_model.currentText()
        self.lbl_result.setText("正在加载模型...")
        self.lbl_result.setStyleSheet("border: 2px dashed #dcdde1; background-color: #f5f6fa; color: #636e72;")
        QApplication.processEvents()

        try:
            if self.model is None or self.current_model_name != selected_model_name:
                self.model = ModelFactory.create_model(selected_model_name)
                self.current_model_name = selected_model_name
            
            self.lbl_result.setText("正在推理中...")
            QApplication.processEvents()

            img_stream = np.fromfile(self.current_image_path, dtype=np.uint8)
            image_bgr = cv2.imdecode(img_stream, cv2.IMREAD_COLOR)
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            size_text = self.combo_size.currentText()
            max_size = None
            if "1024" in size_text: max_size = 1024
            elif "512" in size_text: max_size = 512
            elif "256" in size_text: max_size = 256

            mask = self.model.predict(image_rgb, max_size=max_size)
            self.mask_raw = mask 

            h, w, c = image_rgb.shape
            rgba_image = np.zeros((h, w, 4), dtype=np.uint8)
            rgba_image[:, :, :3] = image_rgb
            rgba_image[:, :, 3] = mask

            self.result_rgba = rgba_image

            qimg = QImage(rgba_image.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
            result_pix = QPixmap.fromImage(qimg)
            
            self.lbl_result.setPixmap(result_pix.scaled(self.lbl_result.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_result.setStyleSheet("border: 2px solid #00b894; border-radius: 10px;")
            
            self.btn_save_res.setEnabled(True)
            self.btn_bg.setEnabled(True)

        except torch.cuda.OutOfMemoryError:
            print("捕获到显存不足错误！")
            torch.cuda.empty_cache()
            QMessageBox.critical(self, "显存不足", "显存不足，请切换 MobileNetV3 或降低分辨率。")
            self.lbl_result.setText("显存不足")
        except Exception as e:
            print(f"分割出错: {e}")
            self.lbl_result.setText("运行出错")
            QMessageBox.warning(self, "错误", f"运行过程中发生错误：\n{str(e)}")

    def select_background(self):
        """选择背景图，并触发自动合成"""
        path, _ = QFileDialog.getOpenFileName(self, "选择背景", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            stream = np.fromfile(path, dtype=np.uint8)
            bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            self.bg_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            
            self.btn_save_comp.setEnabled(True)
            self.update_composite()

    def update_composite(self):
        """执行合成 (默认开启所有优化)"""
        if self.original_rgb is None or self.mask_raw is None or self.bg_rgb is None: return
        
        # 默认开启：自动色彩融合 + 环境光溢出
        self.composite_rgb = ImageProcessor.composite_images(
            self.original_rgb, 
            self.mask_raw, 
            self.bg_rgb,
            use_harmonize=True, 
            use_light_wrap=True, 
            brightness=0,
            roi_rects=None,
            display_size=(self.lbl_composite.width(), self.lbl_composite.height())
        )
        
        h, w, c = self.composite_rgb.shape
        qimg = QImage(self.composite_rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.lbl_composite.setPixmap(pix.scaled(self.lbl_composite.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.lbl_composite.setStyleSheet("border: 2px solid #6c5ce7; border-radius: 10px;")

    def save_result(self):
        if self.result_rgba is None: return
        self._save_image_data(self.result_rgba, "segmentation_result.png", is_rgba=True)

    def save_composite(self):
        if not hasattr(self, 'composite_rgb'): return
        self._save_image_data(self.composite_rgb, "composite_result.jpg", is_rgba=False)

    def _save_image_data(self, img_data, default_name, is_rgba=False):
        import os
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(root_dir, "output")
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        default_path = os.path.join(output_dir, default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", default_path, "PNG Images (*.png);;JPEG Images (*.jpg)"
        )

        if file_path:
            if is_rgba:
                save_img = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGRA)
            else:
                save_img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            
            ext = os.path.splitext(file_path)[1]
            is_success, im_buf = cv2.imencode(ext, save_img)
            if is_success:
                im_buf.tofile(file_path)
                print(f"图片已保存到: {file_path}")