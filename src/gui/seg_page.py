from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from .styles import Styles

class SegPage(QWidget):
    go_back = pyqtSignal() # 返回菜单信号

    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- 顶部导航栏 ---
        nav_bar = QHBoxLayout()
        btn_back = QPushButton("← 返回菜单")
        btn_back.setFixedWidth(100)
        btn_back.setStyleSheet(Styles.BUTTON_STYLE)
        btn_back.clicked.connect(self.go_back.emit)
        
        title = QLabel("工作台")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        
        nav_bar.addWidget(btn_back)
        nav_bar.addStretch()
        nav_bar.addWidget(title)
        nav_bar.addStretch()
        nav_bar.addWidget(QLabel("   ")) # 占位，保持标题居中

        # --- 控制栏 ---
        control_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("📂 选择图片")
        self.btn_load.setStyleSheet(Styles.BUTTON_STYLE)
        self.btn_load.clicked.connect(self.load_image)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(["U-Net", "FCN", "DeepLabV3+"])
        self.combo_model.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
        
        self.btn_run = QPushButton("▶ 开始分割")
        self.btn_run.setStyleSheet(Styles.BUTTON_STYLE)
        self.btn_run.clicked.connect(self.run_segmentation)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(Styles.BUTTON_STYLE + "background-color: #636e72;") # 禁用态颜色

        control_layout.addWidget(self.btn_load)
        control_layout.addWidget(QLabel("模型:"))
        control_layout.addWidget(self.combo_model)
        control_layout.addWidget(self.btn_run)
        control_layout.addStretch()

        # --- 图像显示区 ---
        image_layout = QHBoxLayout()
        self.lbl_original = self.create_image_box("原图")
        self.lbl_result = self.create_image_box("结果")
        image_layout.addWidget(self.lbl_original)
        image_layout.addWidget(self.lbl_result)

        # 组装
        main_layout.addLayout(nav_bar)
        main_layout.addSpacing(10)
        main_layout.addLayout(control_layout)
        main_layout.addLayout(image_layout)

    def create_image_box(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: 2px dashed #b2bec3; background-color: #dfe6e9; color: #636e72; font-size: 16px;")
        lbl.setMinimumSize(300, 300)
        return lbl

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.current_image_path = file_name
            pixmap = QPixmap(file_name)
            self.lbl_original.setPixmap(pixmap.scaled(self.lbl_original.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.btn_run.setEnabled(True)
            self.btn_run.setStyleSheet(Styles.BUTTON_STYLE + "background-color: #00b894;") # 激活态颜色

    def run_segmentation(self):
        # 纯 UI 模拟，不调用模型
        if self.current_image_path:
            self.lbl_result.setText("正在处理...")
            # 模拟：简单显示原图的灰度版
            pix = QPixmap(self.current_image_path)
            img = pix.toImage().convertToFormat(QImage.Format.Format_Grayscale8)
            self.lbl_result.setPixmap(QPixmap.fromImage(img).scaled(self.lbl_result.size(), Qt.AspectRatioMode.KeepAspectRatio))