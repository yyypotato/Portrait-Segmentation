import sys
import cv2
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from src.models.factory import ModelFactory

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Portrait Segmentation System")
        self.setGeometry(100, 100, 1000, 600)
        
        self.current_image = None
        self.model = None
        
        self.init_ui()
        
    def init_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Control Panel
        control_panel = QVBoxLayout()
        
        # Model Selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(["U-Net", "FCN"])
        control_panel.addWidget(QLabel("Select Model:"))
        control_panel.addWidget(self.model_combo)
        
        # Buttons
        self.btn_load = QPushButton("Load Image")
        self.btn_load.clicked.connect(self.load_image)
        control_panel.addWidget(self.btn_load)
        
        self.btn_segment = QPushButton("Segment")
        self.btn_segment.clicked.connect(self.run_segmentation)
        control_panel.addWidget(self.btn_segment)
        
        control_panel.addStretch()
        main_layout.addLayout(control_panel, 1)
        
        # Right Image Display
        image_layout = QHBoxLayout()
        
        self.lbl_input = QLabel("Input Image")
        self.lbl_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_input.setStyleSheet("border: 1px solid gray;")
        
        self.lbl_output = QLabel("Result")
        self.lbl_output.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_output.setStyleSheet("border: 1px solid gray;")
        
        image_layout.addWidget(self.lbl_input)
        image_layout.addWidget(self.lbl_output)
        
        main_layout.addLayout(image_layout, 4)

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.current_image = cv2.imread(file_name)
            if self.current_image is not None:
                # Convert BGR to RGB for display
                rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                self.display_image(rgb_image, self.lbl_input)
            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def run_segmentation(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Warning", "Please load an image first.")
            return
            
        model_name = self.model_combo.currentText()
        try:
            # Instantiate model (in a real app, load weights once or async)
            self.model = ModelFactory.get_model(model_name)
            
            # Run inference
            # Note: In a real app, run this in a separate thread to avoid freezing UI
            mask = self.model.predict(self.current_image)
            
            # Visualize result (dummy visualization for now)
            # Here we just show a placeholder since predict returns zeros in our skeleton
            self.lbl_output.setText(f"Segmented with {model_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def display_image(self, img_array, label_widget):
        h, w, ch = img_array.shape
        bytes_per_line = ch * w
        q_img = QImage(img_array.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        label_widget.setPixmap(pixmap.scaled(label_widget.size(), Qt.AspectRatioMode.KeepAspectRatio))
