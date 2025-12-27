from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QLinearGradient
import math

class SplashScreen(QWidget):
    # 加载完成信号
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 400)
        # 设置无边框窗口和置顶
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # 设置背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.progress = 0
        self.wave_phase = 0 # 波浪相位
        
        # 使用定时器模拟加载进度
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(20) # 提高刷新率以获得更流畅的波浪动画
        
        self.loading_text = "正在初始化..."

    def update_progress(self):
        # 进度增加速度 (约3-4秒完成)
        self.progress += 0.6 
        # 波浪移动速度
        self.wave_phase += 0.15
        
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

        # 1. 绘制窗口背景 (半透明磨砂玻璃效果)
        margin = 20
        rect = QRectF(margin, margin, self.width() - 2*margin, self.height() - 2*margin)
        
        # 背景色：深色带透明度 (Alpha 230)
        bg_color = QColor(20, 24, 36, 230) 
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 30, 30)
        
        # 细微的边框高光
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.5))
        painter.drawRoundedRect(rect, 30, 30)

        # 2. 绘制标题
        painter.setPen(QColor("white"))
        font_title = QFont("Microsoft YaHei UI", 22, QFont.Weight.Bold)
        font_title.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        painter.setFont(font_title)
        painter.drawText(QRectF(rect.left(), rect.top() + 40, rect.width(), 50), Qt.AlignmentFlag.AlignCenter, "PortraitSeg AI")

        # 3. 绘制中间的圆形容器
        container_size = 140
        cx = rect.center().x()
        cy = rect.center().y() + 10
        radius = container_size / 2
        center_pt = QPointF(cx, cy)
        
        # 绘制容器底色
        painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_pt, radius, radius)

        # 4. 绘制波浪液体效果
        # 创建圆形裁剪区域
        path_clip = QPainterPath()
        path_clip.addEllipse(center_pt, radius, radius)
        painter.setClipPath(path_clip)

        # 计算水位高度 (y轴向下增加)
        fill_ratio = min(self.progress / 100.0, 1.0)
        water_level_y = (cy + radius) - (2 * radius * fill_ratio)

        # 构建波浪路径
        path_wave = QPainterPath()
        path_wave.moveTo(cx - radius, cy + radius) # 左下
        path_wave.lineTo(cx + radius, cy + radius) # 右下
        path_wave.lineTo(cx + radius, water_level_y) # 右侧水位点

        # 绘制正弦波上表面
        # x 从右向左遍历
        amplitude = 5 * (1 - abs(fill_ratio - 0.5)) # 中间波浪大，两头小
        frequency = 0.06
        
        for x in range(int(cx + radius), int(cx - radius), -1):
            y = water_level_y + amplitude * math.sin((x - cx) * frequency + self.wave_phase)
            path_wave.lineTo(x, y)
            
        path_wave.lineTo(cx - radius, water_level_y) # 闭合到左侧
        path_wave.closeSubpath()

        # 液体渐变色 (青色 -> 蓝色)
        gradient = QLinearGradient(cx, cy + radius, cx, cy - radius)
        gradient.setColorAt(0, QColor("#00f2ea"))
        gradient.setColorAt(1, QColor("#0078d7"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path_wave)
        
        # 取消裁剪
        painter.setClipping(False)

        # 5. 绘制容器外圈
        ring_pen = QPen(QColor("#2b3042"))
        ring_pen.setWidth(4)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_pt, radius, radius)
        
        # 进度条高光圈 (装饰)
        painter.setPen(QPen(QColor(255, 255, 255, 20), 2))
        painter.drawEllipse(center_pt, radius - 3, radius - 3)

        # 6. 绘制进度百分比
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.setPen(QColor("white"))
        # 绘制文字阴影以增强对比度
        shadow_rect = QRectF(cx - radius + 2, cy - radius + 2, container_size, container_size)
        painter.setPen(QColor(0, 0, 0, 80))
        painter.drawText(shadow_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.progress)}%")
        
        painter.setPen(QColor("white"))
        painter.drawText(QRectF(cx - radius, cy - radius, container_size, container_size), Qt.AlignmentFlag.AlignCenter, f"{int(self.progress)}%")

        # 7. 绘制底部提示文字
        painter.setPen(QColor("#a0a5b5"))
        painter.setFont(QFont("Microsoft YaHei UI", 10))
        painter.drawText(QRectF(rect.left(), rect.bottom() - 50, rect.width(), 30), Qt.AlignmentFlag.AlignCenter, self.loading_text)