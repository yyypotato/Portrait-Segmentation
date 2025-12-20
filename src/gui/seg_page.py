from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFileDialog, QFrame, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon
from .styles import Styles
import cv2
import numpy as np
from src.models.factory import ModelFactory

class SegPage(QWidget):
    go_back = pyqtSignal() # 返回菜单信号

    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.model = None           # 当前加载的模型实例
        self.current_model_name = "" # 当前加载的模型名称
        self.result_rgba = None
        self.init_ui()

    def init_ui(self):
        # 主布局：垂直方向
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # 去除边缘，让顶部栏贴边
        main_layout.setSpacing(0)

        # 1. 顶部导航栏 (左上角返回按钮)
        self.setup_top_bar(main_layout)

        # 2. 主要工作区 (包含三个图像框和中间的操作列)
        content_widget = QWidget()
        # 给工作区加一个浅灰色的背景，突出中间的白色卡片
        content_widget.setStyleSheet("background-color: #f5f6fa;") 
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 20, 40, 40)
        content_layout.setSpacing(20) # 列与列之间的间距

        # --- 第一列：原始图像 ---
        col_original = self.create_image_column("原始图像", "btn_upload", "📂 上传图像", self.load_image)
        self.lbl_original = col_original["label"]
        self.btn_upload = col_original["btn"]

        # --- 第二列：处理逻辑 (箭头 + 模型 + 分割) ---
        col_process = self.create_process_column()

        # --- 第三列：分割结果 ---
        col_result = self.create_image_column("分割结果", "btn_save_seg", "💾 保存结果", self.save_result)
        self.lbl_result = col_result["label"]
        self.btn_save_result = col_result["btn"]
        self.btn_save_result.setEnabled(False) # 初始禁用

        # --- 第四列：合成逻辑 (箭头 + 背景选择) ---
        col_composite_logic = self.create_composite_logic_column()

        # --- 第五列：场景合成 ---
        col_composite = self.create_image_column("场景合成", "btn_save_comp", "💾 保存合成", self.save_composite)
        self.lbl_composite = col_composite["label"]
        self.btn_save_composite = col_composite["btn"]
        self.btn_save_composite.setEnabled(False)

        # 将所有列加入布局
        content_layout.addStretch(1) # 左侧弹簧
        content_layout.addLayout(col_original["layout"])
        content_layout.addLayout(col_process)
        content_layout.addLayout(col_result["layout"])
        content_layout.addLayout(col_composite_logic)
        content_layout.addLayout(col_composite["layout"])
        content_layout.addStretch(1) # 右侧弹簧

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
        self.combo_model.addItems(["DeepLabV3+", "U-Net", "FCN"])
        self.combo_model.setFixedWidth(120)
        
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
        layout.addWidget(self.btn_run)
        layout.addStretch()
        
        return layout

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
            pixmap = QPixmap(file_name)
            self.lbl_original.setPixmap(pixmap.scaled(self.lbl_original.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_original.setStyleSheet("border: 2px solid #0984e3; border-radius: 10px;") # 选中后边框变蓝
            
            # 激活分割按钮
            self.btn_run.setEnabled(True)
            # 重置后续步骤
            self.lbl_result.clear()
            self.lbl_result.setText("等待处理...")
            self.btn_bg.setEnabled(False)

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

            # 4. 模型推理
            # 返回的是 (H, W) 的掩码，0是背景，255是人像
            mask = self.model.predict(image_rgb)

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
            self.btn_save_result.setEnabled(True)
            self.btn_bg.setEnabled(True)

        except Exception as e:
            print(f"分割出错: {e}")
            self.lbl_result.setText(f"出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def select_background(self):
        """选择背景图并合成"""
        if self.result_rgba is None:
            return

        file_name, _ = QFileDialog.getOpenFileName(self, "选择背景图", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            # 1. 读取背景图
            bg_stream = np.fromfile(file_name, dtype=np.uint8)
            bg_bgr = cv2.imdecode(bg_stream, cv2.IMREAD_COLOR)
            bg_rgb = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2RGB)

            # 2. 调整背景图大小以适应前景 (或者反过来，这里选择调整背景适应前景)
            h, w, _ = self.result_rgba.shape
            bg_resized = cv2.resize(bg_rgb, (w, h))

            # 3. 合成逻辑
            # 公式: result = foreground * alpha + background * (1 - alpha)
            alpha = self.result_rgba[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2) # (H, W, 1)
            
            foreground = self.result_rgba[:, :, :3]
            
            composite = (foreground * alpha + bg_resized * (1.0 - alpha)).astype(np.uint8)
            
            # 4. 显示合成结果
            qimg = QImage(composite.data, w, h, w * 3, QImage.Format.Format_RGB888)
            self.lbl_composite.setPixmap(QPixmap.fromImage(qimg).scaled(self.lbl_composite.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_composite.setStyleSheet("border: 2px solid #6c5ce7; border-radius: 10px;")
            
            self.btn_save_composite.setEnabled(True)
            # 保存合成数据用于文件保存
            self.composite_rgb = composite

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