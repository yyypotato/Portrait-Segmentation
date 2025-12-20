from abc import ABC, abstractmethod
import numpy as np
import torch

class PortraitSegmentationModel(ABC):
    """
    人像分割模型抽象基类
    """
    def __init__(self):
        # 自动检测设备 (GPU优先)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None

    @abstractmethod
    def load_weights(self):
        """加载模型权重"""
        pass

    @abstractmethod
    def predict(self, image: np.ndarray) -> np.ndarray:
        """
        执行推理
        :param image: 输入图像 (H, W, 3) RGB格式, uint8
        :return: 分割掩码 (H, W), 0为背景, 255为人像
        """
        pass