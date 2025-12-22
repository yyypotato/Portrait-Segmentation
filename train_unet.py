import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image
import numpy as np
from tqdm import tqdm

from src.models.architectures.unet_model import UNet

# 数据集路径 (根据你的目录结构)
DATA_ROOT = r"datasets/EG1800"
IMAGES_DIR = os.path.join(DATA_ROOT, "images")
MASKS_DIR = os.path.join(DATA_ROOT, "masks")

# 权重保存路径
WEIGHTS_DIR = r"resources/weights"
WEIGHTS_NAME = "unet_portrait.pth"

# 训练超参数
BATCH_SIZE = 4       # 如果显存不足 (如 <4GB)，请改为 2 或 1
LEARNING_RATE = 1e-4
EPOCHS = 50          # 建议至少训练 20-50 轮
IMG_SIZE = 512       # 训练时的图片大小 (U-Net 对尺寸不敏感，但统一尺寸方便批处理)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# ===========================================

class EG1800Dataset(Dataset):
    def __init__(self, images_dir, masks_dir, transform=None, mask_transform=None):
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.transform = transform
        self.mask_transform = mask_transform
        
        # 获取所有图片文件名
        self.image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # 过滤出有对应 mask 的图片
        self.valid_files = []
        for img_file in self.image_files:
            name_part = os.path.splitext(img_file)[0]
            # EG1800 的 mask 通常是 png 格式
            mask_file = name_part + ".png" 
            if os.path.exists(os.path.join(masks_dir, mask_file)):
                self.valid_files.append((img_file, mask_file))
            else:
                # 尝试 jpg 后缀
                mask_file = name_part + ".jpg"
                if os.path.exists(os.path.join(masks_dir, mask_file)):
                    self.valid_files.append((img_file, mask_file))

        print(f"数据集加载: 找到 {len(self.valid_files)} 对有效图片/掩码。")

    def __len__(self):
        return len(self.valid_files)

    def __getitem__(self, idx):
        img_name, mask_name = self.valid_files[idx]
        
        img_path = os.path.join(self.images_dir, img_name)
        mask_path = os.path.join(self.masks_dir, mask_name)
        
        try:
            image = Image.open(img_path).convert("RGB")
            mask = Image.open(mask_path).convert("L") # 转为灰度图 (单通道)
        except Exception as e:
            print(f"读取错误 {img_name}: {e}")
            # 返回随机数据防止崩溃 (实际应处理坏数据)
            return torch.zeros((3, IMG_SIZE, IMG_SIZE)), torch.zeros((1, IMG_SIZE, IMG_SIZE))

        if self.transform:
            image = self.transform(image)
        
        if self.mask_transform:
            mask = self.mask_transform(mask)
            # 二值化处理：确保 mask 只有 0 和 1
            # EG1800 mask 可能是 0/255 或 0/1，ToTensor 会归一化到 0-1
            mask = (mask > 0.5).float()

        return image, mask

def train():
    # 1. 准备数据预处理
    # 图片：缩放 -> 转Tensor -> 标准化 (ImageNet 均值)
    img_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # 掩码：缩放 (最近邻插值，防止产生虚假边缘值) -> 转Tensor
    mask_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE), interpolation=transforms.InterpolationMode.NEAREST),
        transforms.ToTensor()
    ])

    # 2. 加载数据集
    if not os.path.exists(IMAGES_DIR) or not os.path.exists(MASKS_DIR):
        print(f"错误：找不到数据集路径。\n请检查 {IMAGES_DIR} 和 {MASKS_DIR} 是否存在。")
        return

    full_dataset = EG1800Dataset(IMAGES_DIR, MASKS_DIR, transform=img_transform, mask_transform=mask_transform)
    
    if len(full_dataset) == 0:
        print("错误：数据集中没有找到有效的图片对。")
        return

    # 划分训练集 (90%) 和验证集 (10%)
    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    # Windows 下 num_workers 设为 0 比较稳定，Linux 可设为 4
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # 3. 初始化模型
    print(f"正在初始化 U-Net 模型 (Device: {DEVICE})...")
    # n_channels=3 (RGB), n_classes=1 (前景/背景二分类)
    model = UNet(n_channels=3, n_classes=1, bilinear=True).to(DEVICE)

    # 4. 优化器和损失函数
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    # BCEWithLogitsLoss 内部集成了 Sigmoid，数值稳定性比 Sigmoid + BCELoss 更好
    criterion = nn.BCEWithLogitsLoss() 

    # 5. 训练循环
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    save_path = os.path.join(WEIGHTS_DIR, WEIGHTS_NAME)
    best_val_loss = float('inf')

    print("开始训练...")
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0
        
        # 进度条
        with tqdm(total=len(train_loader), desc=f"Epoch {epoch+1}/{EPOCHS} [Train]", unit="batch") as pbar:
            for images, masks in train_loader:
                images = images.to(DEVICE)
                masks = masks.to(DEVICE)

                # 前向传播
                outputs = model(images)
                loss = criterion(outputs, masks)

                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()
                pbar.set_postfix({'loss': f"{loss.item():.4f}"})
                pbar.update(1)
        
        avg_train_loss = train_loss / len(train_loader)

        # 验证阶段
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, masks in val_loader:
                images = images.to(DEVICE)
                masks = masks.to(DEVICE)
                outputs = model(images)
                loss = criterion(outputs, masks)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_loader)
        
        print(f"Epoch {epoch+1} 结果 | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        # 保存最佳模型
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), save_path)
            print(f"--> 发现更优模型 (Val Loss: {avg_val_loss:.4f})，已保存至: {save_path}")
        
        # 也可以选择每轮都保存一个备份
        # torch.save(model.state_dict(), os.path.join(WEIGHTS_DIR, "last.pth"))

    print("\n训练完成！")
    print(f"最终权重文件位于: {save_path}")

if __name__ == "__main__":
    train()