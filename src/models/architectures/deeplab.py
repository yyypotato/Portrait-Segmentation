import os
# 确保权重下载到项目目录
os.environ['TORCH_HOME'] = './resources/weights'

import torch
import cv2
import numpy as np
from torchvision import models, transforms
from PIL import Image
from ..base_model import PortraitSegmentationModel
from ..config import MODEL_CONFIGS

class DeepLabModel(PortraitSegmentationModel):
    def __init__(self, backbone='resnet101'):
        # 先保存 backbone 设置，再调用父类初始化
        self.backbone = backbone
        super().__init__()
        self.load_weights()

    def load_weights(self):
        print(f"正在加载 DeepLabV3+ ({self.backbone})...")
        try:
            if self.backbone == 'resnet101':
                # 高精度版本
                self.model = models.segmentation.deeplabv3_resnet101(weights='DEFAULT')
            elif self.backbone == 'mobilenet_v3_large':
                # 轻量级版本
                self.model = models.segmentation.deeplabv3_mobilenet_v3_large(weights='DEFAULT')
            else:
                raise ValueError(f"不支持的骨干网络: {self.backbone}")
            
            self.model.to(self.device)
            self.model.eval()
            print(f"模型加载成功，运行设备: {self.device}")
            
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise e

    def predict(self, image: np.ndarray, max_size: int = None) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("模型未初始化")

        h, w = image.shape[:2]
        scale_factor = 1.0
        input_image_data = image

        # --- 1. 动态缩放逻辑 ---
        if max_size is not None and max(h, w) > max_size:
            scale_factor = max_size / max(h, w)
            new_w = int(w * scale_factor)
            new_h = int(h * scale_factor)
            # 使用线性插值缩小图片
            input_image_data = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            print(f"为了节省显存，图片已缩放: {w}x{h} -> {new_w}x{new_h}")

        # --- 2. 预处理 ---
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        input_pil = Image.fromarray(input_image_data)
        input_tensor = preprocess(input_pil)
        input_batch = input_tensor.unsqueeze(0).to(self.device)

        # --- 3. 推理 ---
        with torch.no_grad():
            output = self.model(input_batch)['out'][0]
        
        # --- 4. 后处理 ---
        output_predictions = output.argmax(0).byte().cpu().numpy()
        
        # --- 5. 还原尺寸 ---
        if scale_factor != 1.0:
            # 使用最近邻插值 (INTER_NEAREST) 还原掩码，保证只有 0, 1, 2... 整数类别
            output_predictions = cv2.resize(output_predictions, (w, h), interpolation=cv2.INTER_NEAREST)

        # 提取人像 (Index 15)
        person_idx = 15 
        mask = (output_predictions == person_idx).astype(np.uint8) * 255
        
        return mask