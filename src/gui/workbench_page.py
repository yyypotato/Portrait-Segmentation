from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class WorkbenchPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #141824; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        header = QLabel("我的工作台")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00f2ea;")
        layout.addWidget(header)
        layout.addSpacing(20)

        # 模拟最近项目列表
        grid = QGridLayout()
        grid.setSpacing(20)

        for i in range(4):
            card = self.create_task_card(f"项目 #{2024001+i}", "等待处理...", "2023-12-21")
            grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(grid)
        layout.addStretch()
        
        btn_back = QPushButton("返回首页")
        btn_back.clicked.connect(self.go_back.emit)
        btn_back.setStyleSheet("background-color: #1f2435; padding: 10px; border-radius: 5px; color: #a0a5b5;")
        layout.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignCenter)

    def create_task_card(self, title, status, date):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1f2435; border-radius: 10px; border: 1px solid #2b3042;")
        frame.setFixedHeight(120)
        
        l = QVBoxLayout(frame)
        t = QLabel(title); t.setStyleSheet("font-weight: bold; font-size: 16px; border: none;")
        s = QLabel(status); s.setStyleSheet("color: #eab308; border: none;")
        d = QLabel(date); d.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        
        l.addWidget(t); l.addWidget(s); l.addWidget(d)
        return frame