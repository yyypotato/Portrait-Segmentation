from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextBrowser
from PyQt6.QtCore import pyqtSignal
from .styles import Styles

class HelpPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("使用说明")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        
        content = QTextBrowser()
        content.setHtml("""
        <h3>如何使用本工具：</h3>
        <p>1. 点击主菜单的 <b>“开始分割”</b> 按钮进入工作台。</p>
        <p>2. 点击 <b>“选择图片”</b> 导入您想要处理的人像照片。</p>
        <p>3. 在下拉框中选择您想使用的 AI 模型（如 U-Net）。</p>
        <p>4. 点击 <b>“开始分割”</b>，稍等片刻即可在右侧看到结果。</p>
        <hr>
        <p><i>版本: v1.0.0 (Preview)</i></p>
        """)
        content.setStyleSheet("border: none; background-color: #f1f2f6; padding: 20px; border-radius: 10px; font-size: 14px;")

        btn_back = QPushButton("返回主菜单")
        btn_back.setStyleSheet(Styles.BUTTON_STYLE)
        btn_back.clicked.connect(self.go_back.emit)

        layout.addWidget(title)
        layout.addWidget(content)
        layout.addWidget(btn_back)