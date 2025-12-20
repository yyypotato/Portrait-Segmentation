# Portrait Segmentation Tool (人像分割小工具)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![PyTorch](https://img.shields.io/badge/Model-PyTorch-orange)

基于 PyTorch 和 PyQt6 开发的现代化桌面端人像分割与背景合成工具。本项目集成了 DeepLabV3+ 模型，支持自动抠图与背景替换，并针对不同显存配置提供了多种模型选择。

## ✨ 功能特性 (Features)

*   **现代化 GUI 界面**: 采用 PyQt6 构建的卡片式设计，包含主菜单、工作台和帮助页，交互流畅。
*   **多模型支持**:
    *   **DeepLabV3+ (ResNet101)**: 高精度分割模式（适合显存 > 4GB 的设备）。
    *   **DeepLabV3+ (MobileNetV3)**: 轻量级极速模式（适合笔记本或低显存设备）。
    *   **U-Net**: (预留接口) 支持扩展自定义训练的 U-Net 模型。
*   **自动权重管理**: 首次运行时自动通过 `torchvision` 下载并缓存预训练权重，无需手动配置。
*   **背景合成**: 支持实时上传背景图，将分割后的人像与新背景进行合成。
*   **智能显存保护**: 自动捕获 CUDA OOM (显存不足) 错误，并弹出优化建议，防止程序崩溃。
*   **结果保存**: 支持保存透明背景的 PNG 图像或合成后的 JPG 图像。

## 📂 项目结构

```text
PortraitSeg/
├─ main.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ .vscode/
│  └─ launch.json
├─ output/                      # 运行输出（自动创建）
├─ resources/
│  ├─ images/
│  │  ├─ person/                # 测试人像
│  │  └─ background/            # 测试背景
│  └─ weights/
│     └─ hub/checkpoints/       # torchvision 权重缓存（自动下载）
├─ config/                      # 预留（目前为空，可放 YAML/JSON 配置）
└─ src/
   ├─ gui/
   │  ├─ main_window.py
   │  ├─ menu_page.py
   │  ├─ seg_page.py
   │  ├─ help_page.py
   │  └─ styles.py
   ├─ models/
   │  ├─ base_model.py
   │  ├─ config.py
   │  ├─ factory.py
   │  └─ architectures/
   │     ├─ deeplab.py
   │     └─ unet.py             # 占位/可扩展
   └─ utils/                    # 预留
```

---

## ✅ 环境与安装（Quick Start）

### 1) 创建虚拟环境（推荐 Conda）

```bash
conda create -n portraitSeg python=3.11.14 -y
conda activate portraitSeg
```

### 2) 安装依赖

您当前的 `requirements.txt` 包含 `torch==2.7.1+cu118` 这类 **CUDA 特定构建**，在某些情况下直接 `pip install -r requirements.txt` 可能会因为下载源不同而失败。更稳妥的方式是：

#### A. GPU（NVIDIA）版本（推荐）
先按 PyTorch 官方方式安装对应 CUDA 版本的 torch/torchvision，然后再安装其余依赖。

示例（请以 PyTorch 官网为准）：  
https://pytorch.org/get-started/locally/

#### B. CPU 版本
如果没有 NVIDIA GPU 或不想用 GPU，可安装 CPU 版 torch/torchvision。

安装完 torch/torchvision 后，再安装其它依赖：

```bash
pip install -r requirements.txt
```

### 3) 运行

在项目根目录执行：

```bash
python main.py
```

启动时会自动创建必要目录（例如 `output/`、`resources/weights/`）。

---

## 🧠 模型权重下载到哪里？

项目中 `src/models/architectures/deeplab.py` 里设置了：

- `TORCH_HOME = ./resources/weights`

因此 `torchvision` 自动下载的权重会落在类似路径：

```text
resources/weights/hub/checkpoints/
```

您当前目录中已存在示例权重：

```text
resources/weights/hub/checkpoints/deeplabv3_resnet101_coco-586e9e4e.pth
```

---

## 🖥️ 使用说明（GUI 工作流）

1. 打开应用，进入分割页面  
2. **上传图像**（建议从 `resources/images/person/` 选择测试图）
3. **选择模型**（下拉框）
4. 点击 **开始分割**
5. 选择背景图（建议从 `resources/images/background/`）
6. 保存分割结果 / 合成结果（默认建议保存到 `output/`）

---