# Portrait Segmentation Tool (人像分割小工具)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![PyTorch](https://img.shields.io/badge/Model-PyTorch-orange)

一个基于 **PyQt6 + PyTorch** 的桌面端人像分割工具，支持 **DeepLabV3**（预训练权重自动下载/本地缓存）与 **U-Net**（可训练/可加载自定义权重），并内置图片编辑器（裁剪、滤镜、涂鸦、马赛克、贴纸、标签等）。

---

## ✨ 功能特性

### 🧠 智能人像分割
- **多模型支持**：
  - **DeepLabV3+ (ResNet101)**：高精度，适合高质量输出。
  - **DeepLabV3+ (MobileNetV3)**：轻量级，速度快，适合低配设备。
  - **U-Net**：支持加载自定义训练的权重（例如：`resources/weights/unet_portrait_v2.pth`）。
- **蒙版修正 (Refine)**：支持使用画笔/橡皮擦手动修补分割蒙版，处理发丝等细节。
- **背景替换**：一键替换背景，支持光影融合（Harmonization）与边缘光效（Light Wrap）（以项目实现为准）。

### 🎨 全能图片编辑器
- **基础调节**：亮度、对比度、饱和度、色相、锐化、高光/阴影。
- **几何变换**：自由裁剪、旋转、翻转。
- **创作工具**：
  - **涂鸦**
  - **马赛克**
  - **贴纸 & 标签**
  - **相框**

### 📂 工作流管理
- **工作台 (Workbench)**：自动记录最近编辑项目，支持快速恢复。
- **历史 (History)**：查看历史导出记录（以项目实现为准）。

---

## 📂 项目结构

```text
PortraitSeg/
├─ main.py
├─ train_unet.py
├─ get_icons.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ .vscode/
│  └─ launch.json
├─ resources/
│  ├─ config/
│  │  └─ recent_files.json
│  ├─ icons/
│  ├─ images/                   # 若存在：person/background/stickers 等
│  └─ weights/
│     └─ hub/
│        └─ checkpoints/
└─ src/
   ├─ gui/
   │  ├─ main_window.py
   │  ├─ menu_page.py
   │  ├─ seg_page.py
   │  ├─ workbench_page.py
   │  ├─ history_page.py
   │  ├─ help_page.py
   │  ├─ splash_screen.py
   │  ├─ styles.py
   │  ├─ custom_widgets.py
   │  ├─ mask_refine_overlay.py
   │  └─ editor/
   │     ├─ editor_page.py
   │     ├─ processor.py
   │     ├─ canvas.py
   │     ├─ filters.py
   │     ├─ ui_components.py
   │     ├─ crop_overlay.py
   │     ├─ doodle_overlay.py
   │     ├─ mosaic_overlay.py
   │     ├─ sticker_overlay.py
   │     └─ label_overlay.py
   ├─ models/
   │  ├─ __init__.py
   │  ├─ factory.py
   │  ├─ base_model.py
   │  ├─ config.py
   │  └─ architectures/
   │     ├─ deeplab.py
   │     ├─ unet.py
   │     ├─ unet_model.py
   │     └─ unet_parts.py
   └─ utils/
      └─ image_processor.py
```

---

## ✅ 环境与安装（Quick Start）

### 1) 创建虚拟环境（Conda）
```bash
conda create -n portraitSeg python=3.11 -y
conda activate portraitSeg
```

### 2) 安装依赖
由于 PyTorch 的 GPU 版本需要匹配本地 CUDA 环境，建议先装 PyTorch，再装其余依赖。

**A. 安装 PyTorch（按官方命令）**  
访问：https://pytorch.org/get-started/locally/

> 示例（仅示意，请以官网为准）  
```bash
# CUDA 11.8 示例
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**B. 安装项目其余依赖**
```bash
pip install -r requirements.txt
```

### 3) 准备图标资源（如果项目需要）
```bash
python get_icons.py
```

### 4) 运行
在项目根目录执行：
```bash
python main.py
```

启动时会自动创建必要目录（例如 `output/`、`resources/weights/`）。

---

## 🧠 模型权重下载到哪里？

项目在 `src/models/architectures/deeplab.py` 中设置了本地权重目录（`TORCH_HOME = ./resources/weights`），因此 `torchvision` 自动下载的权重会落在：

```text
resources/weights/hub/checkpoints/
```

例如：
```text
resources/weights/hub/checkpoints/deeplabv3_resnet101_coco-586e9e4e.pth
```

## 🏋️ U-Net 训练（可选）

如果你希望使用/替换自己的 U-Net 权重，可以通过项目自带脚本训练。

### 1) 数据准备（建议）
准备训练集与验证集（图像与掩码一一对应）：

- 图像：RGB/JPG/PNG
- 掩码：单通道（0=背景，255=人像）或等价的二值掩码

> 具体数据目录结构以 `train_unet.py` 内的路径配置为准。

### 2) 开始训练
在项目根目录执行：

```bash
python train_unet.py
```

训练过程中会在终端输出 loss 等信息。

### 3) 权重输出位置
训练完成后，将生成/更新权重文件，位置位于：

```text
resources/weights/unet_portrait_v2.pth
```

### 4) 在应用中使用训练好的权重
- 将生成的 `.pth` 权重放到上面的路径（或替换同名文件）。
- 重启应用，在模型下拉框中选择 **U-Net**。

---

## 🖥️ 使用说明（GUI 工作流）

1. 打开应用，进入分割页面  
2. 上传图像  
3. 选择模型（下拉框）  
4. 点击 **开始分割**  
5. 选择背景图进行合成（可选）  
6. 保存分割结果 / 合成结果（建议保存到 `output/`）

---