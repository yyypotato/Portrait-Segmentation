from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class ToolButton(QPushButton):
    """底部功能按钮 (图标+文字)"""
    def __init__(self, text, icon_emoji, parent=None):
        super().__init__(parent)
        self.setText(f"{icon_emoji}\n{text}")
        self.setCheckable(True)
        self.setFixedSize(70, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #b2bec3;
                border: none;
                font-size: 12px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:checked {
                background: #2d3436;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)

class SliderControl(QWidget):
    """带数值显示的滑块组件"""
    value_changed = pyqtSignal(int)

    def __init__(self, name, min_v=-100, max_v=100, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 标题栏 (名称 + 数值)
        top_layout = QVBoxLayout()
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("color: #dfe6e9; font-weight: bold;")
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet("color: #00b894; font-weight: bold;")
        self.lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 滑块
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_v, max_v)
        self.slider.setValue(0)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #636e72;
                height: 4px;
                background: #2d3436;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #b2bec3;
                width: 16px;
                height: 16px;
                margin: -7px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00b894;
                border-radius: 2px;
            }
        """)
        self.slider.valueChanged.connect(self._on_change)

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.slider)
        layout.addWidget(self.lbl_val)
        layout.setAlignment(self.lbl_val, Qt.AlignmentFlag.AlignRight)

    def _on_change(self, val):
        self.lbl_val.setText(str(val))
        self.value_changed.emit(val)

    def set_value(self, val):
        self.slider.setValue(val)