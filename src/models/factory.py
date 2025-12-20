from .architectures.deeplab import DeepLabModel
from .architectures.unet import UNetModel

class ModelFactory:
    @staticmethod
    def create_model(model_name: str):
        """
        根据名称创建模型实例
        """
        if model_name == "DeepLabV3+":
            return DeepLabModel()
        
        elif model_name == "U-Net":
            return UNetModel()
            
        elif model_name == "FCN":
            # 暂时复用 DeepLab 或者返回未实现
            print("FCN 暂未实现，使用 DeepLab 代替演示")
            return DeepLabModel()
            
        else:
            raise ValueError(f"不支持的模型名称: {model_name}")