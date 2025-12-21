from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QRegion

class CropOverlay(QWidget):
    crop_changed = pyqtSignal(QRectF) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        
        # 归一化坐标 (0.0 - 1.0)
        self.norm_rect = QRectF(0.0, 0.0, 1.0, 1.0) 
        self.image_rect = QRectF()
        
        self.dragging = False
        self.drag_mode = None 
        self.last_pos = QPointF()
        self.aspect_ratio = None 

    def set_image_rect(self, rect):
        if rect is None or rect.isEmpty():
            self.image_rect = QRectF()
            self.hide()
            return
        self.image_rect = rect
        self.show()
        self.update()

    def reset_crop(self):
        """重置为全图"""
        self.norm_rect = QRectF(0.0, 0.0, 1.0, 1.0)
        self.aspect_ratio = None
        self.crop_changed.emit(self.norm_rect)
        self.update()

    def set_aspect_ratio(self, ratio):
        """设置比例并计算最大居中矩形"""
        self.aspect_ratio = ratio
        
        if self.image_rect.isEmpty(): return

        if ratio is None:
            # 自由模式，不改变当前框，只解除限制
            pass
        else:
            # 计算基于当前图片尺寸的最大居中矩形
            img_w = self.image_rect.width()
            img_h = self.image_rect.height()
            
            if img_w == 0 or img_h == 0: return

            # 目标宽高
            target_w = img_w
            target_h = target_w / ratio
            
            if target_h > img_h:
                target_h = img_h
                target_w = target_h * ratio
            
            # 转换为归一化坐标
            norm_w = target_w / img_w
            norm_h = target_h / img_h
            
            # 居中
            norm_x = (1.0 - norm_w) / 2.0
            norm_y = (1.0 - norm_h) / 2.0
            
            self.norm_rect = QRectF(norm_x, norm_y, norm_w, norm_h)
            self.crop_changed.emit(self.norm_rect)
            
        self.update()

    def _fix_aspect_ratio(self):
        """拖拽时维持比例"""
        if self.aspect_ratio is None: return
        if self.image_rect.isEmpty(): return
        
        current_w = self.norm_rect.width() * self.image_rect.width()
        current_h = self.norm_rect.height() * self.image_rect.height()
        
        if current_h == 0: return

        center = self.norm_rect.center()
        
        if current_w / current_h > self.aspect_ratio:
            new_w = current_h * self.aspect_ratio
            new_h = current_h
        else:
            new_w = current_w
            new_h = current_w / self.aspect_ratio
            
        norm_w = new_w / self.image_rect.width()
        norm_h = new_h / self.image_rect.height()
        
        self.norm_rect = QRectF(center.x() - norm_w/2, center.y() - norm_h/2, norm_w, norm_h)
        self._constrain_rect()

    def _constrain_rect(self):
        r = self.norm_rect
        if r.left() < 0: r.moveLeft(0)
        if r.top() < 0: r.moveTop(0)
        if r.right() > 1: r.moveRight(1)
        if r.bottom() > 1: r.moveBottom(1)
        self.norm_rect = r
        self.crop_changed.emit(self.norm_rect)

    def get_pixel_rect(self):
        if self.image_rect.isEmpty(): return QRectF()
        x = self.image_rect.x() + self.norm_rect.x() * self.image_rect.width()
        y = self.image_rect.y() + self.norm_rect.y() * self.image_rect.height()
        w = self.norm_rect.width() * self.image_rect.width()
        h = self.norm_rect.height() * self.image_rect.height()
        return QRectF(x, y, w, h)

    def paintEvent(self, event):
        if self.image_rect.isEmpty(): return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        full_rect = self.rect()
        crop_pixel_rect = self.get_pixel_rect()
        
        # 遮罩
        bg_region = QRegion(full_rect)
        crop_region = QRegion(crop_pixel_rect.toRect())
        mask_region = bg_region.subtracted(crop_region)
        
        painter.setClipRegion(mask_region)
        painter.fillRect(full_rect, QColor(0, 0, 0, 180))
        painter.setClipRect(full_rect) 

        # 边框
        pen = QPen(QColor(255, 255, 255), 1)
        painter.setPen(pen)
        painter.drawRect(crop_pixel_rect)

        # 九宫格
        pen_grid = QPen(QColor(255, 255, 255, 80), 1)
        painter.setPen(pen_grid)
        x, y, w, h = crop_pixel_rect.x(), crop_pixel_rect.y(), crop_pixel_rect.width(), crop_pixel_rect.height()
        
        painter.drawLine(QPointF(x + w/3, y), QPointF(x + w/3, y + h))
        painter.drawLine(QPointF(x + 2*w/3, y), QPointF(x + 2*w/3, y + h))
        painter.drawLine(QPointF(x, y + h/3), QPointF(x + w, y + h/3))
        painter.drawLine(QPointF(x, y + 2*h/3), QPointF(x + w, y + 2*h/3))

        # 角落手柄
        pen_corner = QPen(QColor(255, 255, 255), 3)
        painter.setPen(pen_corner)
        cl = 20 
        
        painter.drawLine(QPointF(x, y), QPointF(x + cl, y))
        painter.drawLine(QPointF(x, y), QPointF(x, y + cl))
        painter.drawLine(QPointF(x + w, y), QPointF(x + w - cl, y))
        painter.drawLine(QPointF(x + w, y), QPointF(x + w, y + cl))
        painter.drawLine(QPointF(x, y + h), QPointF(x + cl, y + h))
        painter.drawLine(QPointF(x, y + h), QPointF(x, y + h - cl))
        painter.drawLine(QPointF(x + w, y + h), QPointF(x + w - cl, y + h))
        painter.drawLine(QPointF(x + w, y + h), QPointF(x + w, y + h - cl))
        
        # 边缘手柄
        painter.drawLine(QPointF(x + w/2 - 10, y), QPointF(x + w/2 + 10, y))
        painter.drawLine(QPointF(x + w/2 - 10, y + h), QPointF(x + w/2 + 10, y + h))
        painter.drawLine(QPointF(x, y + h/2 - 10), QPointF(x, y + h/2 + 10))
        painter.drawLine(QPointF(x + w, y + h/2 - 10), QPointF(x + w, y + h/2 + 10))

    def mousePressEvent(self, event):
        if self.image_rect.isEmpty(): return
        pos = event.position()
        rect = self.get_pixel_rect()
        margin = 30
        
        if rect.contains(pos) or rect.adjusted(-margin, -margin, margin, margin).contains(pos):
            self.dragging = True
            self.last_pos = pos
            
            l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
            x, y = pos.x(), pos.y()
            
            if abs(x - l) < margin and abs(y - t) < margin: self.drag_mode = 'tl'
            elif abs(x - r) < margin and abs(y - t) < margin: self.drag_mode = 'tr'
            elif abs(x - l) < margin and abs(y - b) < margin: self.drag_mode = 'bl'
            elif abs(x - r) < margin and abs(y - b) < margin: self.drag_mode = 'br'
            elif abs(x - l) < margin: self.drag_mode = 'l'
            elif abs(x - r) < margin: self.drag_mode = 'r'
            elif abs(y - t) < margin: self.drag_mode = 't'
            elif abs(y - b) < margin: self.drag_mode = 'b'
            elif rect.contains(pos): self.drag_mode = 'center'
            else: self.dragging = False

    def mouseMoveEvent(self, event):
        if not self.dragging or self.image_rect.isEmpty(): return
        
        pos = event.position()
        dx = (pos.x() - self.last_pos.x()) / self.image_rect.width()
        dy = (pos.y() - self.last_pos.y()) / self.image_rect.height()
        
        r = self.norm_rect
        l, t, w, h = r.x(), r.y(), r.width(), r.height()
        
        if self.drag_mode == 'center':
            r.translate(dx, dy)
        else:
            if 'l' in self.drag_mode: l += dx; w -= dx
            if 'r' in self.drag_mode: w += dx
            if 't' in self.drag_mode: t += dy; h -= dy
            if 'b' in self.drag_mode: h += dy
            
            if w < 0.05: w = 0.05
            if h < 0.05: h = 0.05
            
            r.setRect(l, t, w, h)
            if self.aspect_ratio: self._fix_aspect_ratio()

        self.norm_rect = r
        self._constrain_rect()
        self.last_pos = pos
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.drag_mode = None