from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFileDialog, QFrame, QSizePolicy, 
                             QApplication, QMessageBox, QGraphicsDropShadowEffect) 
import torch
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QImage, QColor, QCursor
import cv2
import numpy as np
from src.models.factory import ModelFactory
from src.utils.image_processor import ImageProcessor
# [新增] 导入修正层
from .mask_refine_overlay import MaskRefineOverlay

# [新增] 可点击的 Label
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

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
        
        # [新增] 初始化修正覆盖层 (初始隐藏)
        self.refine_overlay = MaskRefineOverlay(self)
        self.refine_overlay.hide()
        self.refine_overlay.finished.connect(self.on_mask_refined)

    def resizeEvent(self, event):
        # 确保覆盖层始终跟随窗口大小
        self.refine_overlay.resize(self.size())
        super().resizeEvent(event)

    def init_ui(self):
        self.setObjectName("SegPage")
        self.setStyleSheet("""
            QWidget#SegPage {
                background-color: #141824;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Microsoft YaHei', 'Segoe UI';
            }
            QFrame.Card {
                background-color: #1f2435;
                border-radius: 16px;
                border: 1px solid #2b3042;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部导航
        self.setup_top_bar(main_layout)

        # 内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)
        content_layout.setSpacing(25)

        # 1. 原始图像卡片
        self.card_orig, self.lbl_original, self.btn_upload = self.create_image_card(
            "原始图像", "上传图片", self.load_image
        )

        # 2. 处理控制区
        self.layout_proc = self.create_process_column()

        # 3. 分割结果卡片
        # [修改] 使用 create_result_card 以支持点击
        self.card_res, self.lbl_result, self.btn_save_res = self.create_result_card(
            "分割结果", "保存透明图", self.save_result
        )
        self.btn_save_res.setEnabled(False)

        # 4. 智能合成卡片
        self.card_comp = self.create_composite_card()

        # 添加到布局
        content_layout.addWidget(self.card_orig)
        content_layout.addLayout(self.layout_proc)
        content_layout.addWidget(self.card_res)
        content_layout.addWidget(self.card_comp)

        main_layout.addWidget(content_widget)

    def setup_top_bar(self, parent_layout):
        """设置顶部导航栏"""
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
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        btn_back.clicked.connect(self.go_back.emit)
        
        # 装饰性箭头
        arrow = QLabel("‹")
        arrow.setStyleSheet("color: #00f2ea; font-size: 24px; font-weight: bold; margin-right: 5px;")

        back_container = QHBoxLayout()
        back_container.setSpacing(0)
        back_container.addWidget(arrow)
        back_container.addWidget(btn_back)
        
        nav_layout.addLayout(back_container)
        nav_layout.addStretch()
        
        # 页面标题
        page_title = QLabel("智能抠图工作台")
        page_title.setStyleSheet("font-size: 16px; color: #5c6375; font-weight: bold;")
        nav_layout.addWidget(page_title)

        parent_layout.addWidget(nav_bar)

    def create_image_card(self, title_text, btn_text, btn_callback):
        """创建标准的图像显示卡片"""
        card = QFrame()
        card.setProperty("class", "Card")
        card.setFixedWidth(320)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        
        # 图片容器
        lbl_image = QLabel()
        lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_image.setText("等待导入")
        lbl_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lbl_image.setStyleSheet("""
            QLabel {
                background-color: #141824;
                border: 2px dashed #2b3042;
                border-radius: 12px;
                color: #5c6375;
                font-size: 13px;
            }
        """)
        
        # 按钮
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.clicked.connect(btn_callback)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b3042;
                border: 1px solid #3e4559;
                border-radius: 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #353b50;
                border-color: #00f2ea;
                color: #00f2ea;
            }
            QPushButton:disabled {
                background-color: #1f2435;
                color: #5c6375;
                border-color: #2b3042;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(lbl_image)
        layout.addWidget(btn)
        
        # 添加阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        return card, lbl_image, btn

    # [新增] 专门用于结果卡片的创建方法，使用 ClickableLabel
    def create_result_card(self, title_text, btn_text, btn_callback):
        card = QFrame()
        card.setProperty("class", "Card")
        card.setFixedWidth(320)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        
        # [修改] 使用 ClickableLabel
        lbl_image = ClickableLabel()
        lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_image.setText("等待处理")
        lbl_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lbl_image.setCursor(Qt.CursorShape.PointingHandCursor) # 提示可点击
        lbl_image.setToolTip("点击图片进行手动修正")
        lbl_image.clicked.connect(self.open_refine_overlay) # 连接点击事件
        
        lbl_image.setStyleSheet("""
            QLabel {
                background-color: #141824;
                border: 2px dashed #2b3042;
                border-radius: 12px;
                color: #5c6375;
                font-size: 13px;
            }
            QLabel:hover {
                border-color: #00f2ea;
            }
        """)
        
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.clicked.connect(btn_callback)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b3042;
                border: 1px solid #3e4559;
                border-radius: 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #353b50;
                border-color: #00f2ea;
                color: #00f2ea;
            }
            QPushButton:disabled {
                background-color: #1f2435;
                color: #5c6375;
                border-color: #2b3042;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(lbl_image)
        layout.addWidget(btn)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        return card, lbl_image, btn

    def create_process_column(self):
        """创建中间的处理列"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 装饰性箭头
        arrow = QLabel("›")
        arrow.setStyleSheet("font-size: 40px; color: #2b3042; font-weight: bold;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 模型选择
        lbl_model = QLabel("选择模型")
        lbl_model.setStyleSheet("color: #5c6375; font-size: 12px; font-weight: bold;")
        
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "DeepLabV3+ (MobileNetV3)", 
            "DeepLabV3+ (ResNet101)", 
            "U-Net"
        ])
        self.combo_model.setFixedWidth(200)
        self.combo_model.setFixedHeight(35)
        self.combo_model.setStyleSheet("""
            QComboBox {
                padding-left: 10px;
                border: 1px solid #2b3042;
                border-radius: 8px;
                background: #1f2435;
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox::drop-down { border: 0px; }
            QComboBox::down-arrow { 
                image: none; 
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #5c6375;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #1f2435;
                color: #ffffff;
                selection-background-color: #2b3042;
                border: 1px solid #2b3042;
            }
        """)

        # 尺寸选择
        lbl_size = QLabel("推理精度")
        lbl_size.setStyleSheet("color: #5c6375; font-size: 12px; font-weight: bold;")

        self.combo_size = QComboBox()
        self.combo_size.addItems([
            "原图尺寸 (高显存)",
            "限制 1024px (均衡)",
            "限制 512px (快速)",
            "限制 256px (极速)"
        ])
        self.combo_size.setFixedWidth(200)
        self.combo_size.setFixedHeight(35)
        self.combo_size.setCurrentIndex(2) 
        self.combo_size.setStyleSheet(self.combo_model.styleSheet())

        # 运行按钮
        self.btn_run = QPushButton("开始分割")
        self.btn_run.setFixedWidth(200)
        self.btn_run.setFixedHeight(45)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.run_segmentation)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2ea, stop:1 #00c6fb);
                color: #141824;
                border: none;
                border-radius: 22px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33f5ef, stop:1 #33d1fc);
            }
            QPushButton:disabled { 
                background: #2b3042;
                color: #5c6375;
            }
        """)

        layout.addStretch()
        layout.addWidget(arrow)
        layout.addSpacing(10)
        layout.addWidget(lbl_model)
        layout.addWidget(self.combo_model)
        layout.addSpacing(5)
        layout.addWidget(lbl_size)
        layout.addWidget(self.combo_size) 
        layout.addSpacing(20)
        layout.addWidget(self.btn_run)
        layout.addStretch()
        return layout

    def create_composite_card(self):
        """创建合成卡片"""
        card = QFrame()
        card.setProperty("class", "Card")
        card.setFixedWidth(320)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("智能场景合成")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")

        self.lbl_composite = QLabel()
        self.lbl_composite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_composite.setText("合成预览\n(自动色彩融合)")
        self.lbl_composite.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_composite.setStyleSheet("""
            QLabel {
                background-color: #141824;
                border: 2px dashed #2b3042;
                border-radius: 12px;
                color: #5c6375;
                font-size: 13px;
            }
        """)

        # 按钮组
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_bg = QPushButton("选择背景")
        self.btn_bg.clicked.connect(self.select_background)
        self.btn_bg.setEnabled(False)
        self.btn_bg.setFixedHeight(40)
        self.btn_bg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bg.setStyleSheet("""
            QPushButton {
                background-color: #2b3042;
                border: 1px solid #3e4559;
                border-radius: 8px;
                color: #ffffff;
            }
            QPushButton:hover {
                border-color: #eab308;
                color: #eab308;
            }
            QPushButton:disabled {
                color: #5c6375;
            }
        """)

        self.btn_save_comp = QPushButton("保存合成")
        self.btn_save_comp.clicked.connect(self.save_composite)
        self.btn_save_comp.setEnabled(False)
        self.btn_save_comp.setFixedHeight(40)
        self.btn_save_comp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_comp.setStyleSheet("""
            QPushButton {
                background-color: #2b3042;
                border: 1px solid #3e4559;
                border-radius: 8px;
                color: #ffffff;
            }
            QPushButton:hover {
                border-color: #00f2ea;
                color: #00f2ea;
            }
            QPushButton:disabled {
                color: #5c6375;
            }
        """)

        btn_layout.addWidget(self.btn_bg)
        btn_layout.addWidget(self.btn_save_comp)

        layout.addWidget(title)
        layout.addWidget(self.lbl_composite)
        layout.addLayout(btn_layout)

        # 添加阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        card.setGraphicsEffect(shadow)

        return card

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
            # 更新样式：青色边框
            self.lbl_original.setStyleSheet("border: 2px solid #00f2ea; border-radius: 12px;")
            
            self.btn_run.setEnabled(True)
            
            self.lbl_result.clear(); self.lbl_result.setText("等待处理...")
            self.lbl_composite.clear(); self.lbl_composite.setText("合成预览\n(自动色彩融合)")
            
            self.btn_bg.setEnabled(False)
            self.btn_save_res.setEnabled(False)
            self.btn_save_comp.setEnabled(False)
            
            self.mask_raw = None
            self.bg_rgb = None
            self.result_rgba = None
            self.composite_rgb = None

    def run_segmentation(self):
        if not self.current_image_path: return
        
        selected_model_name = self.combo_model.currentText()
        self.lbl_result.setText("正在加载模型...")
        self.lbl_result.setStyleSheet("border: 2px dashed #2b3042; background-color: #141824; color: #5c6375;")
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

            self.update_result_display() # 封装显示逻辑

        except torch.cuda.OutOfMemoryError:
            print("捕获到显存不足错误！")
            torch.cuda.empty_cache()
            QMessageBox.critical(self, "显存不足", "显存不足，请切换 MobileNetV3 或降低分辨率。")
            self.lbl_result.setText("显存不足")
        except Exception as e:
            print(f"分割出错: {e}")
            self.lbl_result.setText("运行出错")
            QMessageBox.warning(self, "错误", f"运行过程中发生错误：\n{str(e)}")

    def update_result_display(self):
        """更新结果显示 (在分割完成或修正完成后调用)"""
        if self.original_rgb is None or self.mask_raw is None: return

        h, w, c = self.original_rgb.shape
        rgba_image = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_image[:, :, :3] = self.original_rgb
        rgba_image[:, :, 3] = self.mask_raw

        self.result_rgba = rgba_image

        qimg = QImage(rgba_image.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
        result_pix = QPixmap.fromImage(qimg)
        
        self.lbl_result.setPixmap(result_pix.scaled(self.lbl_result.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.lbl_result.setStyleSheet("border: 2px solid #00f2ea; border-radius: 12px;")
        
        self.btn_save_res.setEnabled(True)
        self.btn_bg.setEnabled(True)
        
        # 如果有背景，也更新合成图
        if self.bg_rgb is not None:
            self.update_composite()

    # [新增] 打开修正覆盖层
    def open_refine_overlay(self):
        if self.original_rgb is None or self.mask_raw is None:
            return
        
        # 将数据传递给覆盖层
        self.refine_overlay.set_data(self.original_rgb, self.mask_raw)
        self.refine_overlay.resize(self.size())
        self.refine_overlay.show()
        self.refine_overlay.raise_() # 确保在最上层

    # [新增] 修正完成回调
    def on_mask_refined(self, new_mask):
        if new_mask is not None:
            self.mask_raw = new_mask
            self.update_result_display()
            QMessageBox.information(self, "成功", "蒙版修正已应用！")

    def select_background(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择背景", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            stream = np.fromfile(path, dtype=np.uint8)
            bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            self.bg_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            
            self.btn_save_comp.setEnabled(True)
            self.update_composite()

    def update_composite(self):
        if self.original_rgb is None or self.mask_raw is None or self.bg_rgb is None: return
        
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
        # 更新样式：黄色边框
        self.lbl_composite.setStyleSheet("border: 2px solid #eab308; border-radius: 12px;")

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