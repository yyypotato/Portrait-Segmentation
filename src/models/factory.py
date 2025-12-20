from .architectures.deeplab import DeepLabModel
from .architectures.unet import UNetModel

class ModelFactory:
    @staticmethod
    def create_model(model_name: str):
        """
        根据名称创建模型实例
        """
        if model_name == "DeepLabV3+ (ResNet101)":
            return DeepLabModel(backbone='resnet101')
            
        elif model_name == "DeepLabV3+ (MobileNetV3)":
            return DeepLabModel(backbone='mobilenet_v3_large')
        
        elif model_name == "U-Net":
            return UNetModel()
            
        else:
            # 默认回退
            print(f"未匹配到精确模型 {model_name}，尝试默认 DeepLab (MobileNetV3)")
            return DeepLabModel(backbone='mobilenet_v3_large')