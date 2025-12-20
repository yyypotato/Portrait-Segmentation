# 模型配置字典
MODEL_CONFIGS = {
    "DeepLabV3+ (ResNet101)": {
        "type": "deeplab",
        "backbone": "resnet101",
        "person_class_index": 15,
        "description": "高精度，显存占用大 (需 >4GB 显存)"
    },
    "DeepLabV3+ (MobileNetV3)": {
        "type": "deeplab",
        "backbone": "mobilenet_v3_large",
        "person_class_index": 15,
        "description": "速度快，显存占用小 (推荐笔记本使用)"
    },
    "U-Net": {
        "type": "unet",
        "description": "标准 U-Net 结构 (待实现)"
    },
    "FCN": {
        "type": "fcn",
        "description": "全卷积网络 (待实现)"
    }
}