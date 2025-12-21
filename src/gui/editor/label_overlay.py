from PyQt6.QtWidgets import QWidget, QInputDialog, QLineEdit
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPixmap, QFont, QTransform, QFontMetrics
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QSize
import math
import os

class LabelItem:
    """单个标签的数据结构"""
    def __init__(self, image_path, center_pos):
        self.image_path = image_path
        self.pixmap = QPixmap(image_path)
        # 默认大小
        self.width = 150
        self.height = 100
        self.x = center_pos.x() - self.width / 2
        self.y = center_pos.y() - self.height / 2
        self.angle = 0 # 旋转角度
        
        self.text = "点击编辑文字"
        self.font = QFont("Arial", 12)
        self.text_color = QColor(0, 0, 0)
        self.is_bold = False
        self.is_italic = False
        self.has_shadow = False
        
        self.is_selected = True

    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    def contains(self, point):
        # 简单的矩形碰撞检测 (未考虑旋转的精确碰撞，简化处理)
        # 更好的做法是将点逆旋转后检测
        center = QPointF(self.x + self.width/2, self.y + self.height/2)
        trans = QTransform()
        trans.translate(center.x(), center.y())
        trans.rotate(-self.angle)
        trans.translate(-center.x(), -center.y())
        mapped_point = trans.map(QPointF(point))
        return self.get_rect().contains(mapped_point)

class LabelOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
        self.items = []
        self.selected_item = None
        self.image_rect = QRect()
        
        # 交互状态
        self.mode = None # 'move', 'resize', 'rotate'
        self.last_pos = QPoint()
        
        # --- 修复部分：安全加载图标 ---
        delete_path = os.path.join("resources", "icons", "delete_x.png")
        resize_path = os.path.join("resources", "icons", "resize_handle.png")
        
        # 加载删除图标，如果失败则创建红色方块
        self.icon_delete = QPixmap(delete_path)
        if self.icon_delete.isNull():
            self.icon_delete = QPixmap(20, 20)
            self.icon_delete.fill(Qt.GlobalColor.red)
        else:
            self.icon_delete = self.icon_delete.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # 加载缩放图标，如果失败则创建蓝色方块
        self.icon_resize = QPixmap(resize_path)
        if self.icon_resize.isNull():
            self.icon_resize = QPixmap(20, 20)
            self.icon_resize.fill(Qt.GlobalColor.blue)
        else:
            self.icon_resize = self.icon_resize.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # ---------------------------

    def set_image_rect(self, rect):
        self.image_rect = rect
        # --- 修复部分：类型转换 ---
        # setGeometry 需要 QRect (整数)，如果传入的是 QRectF (浮点数) 需要转换
        if isinstance(rect, QRectF):
            self.setGeometry(rect.toRect())
        else:
            self.setGeometry(rect)
        # -----------------------

    def add_label(self, image_path):
        center = QPoint(self.width() // 2, self.height() // 2)
        item = LabelItem(image_path, center)
        self.items.append(item)
        self.select_item(item)
        self.update()

    def select_item(self, item):
        for i in self.items: i.is_selected = False
        if item: item.is_selected = True
        self.selected_item = item
        self.update()

    def delete_selected(self):
        if self.selected_item and self.selected_item in self.items:
            self.items.remove(self.selected_item)
            self.selected_item = None
            self.update()

    def get_result_image(self, bg_size):
        """生成透明背景的标签层图片，用于合并"""
        img = QImage(bg_size, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # 绘制所有标签 (不画边框和手柄)
        for item in self.items:
            self.draw_item(painter, item, draw_handles=False)
            
        painter.end()
        return img

    def draw_item(self, painter, item, draw_handles=True):
        painter.save()
        
        # 变换坐标系到 item 中心
        cx = item.x + item.width / 2
        cy = item.y + item.height / 2
        painter.translate(cx, cy)
        painter.rotate(item.angle)
        painter.translate(-cx, -cy)
        
        # 1. 绘制背景图
        target_rect = QRectF(item.x, item.y, item.width, item.height)
        painter.drawPixmap(target_rect.toRect(), item.pixmap)
        
        # 2. 绘制文字
        painter.setFont(item.font)
        pen = QPen(item.text_color)
        if item.has_shadow:
            # 简单的阴影效果
            shadow_pen = QPen(QColor(0,0,0, 100))
            painter.setPen(shadow_pen)
            painter.drawText(target_rect.translated(2, 2), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, item.text)
        
        painter.setPen(pen)
        painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, item.text)
        
        # 3. 绘制选中框和手柄
        if item.is_selected and draw_handles:
            pen = QPen(QColor("#0984e3"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(target_rect)
            
            # 左上角删除
            painter.drawPixmap(int(item.x - 10), int(item.y - 10), self.icon_delete)
            # 右下角缩放
            painter.drawPixmap(int(item.x + item.width - 10), int(item.y + item.height - 10), self.icon_resize)
            
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        for item in self.items:
            self.draw_item(painter, item, draw_handles=True)

    def mousePressEvent(self, event):
        pos = event.pos()
        
        # 1. 检查选中项的手柄
        if self.selected_item:
            item = self.selected_item
            # 转换坐标系检测手柄
            # 简化：假设未旋转检测手柄区域 (实际应逆变换)
            # 删除按钮 (左上)
            del_rect = QRectF(item.x - 15, item.y - 15, 30, 30)
            if del_rect.contains(QPointF(pos)):
                self.delete_selected()
                return
                
            # 缩放按钮 (右下)
            resize_rect = QRectF(item.x + item.width - 15, item.y + item.height - 15, 30, 30)
            if resize_rect.contains(QPointF(pos)):
                self.mode = 'resize'
                self.last_pos = pos
                return
        
        # 2. 检查点击了哪个 Item
        clicked_item = None
        # 倒序遍历，优先选中上层的
        for i in range(len(self.items)-1, -1, -1):
            if self.items[i].contains(pos):
                clicked_item = self.items[i]
                break
        
        if clicked_item:
            self.select_item(clicked_item)
            self.mode = 'move'
            self.last_pos = pos
        else:
            self.select_item(None)

    def mouseMoveEvent(self, event):
        if not self.selected_item or not self.mode: return
        
        pos = event.pos()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        
        item = self.selected_item
        
        if self.mode == 'move':
            item.x += dx
            item.y += dy
            
        elif self.mode == 'resize':
            # 简单的缩放逻辑
            new_w = max(50, item.width + dx)
            new_h = max(50, item.height + dy)
            item.width = new_w
            item.height = new_h
            
        self.last_pos = pos
        self.update()

    def mouseReleaseEvent(self, event):
        self.mode = None

    def mouseDoubleClickEvent(self, event):
        if self.selected_item:
            text, ok = QInputDialog.getText(self, "编辑文字", "请输入标签文字:", text=self.selected_item.text)
            if ok:
                self.selected_item.text = text
                self.update()

    # --- 样式设置接口 ---
    def set_current_font_bold(self, is_bold):
        if self.selected_item:
            self.selected_item.font.setBold(is_bold)
            self.selected_item.is_bold = is_bold
            self.update()

    def set_current_font_italic(self, is_italic):
        if self.selected_item:
            self.selected_item.font.setItalic(is_italic)
            self.selected_item.is_italic = is_italic
            self.update()
            
    def set_current_shadow(self, has_shadow):
        if self.selected_item:
            self.selected_item.has_shadow = has_shadow
            self.update()

    def set_current_color(self, color):
        if self.selected_item:
            self.selected_item.text_color = color
            self.update()
            
    def set_current_font_size(self, size):
        if self.selected_item:
            self.selected_item.font.setPointSize(size)
            self.update()