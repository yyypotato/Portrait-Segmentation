from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QPen, QColor

class InteractiveLabel(QLabel):
    """
    支持鼠标框选的 Label，用于局部虚化功能
    """
    selection_made = pyqtSignal(QRect) # 信号：选区完成

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.current_rect = QRect()
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.is_drawing = True
            self.current_rect = QRect()

    def mouseMoveEvent(self, event):
        if self.is_drawing and self.start_point:
            self.end_point = event.pos()
            self.current_rect = QRect(self.start_point, self.end_point).normalized()
            self.update() # 触发 paintEvent 重绘矩形框

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            if self.current_rect.isValid() and self.current_rect.width() > 5 and self.current_rect.height() > 5:
                # 发送选区信号
                self.selection_made.emit(self.current_rect)
            self.current_rect = QRect() # 清空选框
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event) # 绘制原本的图片
        if self.is_drawing and self.current_rect.isValid():
            painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.current_rect)