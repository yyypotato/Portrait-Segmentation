# Portrait Segmentation Tool (人像分割小工具)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![PyTorch](https://img.shields.io/badge/Model-PyTorch-orange)

一个基于 **PyQt6 + PyTorch** 的桌面端人像分割工具，支持 **DeepLabV3**（预训练权重自动下载/本地缓存）与 **U-Net**（可训练/可加载自定义权重），并内置图片编辑器（裁剪、滤镜、涂鸦、马赛克、贴纸、标签等）。


---

## ✨ 功能特性

### 人像分割
- **DeepLabV3+ ResNet101 / MobileNetV3**：开箱即用，首次运行自动下载权重并缓存到本地
- **U-Net（自定义）**：支持训练后加载 `resources/weights/unet_portrait.pth`
- **背景替换/合成**：将分割出的人像与背景图合成
- **结果保存**：保存透明 PNG 或合成图

### 图片编辑器（Editor）
- **基础调节**：亮度、对比度、饱和度、色相、锐化等
- **几何变换**：裁剪、旋转、翻转
- **创作工具**：涂鸦、马赛克（像素/模糊等）、贴纸、标签叠加
- **滤镜**：内置多种风格滤镜

---

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