# 模型配置字典
MODEL_CONFIGS = {
    "DeepLabV3+": {
        "type": "deeplab",
        "person_class_index": 15, # COCO数据集中的'person'类别索引
        "description": "使用 ResNet101 骨干网络的 DeepLabV3"
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