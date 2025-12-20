import os
# 确保权重下载到项目目录
os.environ['TORCH_HOME'] = './resources/weights'

import torch
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

    def predict(self, image: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("模型未初始化")

        # 1. 预处理
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        input_image = Image.fromarray(image)
        input_tensor = preprocess(input_image)
        input_batch = input_tensor.unsqueeze(0).to(self.device)

        # 2. 推理 (这里不捕获异常，交给 GUI 层捕获以便弹窗)
        with torch.no_grad():
            output = self.model(input_batch)['out'][0]
        
        # 3. 后处理
        output_predictions = output.argmax(0).byte().cpu().numpy()
        
        # COCO 数据集中 'person' 类别索引为 15
        person_idx = 15 
        mask = (output_predictions == person_idx).astype(np.uint8) * 255
        
        return mask