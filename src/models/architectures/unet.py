import os
import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms
from ..base_model import PortraitSegmentationModel
# 导入网络结构定义
from .unet_model import UNet

class UNetModel(PortraitSegmentationModel):
    def __init__(self):
        super().__init__()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        
        # 定义预处理变换 (需与训练时保持一致)
        self.transform = transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self.load_weights()

    def load_weights(self):
        """加载训练好的权重文件"""
        weights_path = os.path.join('resources', 'weights', 'unet_portrait_v2.pth')
        
        if not os.path.exists(weights_path):
            print(f"Warning: 未找到权重文件 {weights_path}")
            return

        try:
            print(f"正在加载 U-Net 模型 (Device: {self.device})...")
            self.model = UNet(n_channels=3, n_classes=1, bilinear=True)
            
            state_dict = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            print("U-Net 模型加载成功！")
            
        except Exception as e:
            print(f"U-Net 模型加载失败: {e}")
            self.model = None

    def predict(self, image: np.ndarray, max_size: int = None) -> np.ndarray:
        """
        执行推理
        :param image: 输入图像 (H, W, 3) numpy array. 
                      注意：OpenCV 读取默认为 BGR，这里需要确保转为 RGB
        """
        if self.model is None:
            return np.zeros(image.shape[:2], dtype=np.uint8)

        h, w = image.shape[:2]
        
        # ---------------------------------------------------------
        # 1. 颜色空间检查与转换
        # ---------------------------------------------------------
        # 假设输入 image 是 OpenCV 读取的 BGR 格式，而模型训练用的是 RGB
        # 如果发现分割效果极差，请尝试取消下面这行的注释：
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 2. 预处理
        img_pil = Image.fromarray(image)
        input_tensor = self.transform(img_pil).unsqueeze(0).to(self.device)

        # 3. 推理
        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.sigmoid(output).squeeze(0).squeeze(0) # [512, 512]
            
            # -----------------------------------------------------
            # [调试] 打印预测概率的最大值
            # 如果 Max Prob < 0.5，说明模型认为全图都是背景
            # -----------------------------------------------------
            max_val = probs.max().item()
            mean_val = probs.mean().item()
            print(f"[U-Net Debug] Max Prob: {max_val:.4f} (阈值0.5), Mean: {mean_val:.4f}")
            
            pred_mask = probs.cpu().numpy()

        # 4. 后处理
        # 恢复尺寸
        pred_mask = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # 二值化
        mask = (pred_mask > 0.5).astype(np.uint8) * 255
        
        return mask