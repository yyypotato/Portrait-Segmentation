from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame 
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter
import numpy as np

class EditorCanvas(QGraphicsView):
    """
    支持缩放、拖拽的高性能画板
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        # 优化渲染属性
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False) # 图片不需要抗锯齿，要锐利
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True) # 缩放时平滑
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # 允许拖拽
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: transparent;")

    def set_image(self, img_array):
        """设置显示的 numpy 图片"""
        if img_array is None: return
        
        # 1. 确保内存连续 (OpenCV 有时返回非连续内存，会导致显示错乱)
        img_array = np.ascontiguousarray(img_array)
        
        h, w, c = img_array.shape
        bytes_per_line = c * w
        
        # 2. 转换数据类型 [关键修复]
        # PyQt6 QImage 不接受 memoryview，必须转为 bytes
        # .tobytes() 会创建数据副本，虽然有微小开销但能保证类型安全且防止崩溃
        qimg = QImage(img_array.data.tobytes(), w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, w, h)

    def get_image_rect(self):
        """
        获取图片在 View 坐标系中的实际显示区域
        供 CropOverlay 使用，确保裁剪框紧贴图片
        """
        if self.pixmap_item.pixmap().isNull():
            return QRectF()
            
        # 1. 获取 Item 在 Scene 中的边界
        item_rect_scene = self.pixmap_item.sceneBoundingRect()
        
        # 2. 将 Scene 坐标映射回 View (窗口) 坐标
        # mapFromScene 返回的是 QPolygon，需要取 boundingRect
        view_poly = self.mapFromScene(item_rect_scene)
        return view_poly.boundingRect().toRectF()

    def fit_in_view(self):
        """自适应窗口大小"""
        if self.pixmap_item.pixmap().isNull(): return
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        """鼠标滚轮缩放"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)