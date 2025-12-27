from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath

class SplashScreen(QWidget):
    # 加载完成信号
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(450, 350)
        # 设置无边框窗口和置顶
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # 设置背景透明，以便绘制圆角
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.progress = 0
        # 使用定时器模拟加载进度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30) # 每30ms更新一次，约3秒加载完成
        
        self.loading_text = "正在初始化..."

    def update_progress(self):
        self.progress += 1
        
        # 模拟不同阶段的提示文本
        if self.progress < 30:
            self.loading_text = "正在加载 AI 模型权重..."
        elif self.progress < 60:
            self.loading_text = "正在初始化图形界面..."
        elif self.progress < 90:
            self.loading_text = "正在准备工作台..."
        else:
            self.loading_text = "准备就绪，即将启动..."

        self.update() # 触发重绘事件
        
        if self.progress >= 100:
            self.timer.stop()
            self.finished.emit() # 发送完成信号
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 绘制窗口背景 (深色圆角矩形)
        rect = self.rect()
        bg_color = QColor("#141824")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 20, 20)

        # 2. 绘制标题
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Microsoft YaHei UI", 20, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 40, rect.width(), 50), Qt.AlignmentFlag.AlignCenter, "PortraitSeg AI")

        # 3. 绘制中间的“容器”
        container_w = 120
        container_h = 120
        cx = rect.center().x()
        cy = rect.center().y()
        
        container_rect = QRectF(cx - container_w/2, cy - container_h/2, container_w, container_h)
        
        # 绘制容器边框
        pen = QPen(QColor("#2b3042"))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(container_rect, 15, 15)

        # 4. 绘制“液体”填充效果
        # 计算当前填充高度
        fill_height = container_h * (self.progress / 100)
        
        # 定义填充区域 (从底部向上生长)
        fill_rect = QRectF(
            container_rect.x(), 
            container_rect.bottom() - fill_height, 
            container_w, 
            fill_height
        )
        
        # 使用 QPainterPath 创建裁剪区域，确保液体不会超出圆角容器
        path = QPainterPath()
        path.addRoundedRect(container_rect, 15, 15)
        painter.setClipPath(path)
        
        # 绘制填充颜色 (青色)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#00f2ea"))) 
        painter.drawRect(fill_rect)
        
        # 取消裁剪
        painter.setClipping(False)

        # 5. 绘制进度百分比
        # 为了在深色和浅色背景上都能看清，给文字加个阴影效果
        painter.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # 阴影
        painter.setPen(QColor(0, 0, 0, 100))
        painter.drawText(container_rect.translated(2, 2), Qt.AlignmentFlag.AlignCenter, f"{self.progress}%")
        
        # 正文
        painter.setPen(QColor("white"))
        painter.drawText(container_rect, Qt.AlignmentFlag.AlignCenter, f"{self.progress}%")
        
        # 6. 绘制底部提示文字
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Microsoft YaHei UI", 10))
        painter.drawText(QRectF(0, rect.height() - 60, rect.width(), 30), Qt.AlignmentFlag.AlignCenter, self.loading_text)