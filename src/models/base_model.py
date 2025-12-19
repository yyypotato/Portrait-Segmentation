from abc import ABC, abstractmethod
import numpy as np

class PortraitSegmentationModel(ABC):
    """
    所有人像分割模型的基类。
    强制子类实现 load_weights 和 predict 方法。
    """
    
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path
        if model_path:
            self.load_weights(model_path)

    @abstractmethod
    def load_weights(self, path: str):
        """加载模型权重"""
        pass

    @abstractmethod
    def predict(self, image: np.ndarray) -> np.ndarray:
        """
        执行推理。
        :param image: 输入图像 (H, W, C) RGB
        :return: 分割掩码 (H, W) 或 (H, W, 1)
        """
        pass
