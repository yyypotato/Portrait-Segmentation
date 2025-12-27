import os
import json
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QListWidgetItem, QPushButton, 
                             QProgressBar, QMessageBox, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QCursor

# 配置路径
OUTPUT_DIR = "output"
CONFIG_DIR = os.path.join("resources", "config")
SYNC_RECORD_JSON = os.path.join(CONFIG_DIR, "cloud_sync.json")

class HistoryPage(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_logged_in = False # 模拟登录状态
        self.synced_files = self.load_sync_record()
        self.init_ui()

    def load_sync_record(self):
        """加载已同步的文件列表"""
        if os.path.exists(SYNC_RECORD_JSON):
            try:
                with open(SYNC_RECORD_JSON, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def save_sync_record(self):
        """保存同步状态"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(SYNC_RECORD_JSON, 'w', encoding='utf-8') as f:
            json.dump(list(self.synced_files), f)

    def init_ui(self):
        self.setStyleSheet("background-color: #141824; color: white;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # --- 1. 顶部栏 (标题 + 用户信息) ---
        header_layout = QHBoxLayout()
        
        title_box = QVBoxLayout()
        title = QLabel("云端历史")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00f2ea;")
        subtitle = QLabel("查看已导出的作品并备份到云端")
        subtitle.setStyleSheet("color: #64748b; font-size: 14px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # 用户卡片
        self.user_card = QFrame()
        self.user_card.setStyleSheet("background-color: #1f2435; border-radius: 20px; padding: 5px;")
        self.user_card.setFixedSize(200, 50)
        user_layout = QHBoxLayout(self.user_card)
        user_layout.setContentsMargins(10, 5, 10, 5)
        
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(30, 30)
        self.lbl_avatar.setStyleSheet("background-color: #64748b; border-radius: 15px;")
        
        self.lbl_username = QLabel("未登录")
        self.lbl_username.setStyleSheet("font-weight: bold; border: none;")
        
        self.btn_login = QPushButton("登录")
        self.btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_login.clicked.connect(self.toggle_login)
        self.btn_login.setStyleSheet("""
            QPushButton { background-color: #00f2ea; color: #141824; border-radius: 10px; padding: 4px 10px; font-weight: bold; }
            QPushButton:hover { background-color: #00dbd4; }
        """)
        
        user_layout.addWidget(self.lbl_avatar)
        user_layout.addWidget(self.lbl_username)
        user_layout.addWidget(self.btn_login)
        
        header_layout.addWidget(self.user_card)
        main_layout.addLayout(header_layout)

        # --- 2. 操作栏 (同步按钮 + 进度条) ---
        action_bar = QHBoxLayout()
        
        self.btn_sync = QPushButton(" 立即同步到云端")
        self.btn_sync.setIcon(QIcon("resources/icons/cloud.png")) # 如果没有图标会自动忽略
        self.btn_sync.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sync.clicked.connect(self.start_sync)
        self.btn_sync.setStyleSheet("""
            QPushButton { 
                background-color: #1f2435; border: 1px solid #2b3042; 
                color: white; padding: 8px 20px; border-radius: 5px; 
            }
            QPushButton:hover { background-color: #2b3042; border-color: #00f2ea; }
            QPushButton:disabled { color: #64748b; border-color: #2b3042; }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #1f2435; height: 8px; border-radius: 4px; }
            QProgressBar::chunk { background-color: #00f2ea; border-radius: 4px; }
        """)
        
        action_bar.addWidget(self.btn_sync)
        action_bar.addWidget(self.progress_bar)
        main_layout.addLayout(action_bar)

        # --- 3. 图片画廊 (ListWidget IconMode) ---
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.ViewMode.IconMode)
        self.gallery.setIconSize(QSize(180, 180))
        self.gallery.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.gallery.setSpacing(15)
        self.gallery.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection) # 禁止选中，只响应双击
        self.gallery.setStyleSheet("""
            QListWidget { background-color: transparent; border: none; }
            QListWidget::item { background-color: #1f2435; border-radius: 10px; padding: 10px; }
            QListWidget::item:hover { background-color: #252a3d; border: 1px solid #00f2ea; }
        """)
        self.gallery.itemDoubleClicked.connect(self.open_image)
        
        main_layout.addWidget(self.gallery)

        # --- 4. 底部 ---
        btn_back = QPushButton("返回首页")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.clicked.connect(self.go_back.emit)
        btn_back.setStyleSheet("""
            QPushButton { background-color: #1f2435; padding: 10px 30px; border-radius: 5px; color: #a0a5b5; border: 1px solid #2b3042; }
            QPushButton:hover { background-color: #2b3042; color: white; }
        """)
        main_layout.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignCenter)

        # 初始加载
        self.refresh_gallery()

    def toggle_login(self):
        """模拟登录/登出"""
        if not self.is_logged_in:
            # 模拟登录成功
            self.is_logged_in = True
            self.lbl_username.setText("User_001")
            self.lbl_avatar.setStyleSheet("background-color: #00f2ea; border-radius: 15px;")
            self.btn_login.setText("退出")
            self.btn_login.setStyleSheet("background-color: #ef4444; color: white; border-radius: 10px; padding: 4px 10px; font-weight: bold;")
            QMessageBox.information(self, "欢迎", "登录成功！现在可以同步数据了。")
        else:
            # 登出
            self.is_logged_in = False
            self.lbl_username.setText("未登录")
            self.lbl_avatar.setStyleSheet("background-color: #64748b; border-radius: 15px;")
            self.btn_login.setText("登录")
            self.btn_login.setStyleSheet("background-color: #00f2ea; color: #141824; border-radius: 10px; padding: 4px 10px; font-weight: bold;")

    def refresh_gallery(self):
        """扫描 output 目录并刷新显示"""
        self.gallery.clear()
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        # 按修改时间倒序
        files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)

        for f in files:
            file_path = os.path.join(OUTPUT_DIR, f)
            
            # 创建图标
            icon = QIcon(file_path)
            
            # 判断同步状态
            status = "已同步" if f in self.synced_files else "未同步"
            
            item = QListWidgetItem(icon, f"{f}\n[{status}]")
            item.setData(Qt.ItemDataRole.UserRole, file_path) # 存储完整路径
            
            # 设置字体颜色
            if status == "已同步":
                item.setForeground(Qt.GlobalColor.green)
            else:
                item.setForeground(Qt.GlobalColor.gray)
                
            self.gallery.addItem(item)

    def start_sync(self):
        """模拟同步过程"""
        if not self.is_logged_in:
            QMessageBox.warning(self, "提示", "请先登录后再进行同步。")
            return

        # 找出未同步的文件
        if not os.path.exists(OUTPUT_DIR):
            return
            
        all_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        unsynced = [f for f in all_files if f not in self.synced_files]
        
        if not unsynced:
            QMessageBox.information(self, "提示", "所有文件已是最新状态。")
            return

        # 开始模拟进度
        self.btn_sync.setEnabled(False)
        self.btn_sync.setText("正在同步...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.sync_queue = unsynced
        self.sync_step = 0
        self.total_steps = len(unsynced)
        
        # 使用 Timer 模拟网络延迟
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_sync_step)
        self.timer.start(200) # 每200ms处理一张

    def process_sync_step(self):
        if self.sync_step < self.total_steps:
            # 处理一张图片
            filename = self.sync_queue[self.sync_step]
            self.synced_files.add(filename)
            
            # 更新进度
            self.sync_step += 1
            progress = int((self.sync_step / self.total_steps) * 100)
            self.progress_bar.setValue(progress)
        else:
            # 完成
            self.timer.stop()
            self.save_sync_record()
            self.refresh_gallery()
            
            self.btn_sync.setEnabled(True)
            self.btn_sync.setText(" 立即同步到云端")
            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "成功", f"成功同步了 {self.total_steps} 张图片到云端！")

    def open_image(self, item):
        """双击打开图片"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(file_path):
            os.startfile(file_path) # Windows 下调用系统默认看图软件