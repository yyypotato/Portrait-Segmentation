from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap, QTransform
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPointF
import math
import os

class StickerItem:
    def __init__(self, image_path, center_pos, size=150):
        self.pixmap = QPixmap(image_path)
        # 计算宽高比
        if self.pixmap.height() > 0:
            self.ratio = self.pixmap.width() / self.pixmap.height()
        else:
            self.ratio = 1.0
            
        self.width = size
        self.height = size / self.ratio
        
        # 中心点坐标
        self.x = center_pos.x()
        self.y = center_pos.y()
        
        self.angle = 0.0 # 旋转角度
        self.is_selected = True

    @property
    def rect(self):
        # 返回局部坐标系下的矩形 (中心为 0,0)
        return QRectF(-self.width/2, -self.height/2, self.width, self.height)

class StickerOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 允许接收鼠标事件
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        self.items = []
        self.selected_item = None
        
        # 交互状态
        self._mode = None # 'move', 'rotate_scale'
        self._last_pos = QPointF()
        
        # 加载 UI 图标
        self.icon_delete = QPixmap(os.path.join("resources", "icons", "delete_x.png"))
        if self.icon_delete.isNull():
            self.icon_delete = QPixmap(24, 24)
            self.icon_delete.fill(Qt.GlobalColor.red)
            
        self.icon_resize = QPixmap(os.path.join("resources", "icons", "resize_handle.png"))
        if self.icon_resize.isNull():
            self.icon_resize = QPixmap(24, 24)
            self.icon_resize.fill(Qt.GlobalColor.blue)

    def set_image_rect(self, rect):
        if isinstance(rect, QRectF):
            self.setGeometry(rect.toRect())
        else:
            self.setGeometry(rect)

    def add_sticker(self, path):
        # 添加到视图中心
        center = QPointF(self.width()/2, self.height()/2)
        item = StickerItem(path, center)
        self.items.append(item)
        self.selected_item = item
        self.update()

    def clear(self):
        self.items = []
        self.selected_item = None
        self.update()

    def get_result_image(self, bg_size):
        """生成透明背景的贴纸层图片"""
        # Format_ARGB32_Premultiplied 在 Windows (Little Endian) 上内存顺序通常是 B G R A
        img = QImage(bg_size, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        for item in self.items:
            painter.save()
            painter.translate(item.x, item.y)
            painter.rotate(item.angle)
            painter.drawPixmap(item.rect.toRect(), item.pixmap)
            painter.restore()
            
        painter.end()
        return img

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        for item in self.items:
            painter.save()
            painter.translate(item.x, item.y)
            painter.rotate(item.angle)
            
            # 绘制贴纸图片
            painter.drawPixmap(item.rect.toRect(), item.pixmap)
            
            # 如果被选中，绘制边框和手柄
            if item == self.selected_item:
                # 1. 边框
                pen = QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine) # 实线白框
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(item.rect)
                
                # 2. 手柄 (在局部坐标系中绘制)
                icon_sz = 24
                half_sz = icon_sz / 2
                
                # 左上角：删除
                painter.drawPixmap(int(-item.width/2 - half_sz), int(-item.height/2 - half_sz), 
                                 icon_sz, icon_sz, self.icon_delete)
                
                # 右下角：旋转/缩放
                painter.drawPixmap(int(item.width/2 - half_sz), int(item.height/2 - half_sz), 
                                 icon_sz, icon_sz, self.icon_resize)
                
            painter.restore()

    def mousePressEvent(self, event):
        pos = event.position() # QPointF
        
        # 1. 优先检查选中项的手柄
        if self.selected_item:
            item = self.selected_item
            local_pos = self._map_to_local(item, pos)
            
            # 检查删除按钮 (左上角)
            tl = QPointF(-item.width/2, -item.height/2)
            if (local_pos - tl).manhattanLength() < 25: 
                self.items.remove(item)
                self.selected_item = None
                self.update()
                return
                
            # 检查缩放/旋转按钮 (右下角)
            br = QPointF(item.width/2, item.height/2)
            if (local_pos - br).manhattanLength() < 25:
                self._mode = 'rotate_scale'
                self._last_pos = pos
                return

        # 2. 检查是否点击了贴纸本体 (倒序遍历)
        clicked_item = None
        for item in reversed(self.items):
            local_pos = self._map_to_local(item, pos)
            if item.rect.contains(local_pos):
                clicked_item = item
                break
        
        if clicked_item:
            self.selected_item = clicked_item
            # 移到最上层
            self.items.remove(clicked_item)
            self.items.append(clicked_item)
            
            self._mode = 'move'
            self._last_pos = pos
        else:
            self.selected_item = None
            
        self.update()

    def mouseMoveEvent(self, event):
        if not self.selected_item or not self._mode: return
        
        pos = event.position()
        item = self.selected_item
        
        if self._mode == 'move':
            delta = pos - self._last_pos
            item.x += delta.x()
            item.y += delta.y()
            self._last_pos = pos
            
        elif self._mode == 'rotate_scale':
            # 计算相对于中心的向量
            dx = pos.x() - item.x
            dy = pos.y() - item.y
            
            # 1. 旋转
            angle = math.degrees(math.atan2(dy, dx))
            # 修正角度：假设手柄在右下角
            base_angle = math.degrees(math.atan2(item.height, item.width))
            item.angle = angle - base_angle
            
            # 2. 缩放
            dist = math.sqrt(dx*dx + dy*dy)
            diag = dist * 2
            new_w = diag / math.sqrt(1 + 1/(item.ratio**2))
            
            item.width = max(30, new_w)
            item.height = item.width / item.ratio
            
        self.update()

    def mouseReleaseEvent(self, event):
        self._mode = None

    def _map_to_local(self, item, global_pos):
        """将全局坐标映射到贴纸的局部坐标系"""
        t = QTransform()
        t.translate(item.x, item.y)
        t.rotate(item.angle)
        inv, success = t.inverted()
        if success:
            return inv.map(global_pos)
        return QPointF(0, 0)