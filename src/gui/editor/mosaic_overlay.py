from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF

class MosaicOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        self.image_rect = QRect()
        self.brush_size = 20
        self.is_drawing = False
        self.last_point = QPoint()
        
        # mask_image: 记录涂抹区域 (Alpha通道: 255=显示马赛克, 0=不显示)
        self.mask_image = QImage() 
        
        # mosaic_pixmap: 预先生成的全图马赛克效果
        self.mosaic_pixmap = None
        
        # 当前模式: 'draw' 或 'eraser'
        self.mode = 'draw'

    def set_image_rect(self, rect):
        if isinstance(rect, QRectF):
            rect = rect.toRect()
            
        self.image_rect = rect
        self.setGeometry(rect)
        
        # 修复：如果尺寸改变，尝试缩放现有遮罩，而不是直接清空
        # 这样在调整窗口大小时不会丢失已画的内容
        if self.mask_image.size() != rect.size():
            if not self.mask_image.isNull() and not rect.isEmpty():
                self.mask_image = self.mask_image.scaled(
                    rect.size(), 
                    Qt.AspectRatioMode.IgnoreAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                self.mask_image = QImage(rect.size(), QImage.Format.Format_ARGB32_Premultiplied)
                self.mask_image.fill(Qt.GlobalColor.transparent)

    def set_mosaic_pixmap(self, pixmap):
        """设置底层的马赛克效果图"""
        self.mosaic_pixmap = pixmap
        self.update()

    def set_brush_size(self, size):
        self.brush_size = size

    def set_mode(self, mode):
        """ 'draw' or 'eraser' """
        self.mode = mode

    def clear_mask(self):
        if not self.mask_image.isNull():
            self.mask_image.fill(Qt.GlobalColor.transparent)
            self.update()

    def get_mask(self):
        """获取最终的遮罩图 (QImage)"""
        return self.mask_image

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.last_point = event.pos()
            self.draw_line(event.pos())

    def mouseMoveEvent(self, event):
        if self.is_drawing and (event.buttons() & Qt.MouseButton.LeftButton):
            self.draw_line(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False

    def draw_line(self, end_point):
        if self.mask_image.isNull(): return

        painter = QPainter(self.mask_image)
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.mode == 'eraser':
            # 橡皮擦：清除 Alpha 通道
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            pen = QPen(Qt.GlobalColor.transparent, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        else:
            # 涂抹
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            pen = QPen(QColor(255, 0, 0, 255), self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            
        painter.setPen(pen)
        painter.drawLine(self.last_point, end_point)
        painter.end()
        
        self.last_point = end_point
        self.update()

    def paintEvent(self, event):
        if self.mosaic_pixmap is None or self.mask_image.isNull():
            return

        painter = QPainter(self)
        
        # 实时合成显示
        display_img = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        display_img.fill(Qt.GlobalColor.transparent)
        
        p = QPainter(display_img)
        
        # 【关键修复】使用 drawPixmap(rect, pixmap) 进行拉伸绘制
        # 确保马赛克底图完全填充当前控件区域，与底层图片严格对齐
        # 之前是 p.drawPixmap(0, 0, self.mosaic_pixmap)，导致预览时马赛克错位
        p.drawPixmap(self.rect(), self.mosaic_pixmap)
        
        # 使用 DestinationIn 模式绘制遮罩 (保留重叠部分的 Alpha)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        p.drawImage(0, 0, self.mask_image)
        p.end()
        
        painter.drawImage(0, 0, display_img)