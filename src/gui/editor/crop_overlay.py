from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QRegion

class CropOverlay(QWidget):
    """
    覆盖在 Canvas 上的裁剪框控件
    """
    crop_changed = pyqtSignal(QRectF) # 发送归一化的裁剪区域 (0-1)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 允许鼠标事件穿透到自身，但不穿透到下面的 Canvas (除非在裁剪框外)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        
        # 归一化坐标 (0.0 - 1.0)，相对于显示的图片区域
        self.norm_rect = QRectF(0.1, 0.1, 0.8, 0.8) # 默认给一点边距
        
        # 实际显示的图片区域 (由 Canvas 设置)
        self.image_rect = QRectF()
        
        # 交互状态
        self.dragging = False
        self.drag_mode = None 
        self.last_pos = QPointF()
        self.aspect_ratio = None 

        self.handle_size = 30 # 增大触控区域
        self.corner_line_len = 20

    def set_image_rect(self, rect):
        """设置图片在控件中的实际显示区域"""
        if rect is None or rect.isEmpty():
            self.image_rect = QRectF()
            self.hide()
            return
        
        self.image_rect = rect
        self.show()
        self.update()

    def set_aspect_ratio(self, ratio):
        """设置宽高比 (float), None 为自由"""
        self.aspect_ratio = ratio
        self._fix_aspect_ratio()
        self.update()

    def _fix_aspect_ratio(self):
        # 修复 ZeroDivisionError：如果图片区域无效，直接返回
        if self.aspect_ratio is None: return
        if self.image_rect.isEmpty() or self.image_rect.height() == 0: return
        
        # 获取当前像素坐标
        current_w = self.norm_rect.width() * self.image_rect.width()
        current_h = self.norm_rect.height() * self.image_rect.height()
        
        if current_h == 0: return # 双重保险

        center = self.norm_rect.center()
        
        # 保持面积近似，调整宽高
        if current_w / current_h > self.aspect_ratio:
            # 太宽，缩减宽度
            new_w = current_h * self.aspect_ratio
            new_h = current_h
        else:
            # 太高，缩减高度
            new_w = current_w
            new_h = current_w / self.aspect_ratio
            
        # 转回归一化
        norm_w = new_w / self.image_rect.width()
        norm_h = new_h / self.image_rect.height()
        
        self.norm_rect = QRectF(center.x() - norm_w/2, center.y() - norm_h/2, norm_w, norm_h)
        self._constrain_rect()

    def _constrain_rect(self):
        """限制裁剪框在图片范围内"""
        r = self.norm_rect
        if r.left() < 0: r.moveLeft(0)
        if r.top() < 0: r.moveTop(0)
        if r.right() > 1: r.moveRight(1)
        if r.bottom() > 1: r.moveBottom(1)
        self.norm_rect = r
        self.crop_changed.emit(self.norm_rect)

    def get_pixel_rect(self):
        """获取屏幕像素坐标下的裁剪框"""
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
        
        # 1. 绘制半透明遮罩 (挖空中间)
        bg_region = QRegion(full_rect)
        crop_region = QRegion(crop_pixel_rect.toRect())
        mask_region = bg_region.subtracted(crop_region)
        
        painter.setClipRegion(mask_region)
        painter.fillRect(full_rect, QColor(0, 0, 0, 180)) # 加深背景遮罩
        painter.setClipRect(full_rect) 

        # 2. 绘制裁剪框边框
        pen = QPen(QColor(255, 255, 255), 1)
        painter.setPen(pen)
        painter.drawRect(crop_pixel_rect)

        # 3. 绘制九宫格线
        pen_grid = QPen(QColor(255, 255, 255, 80), 1)
        painter.setPen(pen_grid)
        x, y, w, h = crop_pixel_rect.x(), crop_pixel_rect.y(), crop_pixel_rect.width(), crop_pixel_rect.height()
        
        painter.drawLine(QPointF(x + w/3, y), QPointF(x + w/3, y + h))
        painter.drawLine(QPointF(x + 2*w/3, y), QPointF(x + 2*w/3, y + h))
        painter.drawLine(QPointF(x, y + h/3), QPointF(x + w, y + h/3))
        painter.drawLine(QPointF(x, y + 2*h/3), QPointF(x + w, y + 2*h/3))

        # 4. 绘制四个角 (加粗L型)
        pen_corner = QPen(QColor(255, 255, 255), 3)
        painter.setPen(pen_corner)
        cl = 20 
        
        # 左上
        painter.drawLine(QPointF(x, y), QPointF(x + cl, y))
        painter.drawLine(QPointF(x, y), QPointF(x, y + cl))
        # 右上
        painter.drawLine(QPointF(x + w, y), QPointF(x + w - cl, y))
        painter.drawLine(QPointF(x + w, y), QPointF(x + w, y + cl))
        # 左下
        painter.drawLine(QPointF(x, y + h), QPointF(x + cl, y + h))
        painter.drawLine(QPointF(x, y + h), QPointF(x, y + h - cl))
        # 右下
        painter.drawLine(QPointF(x + w, y + h), QPointF(x + w - cl, y + h))
        painter.drawLine(QPointF(x + w, y + h), QPointF(x + w, y + h - cl))
        
        # 5. 绘制四边中间的短横线 (提示可以拖动)
        painter.drawLine(QPointF(x + w/2 - 10, y), QPointF(x + w/2 + 10, y)) # 上
        painter.drawLine(QPointF(x + w/2 - 10, y + h), QPointF(x + w/2 + 10, y + h)) # 下
        painter.drawLine(QPointF(x, y + h/2 - 10), QPointF(x, y + h/2 + 10)) # 左
        painter.drawLine(QPointF(x + w, y + h/2 - 10), QPointF(x + w, y + h/2 + 10)) # 右

    def mousePressEvent(self, event):
        if self.image_rect.isEmpty(): return
        pos = event.position()
        rect = self.get_pixel_rect()
        margin = 30 # 增大判定范围
        
        if rect.contains(pos) or rect.adjusted(-margin, -margin, margin, margin).contains(pos):
            self.dragging = True
            self.last_pos = pos
            
            l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
            x, y = pos.x(), pos.y()
            
            # 优先判定角
            if abs(x - l) < margin and abs(y - t) < margin: self.drag_mode = 'tl'
            elif abs(x - r) < margin and abs(y - t) < margin: self.drag_mode = 'tr'
            elif abs(x - l) < margin and abs(y - b) < margin: self.drag_mode = 'bl'
            elif abs(x - r) < margin and abs(y - b) < margin: self.drag_mode = 'br'
            # 判定边
            elif abs(x - l) < margin: self.drag_mode = 'l'
            elif abs(x - r) < margin: self.drag_mode = 'r'
            elif abs(y - t) < margin: self.drag_mode = 't'
            elif abs(y - b) < margin: self.drag_mode = 'b'
            # 判定中心
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