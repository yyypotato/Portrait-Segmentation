# Portrait Segmentation Project

## 项目架构 (Project Architecture)

本项目采用模块化设计，将界面(GUI)、模型逻辑(Models)和工具函数(Utils)分离，便于扩展和维护。

```
PortraitSeg/
├── main.py                 # 程序入口 (Entry point)
├── requirements.txt        # 项目依赖 (Dependencies)
├── config/                 # 配置文件目录
│   └── config.yaml         # (可选) 模型路径、默认参数配置
├── resources/              # 静态资源
│   └── weights/            # 存放模型权重文件 (.pth, .onnx 等)
└── src/                    # 源代码目录
    ├── gui/                # 图形用户界面代码
    │   ├── __init__.py
    │   └── main_window.py  # PyQt 主窗口逻辑
    ├── models/             # 模型相关代码
    │   ├── __init__.py
    │   ├── base_model.py   # 模型抽象基类 (定义统一接口)
    │   ├── unet.py         # U-Net 模型实现类
    │   ├── fcn.py          # FCN 模型实现类
    │   └── factory.py      # 模型工厂模式 (用于动态加载模型)
    └── utils/              # 工具函数
        ├── __init__.py
        └── image_process.py# 图像预处理与后处理
```

## 模块说明

1.  **src.gui**: 负责所有界面展示和交互。`main_window.py` 包含图像上传、模型选择、分割按钮和结果展示。
2.  **src.models**: 负责深度学习模型的加载和推理。
    *   `base_model.py`: 定义了 `load_model` 和 `predict` 等标准接口，确保不同模型可以被 GUI 统一调用。
    *   `factory.py`: 根据 GUI 选择的名称（如 "U-Net"）实例化对应的模型类。
3.  **src.utils**: 包含图像的读取、缩放、归一化（预处理）以及将掩码转换为可视化图像（后处理）。

## 使用方法

1.  安装依赖: `pip install -r requirements.txt`
2.  运行程序: `python main.py`
