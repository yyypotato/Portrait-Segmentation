from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

class HistoryPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #141824; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        header = QLabel("云端历史记录")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00f2ea;")
        layout.addWidget(header)

        list_widget = QListWidget()
        list_widget.setStyleSheet("background-color: #1f2435; border: none; border-radius: 10px; padding: 10px;")
        list_widget.addItems([f"历史记录 - 2023-12-{day} (已同步)" for day in range(10, 20)])
        layout.addWidget(list_widget)

        btn_back = QPushButton("返回首页")
        btn_back.clicked.connect(self.go_back.emit)
        btn_back.setStyleSheet("background-color: #1f2435; padding: 10px; border-radius: 5px; color: #a0a5b5;")
        layout.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignCenter)