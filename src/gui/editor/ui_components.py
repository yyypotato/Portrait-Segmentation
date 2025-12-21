from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QIcon

class IconButton(QPushButton):
    """
    加载本地 PNG 图标的按钮，支持自动着色
    """
    def __init__(self, icon_name, text, parent=None, is_small=False):
        super().__init__(parent)
        self.text_str = text
        self.is_small = is_small
        # 路径指向 resources/icons/
        self.icon_path = f"resources/icons/{icon_name}.png"
        
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if is_small:
            self.setFixedSize(60, 60)
        else:
            self.setFixedSize(70, 70)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. 确定颜色
        if self.isChecked():
            bg_color = QColor("#2d3436")
            content_color = QColor("#0984e3") # 选中蓝
        else:
            bg_color = Qt.GlobalColor.transparent
            content_color = QColor("#b2bec3") # 未选中灰

        # 2. 绘制背景
        if self.isChecked():
            painter.setBrush(bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 10, 10)

        # 3. 绘制并着色图标
        target_size = 28 if not self.is_small else 24
        pixmap = QPixmap(self.icon_path)
        
        if not pixmap.isNull():
            # 创建一个与图标同大小的透明画布用于着色
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.GlobalColor.transparent)
            
            p = QPainter(colored_pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # A. 绘制原始黑色图标
            p.drawPixmap(0, 0, pixmap)
            # B. 设置混合模式为 SourceIn (保留源像素的颜色，但只在目标像素不透明的地方绘制)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            # C. 填充目标颜色
            p.fillRect(colored_pixmap.rect(), content_color)
            p.end()

            # 计算居中位置
            x = (self.width() - target_size) / 2
            y = (self.height() - target_size) / 2 - 8
            
            painter.drawPixmap(int(x), int(y), target_size, target_size, colored_pixmap)

        # 4. 绘制文字
        painter.setPen(content_color)
        font = painter.font()
        font.setPointSize(9 if self.is_small else 10)
        font.setBold(self.isChecked())
        painter.setFont(font)
        
        text_rect = QRectF(0, self.height() - 25, self.width(), 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text_str)

class ModernSlider(QWidget):
    """
    (保持不变) 单个大滑块
    """
    value_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(-100, 100)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #636e72;
                height: 4px;
                background: #636e72;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0984e3;
                border: 2px solid #74b9ff;
                width: 20px;
                height: 20px;
                margin: -9px 0;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #0984e3;
                border-radius: 2px;
            }
        """)
        self.slider.valueChanged.connect(self._on_change)
        
        self.lbl_val = QLabel("0")
        self.lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_val.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        layout.addWidget(self.lbl_val)
        layout.addWidget(self.slider)

    def _on_change(self, val):
        self.lbl_val.setText(str(val))
        self.value_changed.emit(val)

    def set_value(self, val):
        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self.lbl_val.setText(str(val))
        self.slider.blockSignals(False)