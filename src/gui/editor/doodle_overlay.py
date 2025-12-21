from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QPainterPath, QBrush
import math

class DoodleOverlay(QWidget):
    """
    涂鸦覆盖层
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        
        self.image_rect = QRectF() # 图片在屏幕上的实际区域
        self.drawing_layer = QPixmap() # 存储已完成的笔画
        self.drawing_layer.fill(Qt.GlobalColor.transparent)
        
        # 状态
        self.is_drawing = False
        self.start_pos = QPointF()
        self.current_pos = QPointF()
        
        # 工具设置
        self.tool_type = "curve" # curve, eraser, arrow, line, rect, circle
        self.pen_width = 5
        self.pen_color = QColor(255, 165, 0) # 橙色
        
        # 曲线路径缓存
        self.current_path = QPainterPath()

    def set_image_rect(self, rect):
        """设置绘图区域，并调整画布大小"""
        if rect.isEmpty(): return
        self.image_rect = rect
        
        # 如果画布尺寸变了，需要重新调整 drawing_layer
        # 这里简化处理：每次进入涂鸦模式建议重置，或者保存历史
        if self.drawing_layer.size() != rect.size().toSize():
            new_layer = QPixmap(rect.size().toSize())
            new_layer.fill(Qt.GlobalColor.transparent)
            # 如果需要保留之前的涂鸦，这里需要做缩放迁移，暂略
            self.drawing_layer = new_layer
            
        self.setGeometry(rect.toRect()) # 覆盖层直接对齐图片区域
        self.show()
        self.update()

    def clear_canvas(self):
        """清空画布"""
        self.drawing_layer.fill(Qt.GlobalColor.transparent)
        self.update()

    def get_result(self):
        """获取最终的涂鸦图层 (QPixmap)"""
        return self.drawing_layer

    def set_tool(self, tool_name):
        self.tool_type = tool_name

    def set_width(self, width):
        self.pen_width = width

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制已完成的图层
        painter.drawPixmap(0, 0, self.drawing_layer)
        
        # 2. 绘制正在进行的笔画
        if self.is_drawing:
            self._draw_shape(painter, is_preview=True)

    def _draw_shape(self, painter, is_preview=False):
        """绘制形状的核心逻辑"""
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        
        if self.tool_type == "eraser":
            # 橡皮擦在预览时显示白色轮廓，实际绘制时使用 Clear 模式
            if is_preview:
                pen.setColor(QColor(255, 255, 255))
                pen.setWidth(self.pen_width)
                painter.setPen(pen)
                painter.drawPath(self.current_path)
            else:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                pen.setWidth(self.pen_width)
                painter.setPen(pen)
                painter.drawPath(self.current_path)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver) # 还原
                
        elif self.tool_type == "curve":
            painter.setPen(pen)
            painter.drawPath(self.current_path)
            
        else:
            # 几何图形 (Line, Arrow, Rect, Circle)
            painter.setPen(pen)
            start = self.start_pos
            end = self.current_pos
            
            if self.tool_type == "line":
                painter.drawLine(start, end)
                
            elif self.tool_type == "rect":
                rect = QRectF(start, end).normalized()
                painter.drawRect(rect)
                
            elif self.tool_type == "circle":
                rect = QRectF(start, end).normalized()
                painter.drawEllipse(rect)
                
            elif self.tool_type == "arrow":
                self._draw_arrow(painter, start, end)

    def _draw_arrow(self, painter, start, end):
        """绘制箭头"""
        painter.drawLine(start, end)
        
        # 计算箭头头部
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        arrow_len = self.pen_width * 3 + 10
        arrow_angle = math.pi / 6 # 30度
        
        p1 = QPointF(end.x() - arrow_len * math.cos(angle - arrow_angle),
                     end.y() - arrow_len * math.sin(angle - arrow_angle))
        p2 = QPointF(end.x() - arrow_len * math.cos(angle + arrow_angle),
                     end.y() - arrow_len * math.sin(angle + arrow_angle))
        
        path = QPainterPath()
        path.moveTo(end)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        
        painter.fillPath(path, QBrush(self.pen_color))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.start_pos = event.position()
            self.current_pos = event.position()
            
            if self.tool_type in ["curve", "eraser"]:
                self.current_path = QPainterPath()
                self.current_path.moveTo(self.start_pos)
            
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.current_pos = event.position()
            
            if self.tool_type in ["curve", "eraser"]:
                self.current_path.lineTo(self.current_pos)
            
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.current_pos = event.position()
            
            # 将当前笔画固化到 drawing_layer
            painter = QPainter(self.drawing_layer)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_shape(painter, is_preview=False)
            painter.end()
            
            self.update()