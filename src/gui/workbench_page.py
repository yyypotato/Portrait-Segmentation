import os
import json
import datetime
import torch
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, 
                             QPushButton, QHBoxLayout, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QPixmap

# 配置文件路径
CONFIG_DIR = os.path.join("resources", "config")
RECENT_FILES_JSON = os.path.join(CONFIG_DIR, "recent_files.json")

class ProjectCard(QFrame):
    """单个项目卡片组件"""
    clicked = pyqtSignal(str)  # 点击时发送文件路径
    delete_requested = pyqtSignal(str) # [新增] 请求删除信号

    def __init__(self, file_path, timestamp):
        super().__init__()
        self.file_path = file_path
        self.timestamp = timestamp
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(110) # 增加高度以容纳图片
        
        # 卡片样式
        self.setStyleSheet("""
            ProjectCard {
                background-color: #1f2435;
                border-radius: 10px;
                border: 1px solid #2b3042;
            }
            ProjectCard:hover {
                border: 1px solid #00f2ea;
                background-color: #252a3d;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        # [修改] 使用水平布局：图片 | 信息 | 删除按钮
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # --- 1. 图片缩略图 ---
        lbl_thumb = QLabel()
        lbl_thumb.setFixedSize(90, 90)
        lbl_thumb.setStyleSheet("background-color: #141824; border-radius: 5px; border: 1px solid #2b3042;")
        lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(file_path):
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # 保持比例缩放
                    pixmap = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    lbl_thumb.setPixmap(pixmap)
                else:
                    lbl_thumb.setText("无法预览")
                    lbl_thumb.setStyleSheet("color: #64748b; font-size: 10px; background-color: #141824; border-radius: 5px;")
            except:
                lbl_thumb.setText("Error")
        else:
            lbl_thumb.setText("文件丢失")
            lbl_thumb.setStyleSheet("color: #ef4444; font-size: 10px; background-color: #141824; border-radius: 5px;")
            
        layout.addWidget(lbl_thumb)
        
        # --- 2. 信息区域 ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # 文件名
        name = os.path.basename(file_path)
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        
        # 路径 (截断显示)
        lbl_path = QLabel(file_path)
        lbl_path.setStyleSheet("color: #64748b; font-size: 12px;")
        # 简单的路径显示，不做复杂截断
        
        # 时间
        lbl_time = QLabel(f"上次编辑: {timestamp}")
        lbl_time.setStyleSheet("color: #00f2ea; font-size: 11px;")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_path)
        info_layout.addStretch()
        info_layout.addWidget(lbl_time)
        
        layout.addLayout(info_layout)
        
        # --- 3. 删除按钮 ---
        btn_del = QPushButton("×")
        btn_del.setFixedSize(24, 24)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setToolTip("从列表中移除记录")
        btn_del.clicked.connect(self.on_delete_clicked)
        btn_del.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748b;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #ef4444;
                color: white;
            }
        """)
        
        layout.addWidget(btn_del, 0, Qt.AlignmentFlag.AlignTop)

    def on_delete_clicked(self):
        self.delete_requested.emit(self.file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)

