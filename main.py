import sys
import os
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def ensure_directories():
    """确保必要的目录存在"""
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义需要创建的目录列表
    dirs = [
        os.path.join(root_dir, "output"),
        os.path.join(root_dir, "resources", "weights")
    ]
    
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"已创建目录: {d}")

def main():
    # 1. 先检查目录结构
    ensure_directories()
    
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()