import os
os.environ['TORCH_HOME'] = './resources/weights'

import torch
import numpy as np
from torchvision import models, transforms
from PIL import Image
from ..base_model import PortraitSegmentationModel
from ..config import MODEL_CONFIGS

class DeepLabModel(PortraitSegmentationModel):
    def __init__(self):
        super().__init__()
        self.load_weights()

    def load_weights(self):
        print("正在加载 DeepLabV3+ (ResNet101)...")
        try:
            # weights='DEFAULT' 会自动下载官方在 COCO 上预训练的最佳权重
            self.model = models.segmentation.deeplabv3_resnet101(weights='DEFAULT')
            self.model.to(self.device)
            self.model.eval() # 切换到评估模式
            print(f"DeepLabV3+ 加载成功，运行设备: {self.device}")
        except Exception as e:
            print(f"DeepLabV3+ 加载失败: {e}")
            raise e

    def predict(self, image: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("模型未初始化")

        # 1. 预处理 (DeepLab 官方标准)
        preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # numpy -> PIL -> Tensor
        input_image = Image.fromarray(image)
        input_tensor = preprocess(input_image)
        # 添加 batch 维度: (C, H, W) -> (1, C, H, W)
        input_batch = input_tensor.unsqueeze(0).to(self.device)

        # 2. 推理
        with torch.no_grad():
            output = self.model(input_batch)['out'][0]
        
        # 3. 后处理
        # output shape: (21, H, W)
        output_predictions = output.argmax(0).byte().cpu().numpy()
        
        # 提取人像类别 (Index 15)
        person_idx = MODEL_CONFIGS["DeepLabV3+"]["person_class_index"]
        mask = (output_predictions == person_idx).astype(np.uint8) * 255
        
        return mask