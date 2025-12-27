import cv2
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSlider, QFrame, QGraphicsDropShadowEffect, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QSize, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QCursor, QWheelEvent, QMouseEvent, QBrush

class RefineCanvas(QWidget):
    """
    支持缩放、移动、涂抹的画布
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        # 隐藏系统光标，使用自定义笔刷光标
        self.setCursor(Qt.CursorShape.BlankCursor)
        
        # 数据
        self.img_rgb = None
        self.dark_bg = None # 预计算的暗色背景
        self.mask = None
        self.display_image = None # 使用 QImage 作为缓存，方便局部更新
        
        # 交互状态
        self.space_pressed = False
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF()
        self.cursor_pos = QPointF(-100, -100) # 鼠标当前位置(屏幕坐标)
        self.is_panning = False
        
        # 绘图工具状态
        self.is_drawing = False
        self.brush_size = 20
        self.mode = 'restore' # 'restore' (增加/变亮) or 'erase' (擦除/变暗)
        self.last_draw_point = None
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True
            # 按住空格时显示手型
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.update()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False
            if not self.is_panning:
                # 恢复自定义光标
                self.setCursor(Qt.CursorShape.BlankCursor)
            self.update()
        super().keyReleaseEvent(event)

    def set_data(self, img_rgb, mask):
        self.img_rgb = img_rgb
        self.mask = mask.copy()
        
        # 预计算暗色背景 (原图 * 0.3)
        # 这样在涂抹时不需要重复计算背景，大幅提升性能
        self.dark_bg = (self.img_rgb * 0.3).astype(np.uint8)
        
        self.update_full_display_image()
        self.reset_view()
        self.update()

    def reset_view(self):
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        if self.img_rgb is not None:
            w_ratio = self.width() / self.img_rgb.shape[1]
            h_ratio = self.height() / self.img_rgb.shape[0]
            self.scale = min(w_ratio, h_ratio) * 0.9
            
            content_w = self.img_rgb.shape[1] * self.scale
            content_h = self.img_rgb.shape[0] * self.scale
            self.offset = QPointF((self.width() - content_w) / 2, (self.height() - content_h) / 2)

    def update_full_display_image(self):
        """全量更新显示图像 (仅在初始化时调用)"""
        if self.img_rgb is None: return

        h, w, c = self.img_rgb.shape
        
        # 融合: 前景(原图) + 背景(暗色)
        mask_3c = cv2.cvtColor(self.mask, cv2.COLOR_GRAY2RGB)
        mask_float = mask_3c.astype(float) / 255.0
        
        display_arr = (self.img_rgb * mask_float + self.dark_bg * (1 - mask_float)).astype(np.uint8)
        
        # 创建 QImage (注意保持引用，防止被垃圾回收)
        self.display_image = QImage(display_arr.data, w, h, w * 3, QImage.Format.Format_RGB888).copy()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制背景
        painter.fillRect(self.rect(), QColor("#141824"))

        # 2. 绘制图像
        if self.display_image:
            painter.translate(self.offset)
            painter.scale(self.scale, self.scale)
            painter.drawImage(0, 0, self.display_image)
            
            # 恢复坐标系用于绘制光标
            painter.resetTransform()

        # 3. 绘制自定义光标 (圆圈)
        # 只有在不拖拽且鼠标在窗口内时显示
        if not self.is_panning and not self.space_pressed:
            self.draw_brush_cursor(painter)

    def draw_brush_cursor(self, painter):
        # 笔刷半径在屏幕上的大小
        screen_radius = (self.brush_size / 2) * self.scale
        
        center = self.cursor_pos
        
        # 绘制白色外圈
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, screen_radius, screen_radius)
        
        # 绘制黑色内描边 (增强对比度，确保在白色背景也能看见)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(center, screen_radius, screen_radius)
        
        # 中心点
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(center, 1, 1)

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        mouse_pos = event.position()
        
        new_scale = self.scale * zoom_factor
        new_scale = max(0.1, min(new_scale, 10.0))
        
        p_img = (mouse_pos - self.offset) / self.scale
        
        self.scale = new_scale
        self.offset = mouse_pos - p_img * self.scale
        
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self.space_pressed):
            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.last_draw_point = self.map_to_image(event.position())
            self.apply_paint(self.last_draw_point)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.cursor_pos = event.position()
        
        if self.is_panning:
            delta = event.position() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.position()
            self.update()
        elif self.is_drawing:
            curr_point = self.map_to_image(event.position())
            self.apply_paint(curr_point)
            self.last_draw_point = curr_point
        else:
            # 仅更新光标位置
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton or self.is_panning:
            self.is_panning = False
            if self.space_pressed:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.BlankCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
            self.last_draw_point = None

    def map_to_image(self, pos):
        img_x = (pos.x() - self.offset.x()) / self.scale
        img_y = (pos.y() - self.offset.y()) / self.scale
        return (int(img_x), int(img_y))

    def apply_paint(self, point):
        if self.mask is None or point is None: return
        
        # 1. 计算 ROI (局部更新区域) - 核心优化点
        # 只更新笔刷划过的矩形区域，而不是整张图
        radius = self.brush_size // 2
        margin = radius + 5 # 安全边距
        
        if self.last_draw_point:
            p1 = self.last_draw_point
            p2 = point
            x_min = min(p1[0], p2[0]) - margin
            x_max = max(p1[0], p2[0]) + margin
            y_min = min(p1[1], p2[1]) - margin
            y_max = max(p1[1], p2[1]) + margin
        else:
            x, y = point
            x_min = x - margin
            x_max = x + margin
            y_min = y - margin
            y_max = y + margin
            
        h, w = self.mask.shape
        x_min = max(0, int(x_min))
        y_min = max(0, int(y_min))
        x_max = min(w, int(x_max))
        y_max = min(h, int(y_max))
        
        if x_max <= x_min or y_max <= y_min: return

        # 2. 更新 Mask (Numpy)
        color = 255 if self.mode == 'restore' else 0
        if self.last_draw_point:
            cv2.line(self.mask, self.last_draw_point, point, color, thickness=self.brush_size)
        else:
            cv2.circle(self.mask, point, radius, color, -1)
            
        # 3. 局部更新显示图像 (QImage)
        # 提取 ROI
        mask_roi = self.mask[y_min:y_max, x_min:x_max]
        img_roi = self.img_rgb[y_min:y_max, x_min:x_max]
        bg_roi = self.dark_bg[y_min:y_max, x_min:x_max]
        
        # 局部融合
        mask_3c = cv2.cvtColor(mask_roi, cv2.COLOR_GRAY2RGB)
        mask_float = mask_3c.astype(float) / 255.0
        blended_roi = (img_roi * mask_float + bg_roi * (1 - mask_float)).astype(np.uint8)
        
        # 转换 ROI 为 QImage
        h_roi, w_roi, _ = blended_roi.shape
        # 注意：必须 copy() 或者保持引用，否则 QImage 指向的内存会被释放
        qimg_roi = QImage(blended_roi.data, w_roi, h_roi, w_roi * 3, QImage.Format.Format_RGB888)
        
        # 绘制到主图上
        painter = QPainter(self.display_image)
        painter.drawImage(x_min, y_min, qimg_roi)
        painter.end()
        
        self.update()


class MaskRefineOverlay(QWidget):
    """
    全屏覆盖的修正层
    """
    finished = pyqtSignal(object) # 发送修改后的 mask

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #141824;")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. 画布区域
        self.canvas = RefineCanvas()
        layout.addWidget(self.canvas, 1)

        # 2. 右侧工具栏
        toolbar = QFrame()
        toolbar.setFixedWidth(280)
        toolbar.setStyleSheet("background-color: #1f2435; border-left: 1px solid #2b3042;")
        
        tb_layout = QVBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 40, 20, 40)
        tb_layout.setSpacing(25)

        # 标题
        lbl_title = QLabel("蒙版修正")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        
        lbl_desc = QLabel("• 滚轮缩放\n• 中键/空格+左键拖动\n• 左键涂抹")
        lbl_desc.setStyleSheet("color: #64748b; font-size: 12px; line-height: 18px;")

        # 模式选择
        lbl_mode = QLabel("工具模式")
        lbl_mode.setStyleSheet("color: #a0a5b5; font-weight: bold;")
        
        self.btn_restore = QPushButton("🖌️ 增加/找回")
        self.btn_restore.setCheckable(True)
        self.btn_restore.setChecked(True)
        self.btn_restore.clicked.connect(lambda: self.set_mode('restore'))
        
        self.btn_erase = QPushButton("🧽 擦除/移除")
        self.btn_erase.setCheckable(True)
        self.btn_erase.clicked.connect(lambda: self.set_mode('erase'))
        
        # 样式
        btn_style = """
            QPushButton { 
                background-color: #141824; color: white; border: 1px solid #2b3042; 
                padding: 12px; border-radius: 8px; font-size: 14px; text-align: left;
            }
            QPushButton:checked { 
                background-color: #2b3042; border: 1px solid #00f2ea; color: #00f2ea; 
            }
            QPushButton:hover { background-color: #252a3d; }
        """
        self.btn_restore.setStyleSheet(btn_style)
        self.btn_erase.setStyleSheet(btn_style)
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_restore)
        self.mode_group.addButton(self.btn_erase)

        # 笔刷大小
        lbl_size = QLabel("笔刷大小")
        lbl_size.setStyleSheet("color: #a0a5b5; font-weight: bold;")
        
        self.slider_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_size.setRange(5, 150)
        self.slider_size.setValue(20)
        self.slider_size.valueChanged.connect(self.update_brush_size)

        # 底部按钮
        btn_box = QVBoxLayout()
        btn_box.setSpacing(15)
        
        self.btn_save = QPushButton("完成并应用")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2ea, stop:1 #00c6fb);
                color: #141824; border: none; border-radius: 20px; font-weight: bold; font-size: 15px; height: 40px;
            }
            QPushButton:hover { background: #33f5ef; }
        """)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #a0a5b5; border: 1px solid #2b3042; 
                border-radius: 20px; font-weight: bold; font-size: 14px; height: 40px;
            }
            QPushButton:hover { color: white; border-color: white; }
        """)

        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(self.btn_cancel)

        # 组装工具栏
        tb_layout.addWidget(lbl_title)
        tb_layout.addWidget(lbl_desc)
        tb_layout.addSpacing(20)
        tb_layout.addWidget(lbl_mode)
        tb_layout.addWidget(self.btn_restore)
        tb_layout.addWidget(self.btn_erase)
        tb_layout.addSpacing(10)
        tb_layout.addWidget(lbl_size)
        tb_layout.addWidget(self.slider_size)
        tb_layout.addStretch()
        tb_layout.addLayout(btn_box)

        layout.addWidget(toolbar)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        toolbar.setGraphicsEffect(shadow)

    def set_data(self, img_rgb, mask):
        self.canvas.set_data(img_rgb, mask)

    def set_mode(self, mode):
        self.canvas.mode = mode

    def update_brush_size(self, val):
        self.canvas.brush_size = val

    def on_save(self):
        if self.canvas.mask is not None:
            self.finished.emit(self.canvas.mask)
        self.hide()

    def on_cancel(self):
        self.hide()