class WorkbenchPage(QWidget):
    go_back = pyqtSignal()
    open_project = pyqtSignal(str) # 请求打开文件 (连接到 SegPage)

    def __init__(self):
        super().__init__()
        self.ensure_config_exists()
        self.init_ui()

    def ensure_config_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        if not os.path.exists(RECENT_FILES_JSON):
            with open(RECENT_FILES_JSON, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def init_ui(self):
        self.setStyleSheet("background-color: #141824; color: white;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # --- 1. 顶部标题栏 ---
        header_layout = QHBoxLayout()
        title = QLabel("我的工作台")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00f2ea;")
        
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_recent_projects)
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: #1f2435; color: white; border: 1px solid #2b3042; padding: 5px 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #2b3042; }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_refresh)
        main_layout.addLayout(header_layout)

        # --- 2. 系统状态卡片 ---
        status_card = self.create_system_status_card()
        main_layout.addWidget(status_card)

        # --- 3. 最近项目区域 ---
        lbl_recent = QLabel("最近编辑的图片")
        lbl_recent.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(lbl_recent)

        # 使用 ScrollArea 包裹 Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget { background: transparent; }")
        
        self.projects_container = QWidget()
        self.projects_grid = QGridLayout(self.projects_container)
        self.projects_grid.setSpacing(15)
        self.projects_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll.setWidget(self.projects_container)
        main_layout.addWidget(scroll)

        # --- 4. 底部按钮 ---
        btn_back = QPushButton("返回首页")
        btn_back.clicked.connect(self.go_back.emit)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton { background-color: #1f2435; padding: 10px 30px; border-radius: 5px; color: #a0a5b5; border: 1px solid #2b3042; }
            QPushButton:hover { background-color: #2b3042; color: white; }
        """)
        main_layout.addWidget(btn_back, 0, Qt.AlignmentFlag.AlignCenter)

        # 初始化加载数据
        self.load_recent_projects()

    def create_system_status_card(self):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1f2435; border-radius: 10px; border: 1px solid #2b3042;")
        frame.setFixedHeight(100)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)

        # GPU 信息检测
        gpu_info = "未检测到 GPU (使用 CPU 模式)"
        gpu_color = "#64748b" # 灰色
        
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                # 尝试获取显存信息
                free, total = torch.cuda.mem_get_info(0)
                used_gb = (total - free) / 1024**3
                total_gb = total / 1024**3
                gpu_info = f"GPU 就绪: {gpu_name}\n显存占用: {used_gb:.1f}GB / {total_gb:.1f}GB"
                gpu_color = "#00f2ea" # 青色
            except:
                gpu_info = f"GPU 就绪: {torch.cuda.get_device_name(0)}"
                gpu_color = "#00f2ea"

        lbl_gpu = QLabel(gpu_info)
        lbl_gpu.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {gpu_color}; border: none;")
        
        # 简单的提示
        lbl_tip = QLabel("提示: 点击下方卡片可快速继续编辑")
        lbl_tip.setStyleSheet("color: #a0a5b5; font-size: 12px; border: none;")
        
        layout.addWidget(lbl_gpu)
        layout.addStretch()
        layout.addWidget(lbl_tip)
        
        return frame

    def load_recent_projects(self):
        """读取 JSON 并刷新界面"""
        # 清空现有列表
        for i in reversed(range(self.projects_grid.count())): 
            widget = self.projects_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            with open(RECENT_FILES_JSON, 'r', encoding='utf-8') as f:
                files = json.load(f)
        except Exception as e:
            print(f"加载最近文件失败: {e}")
            files = []

        if not files:
            empty_lbl = QLabel("暂无最近编辑记录。")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; margin: 20px; border: none;")
            self.projects_grid.addWidget(empty_lbl, 0, 0)
            return

        # 倒序显示，最新的在前面
        valid_count = 0
        for item in reversed(files):
            path = item.get("path")
            time_str = item.get("time", "未知时间")
            
            if path:
                card = ProjectCard(path, time_str)
                card.clicked.connect(self.on_project_clicked)
                card.delete_requested.connect(self.delete_project_record) # 连接删除信号
                # 每行显示 2 个
                self.projects_grid.addWidget(card, valid_count // 2, valid_count % 2)
                valid_count += 1

    def on_project_clicked(self, file_path):
        if os.path.exists(file_path):
            self.open_project.emit(file_path)
        else:
            QMessageBox.warning(self, "文件丢失", "找不到该文件，可能已被移动或删除。")
            # 不自动刷新，让用户自己决定是否删除记录

    def delete_project_record(self, file_path):
        """处理删除记录请求"""
        reply = QMessageBox.question(self, '确认删除', 
                                     f"确定要从历史记录中移除该文件吗？\n(不会删除本地物理文件)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(RECENT_FILES_JSON, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                
                # 过滤掉要删除的记录
                new_records = [r for r in records if r.get("path") != file_path]
                
                with open(RECENT_FILES_JSON, 'w', encoding='utf-8') as f:
                    json.dump(new_records, f, ensure_ascii=False, indent=2)
                
                self.load_recent_projects() # 刷新界面
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除失败: {str(e)}")

    @staticmethod
    def add_recent_record(file_path):
        """
        静态工具方法：供 SegPage 等页面调用，添加文件到最近列表
        """
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
            
        records = []
        if os.path.exists(RECENT_FILES_JSON):
            try:
                with open(RECENT_FILES_JSON, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            except:
                records = []

        # 1. 移除已存在的相同路径
        records = [r for r in records if r.get("path") != file_path]
        
        # 2. 添加新记录
        new_record = {
            "path": file_path,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        records.append(new_record)
        
        # 3. 只保留最近 20 条 (增加记录数)
        if len(records) > 20:
            records = records[-20:]
            
        # 4. 写入文件
        with open(RECENT_FILES_JSON, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)