from .base_model import PortraitSegmentationModel
import numpy as np

class UNetModel(PortraitSegmentationModel):
    def load_weights(self, path: str):
        print(f"Loading U-Net weights from {path}...")
        # TODO: Implement actual torch/onnx loading
        # self.model = torch.load(path)
        pass

    def predict(self, image: np.ndarray) -> np.ndarray:
        print("Running U-Net inference...")
        # Dummy output for demonstration
        h, w, _ = image.shape
        return np.zeros((h, w), dtype=np.uint8)

class FCNModel(PortraitSegmentationModel):
    def load_weights(self, path: str):
        print(f"Loading FCN weights from {path}...")
        pass

    def predict(self, image: np.ndarray) -> np.ndarray:
        print("Running FCN inference...")
        h, w, _ = image.shape
        return np.zeros((h, w), dtype=np.uint8)
