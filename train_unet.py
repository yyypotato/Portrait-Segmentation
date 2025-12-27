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

# [修改] 数据集路径指向新的 EG1800_Portrait
DATA_ROOT = r"datasets/EG1800_Portrait"
IMAGES_DIR = os.path.join(DATA_ROOT, "images")
MASKS_DIR = os.path.join(DATA_ROOT, "masks")

# 权重保存路径
WEIGHTS_DIR = r"resources/weights"

# [修改] 使用新的文件名，避免覆盖原来的 unet_portrait.pth
WEIGHTS_NAME = "unet_portrait_v2.pth"      

# [修改] 使用新的检查点文件名，确保从零开始训练（不读取旧数据集的进度）
CHECKPOINT_NAME = "last_checkpoint_v2.pth" 

# 训练超参数
BATCH_SIZE = 4
LEARNING_RATE = 1e-4
EPOCHS = 50
IMG_SIZE = 512

# 自动检测并选择 GPU
if torch.cuda.is_available():
    gpu_count = torch.cuda.device_count()
    print(f"\n[系统检测] 发现 {gpu_count} 个 NVIDIA GPU:")
    
    target_device = "cuda:0" # 默认选择第一张卡
    
    for i in range(gpu_count):
        gpu_name = torch.cuda.get_device_name(i)
        print(f"  - GPU {i}: {gpu_name}")
        
        # 简单的自动策略：如果发现名字里带 'RTX' 或 'GTX'，优先选它
        if "RTX" in gpu_name or "GTX" in gpu_name:
            target_device = f"cuda:{i}"

    DEVICE = target_device
    print(f"--> [已锁定] 训练将使用: {DEVICE} ({torch.cuda.get_device_name(int(DEVICE.split(':')[-1]))})\n")
else:
    DEVICE = "cpu"
    print("\n[警告] 未检测到 GPU，将使用 CPU 训练 (速度极慢)。")
    print("请检查: 1. 显卡驱动 2. PyTorch 版本 (pip list | findstr torch)\n")


RESUME = True  # 保持 True，以便支持 v2 版本的断点续训

class EG1800Dataset(Dataset):
    def __init__(self, images_dir, masks_dir, transform=None, mask_transform=None):
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.transform = transform
        self.mask_transform = mask_transform
        
        self.image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        self.valid_files = []
        for img_file in self.image_files:
            name_part = os.path.splitext(img_file)[0]
            
            # [修改] 适配多种 Mask 命名规则
            # 优先尝试: 00001.jpg -> 00001_mask.png (您当前的数据集格式)
            # 其次尝试: 00001.jpg -> 00001.png (标准 EG1800 格式)
            possible_masks = [
                name_part + "_mask.png", 
                name_part + ".png",
                name_part + ".jpg"
            ]
            
            found = False
            for mask_file in possible_masks:
                if os.path.exists(os.path.join(masks_dir, mask_file)):
                    self.valid_files.append((img_file, mask_file))
                    found = True
                    break
            
            # if not found:
            #     print(f"Warning: No mask found for {img_file}")

        print(f"数据集加载: 找到 {len(self.valid_files)} 对有效图片/掩码。")

    def __len__(self):
        return len(self.valid_files)

    def __getitem__(self, idx):
        img_name, mask_name = self.valid_files[idx]
        img_path = os.path.join(self.images_dir, img_name)
        mask_path = os.path.join(self.masks_dir, mask_name)
        
        try:
            image = Image.open(img_path).convert("RGB")
            mask = Image.open(mask_path).convert("L")
        except Exception as e:
            print(f"读取错误 {img_name}: {e}")
            return torch.zeros((3, IMG_SIZE, IMG_SIZE)), torch.zeros((1, IMG_SIZE, IMG_SIZE))

        if self.transform:
            image = self.transform(image)
        
        if self.mask_transform:
            mask = self.mask_transform(mask)
            # [修改] 鲁棒性处理：只要大于 0 就视为前景
            # 防止 mask 像素值是 1/255 (0.0039) 时被 >0.5 截断为全黑
            mask = (mask > 0.0).float()

        return image, mask

def train():
    # 1. 数据准备
    img_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    mask_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE), interpolation=transforms.InterpolationMode.NEAREST),
        transforms.ToTensor()
    ])

    if not os.path.exists(IMAGES_DIR) or not os.path.exists(MASKS_DIR):
        print(f"错误：找不到数据集路径 {DATA_ROOT}")
        print(f"请检查 {IMAGES_DIR} 是否存在")
        return

    full_dataset = EG1800Dataset(IMAGES_DIR, MASKS_DIR, transform=img_transform, mask_transform=mask_transform)
    
    if len(full_dataset) == 0:
        print("错误：数据集中没有找到有效的图片对。")
        print(f"请检查 {IMAGES_DIR} 中的图片名与 {MASKS_DIR} 中的掩码名是否对应。")
        print("当前支持格式示例: image='00001.jpg', mask='00001_mask.png'")
        return

    train_size = int(0.9 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # 2. 初始化模型与优化器
    print(f"正在初始化 U-Net 模型 (Device: {DEVICE})...")
    model = UNet(n_channels=3, n_classes=1, bilinear=True).to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.BCEWithLogitsLoss() 

    # 3. 断点续训逻辑
    start_epoch = 0
    best_val_loss = float('inf')
    
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    checkpoint_path = os.path.join(WEIGHTS_DIR, CHECKPOINT_NAME)
    final_weights_path = os.path.join(WEIGHTS_DIR, WEIGHTS_NAME)

    if RESUME and os.path.exists(checkpoint_path):
        print(f"--> 发现检查点: {checkpoint_path}")
        try:
            checkpoint = torch.load(checkpoint_path, map_location=DEVICE)
            model.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            start_epoch = checkpoint['epoch'] + 1
            best_val_loss = checkpoint.get('best_val_loss', float('inf'))
            print(f"--> 成功恢复！将从 Epoch {start_epoch+1} 继续训练 (最佳 Loss: {best_val_loss:.4f})")
        except Exception as e:
            print(f"--> 恢复失败，将重新开始训练: {e}")
    else:
        print(f"--> 未发现检查点 {CHECKPOINT_NAME}，开始新的训练。")

    # 4. 训练循环
    for epoch in range(start_epoch, EPOCHS):
        model.train()
        train_loss = 0
        
        with tqdm(total=len(train_loader), desc=f"Epoch {epoch+1}/{EPOCHS} [Train]", unit="batch") as pbar:
            for images, masks in train_loader:
                images = images.to(DEVICE)
                masks = masks.to(DEVICE)

                outputs = model(images)
                loss = criterion(outputs, masks)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()
                pbar.set_postfix({'loss': f"{loss.item():.4f}"})
                pbar.update(1)
        
        avg_train_loss = train_loss / len(train_loader)

        # 验证
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
        print(f"Epoch {epoch+1} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        # 保存最佳模型 (仅权重，供 APP 使用)
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), final_weights_path)
            print(f"    [★] 发现更优模型，已更新: {final_weights_path}")

        # 保存检查点 (包含优化器状态，供续训使用)
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'best_val_loss': best_val_loss
        }
        torch.save(checkpoint, checkpoint_path)

    print("\n训练完成！")
    print(f"最终权重文件位于: {final_weights_path}")

if __name__ == "__main__":
    train()