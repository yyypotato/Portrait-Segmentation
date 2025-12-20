import numpy as np
from ..base_model import PortraitSegmentationModel

class UNetModel(PortraitSegmentationModel):
    def __init__(self):
        super().__init__()
        self.load_weights()

    def load_weights(self):
        print("警告: U-Net 模型尚未集成权重，目前仅为占位符。")
        # TODO: 在这里加载您训练好的 U-Net .pth 文件
        pass

    def predict(self, image: np.ndarray) -> np.ndarray:
        print("U-Net 推理: 返回空掩码")
        h, w, _ = image.shape
        # 返回全黑图片
        return np.zeros((h, w), dtype=np.uint8)