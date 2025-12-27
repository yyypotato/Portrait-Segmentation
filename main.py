import sys
import os
from PyQt6.QtWidgets import QApplication
# [修改] 移除顶部的 MainWindow 导入，防止启动时加载 PyTorch 导致长时间无反应
# from src.gui.main_window import MainWindow 
from src.gui.splash_screen import SplashScreen

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
    
    # 确保工作目录正确
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Microsoft YaHei")
    app.setFont(font)

    # 2. 马上显示加载页面 (此时还没有加载 PyTorch，启动速度极快)
    splash = SplashScreen()
    splash.show()
    
    # [关键] 强制刷新界面，确保加载动画先显示出来，再进行后续的重型加载
    app.processEvents()

    # 3. 延迟导入 MainWindow
    # MainWindow 内部会导入 PyTorch 等重型库，放在这里导入可以让用户先看到加载界面，而不是盯着桌面发呆
    from src.gui.main_window import MainWindow

    # 初始化主窗口 (此时加载界面在运行，后台在加载模型和UI)
    window = MainWindow()

    def show_main_window():
        window.show()
        # 默认进入主菜单 (MenuPage)
        if hasattr(window, 'stack'):
            window.stack.setCurrentIndex(0)

    # 4. 连接信号：只有当动画播放完毕(finished)时，才显示主窗口
    splash.finished.connect(show_main_window)
    
    # [修改] 删除了这里原本直接调用的 show_main_window()
    # 这样就解决了“加载的时候主菜单就直接出现了”的问题，现在会等待动画结束

    sys.exit(app.exec())

if __name__ == "__main__":
    main()