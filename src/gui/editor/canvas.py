from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame 
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter

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
        h, w, c = img_array.shape
        bytes_per_line = 3 * w
        qimg = QImage(img_array.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, w, h)

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