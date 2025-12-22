import cv2
import numpy as np

def _adjust_saturation(img, saturation_scale):
    """辅助函数：调整饱和度"""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] *= saturation_scale
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

def _apply_vignette(img, strength=0.5):
    """辅助函数：添加暗角"""
    rows, cols = img.shape[:2]
    # 生成高斯核
    kernel_x = cv2.getGaussianKernel(cols, cols/2)
    kernel_y = cv2.getGaussianKernel(rows, rows/2)
    kernel = kernel_y * kernel_x.T
    mask = kernel / kernel.max()
    
    # 调整暗角强度
    mask = mask * (1 - strength) + strength
    mask = np.dstack([mask] * 3)
    
    return np.clip(img * mask, 0, 255).astype(np.uint8)

def _apply_curve(img, x_points, y_points):
    """辅助函数：模拟曲线调整 (使用LUT)"""
    # 创建查找表
    lut = np.interp(np.arange(256), x_points, y_points).astype(np.uint8)
    return cv2.LUT(img, lut)

def apply_filter(img, filter_name):
    """
    应用滤镜效果
    :param img: 输入图像 (RGB numpy array, uint8)
    :param filter_name: 滤镜名称
    :return: 处理后的图像 (RGB numpy array, uint8)
    """
    if filter_name == "original" or filter_name == "f_original":
        return img

    # ---------------------------------------------------------
    # 1. 特殊算法类滤镜 (不基于简单的 RGB 调整)
    # ---------------------------------------------------------

    if filter_name == "f_demist":
        # 【去雾优化】：使用 CLAHE (限制对比度自适应直方图均衡化)
        # 转换到 LAB 空间，只处理 L (亮度) 通道
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # 创建 CLAHE 对象 (clipLimit 控制对比度限制，tileGridSize 控制局部大小)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # 合并并转回 RGB
        limg = cv2.merge((cl, a, b))
        res = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        
        # 稍微增加一点饱和度以补偿去雾后的色彩
        return _adjust_saturation(res, 1.1)

    elif filter_name == "f_mono":
        # 【黑白】：标准灰度
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif filter_name == "f_individuality":
        # 【个性优化】：Bleach Bypass (跳过漂白) 风格
        # 特点：高对比度，低饱和度，银色质感
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        # 混合原图和灰度图 (叠加模式 Overlay 模拟)
        img_f = img.astype(np.float32) / 255.0
        gray_f = gray.astype(np.float32) / 255.0
        
        # Overlay blending logic
        mask = img_f < 0.5
        res = np.zeros_like(img_f)
        res[mask] = 2 * img_f[mask] * gray_f[mask]
        res[~mask] = 1 - 2 * (1 - img_f[~mask]) * (1 - gray_f[~mask])
        
        res = np.clip(res * 255, 0, 255).astype(np.uint8)
        # 降低饱和度
        return _adjust_saturation(res, 0.6)

    elif filter_name == "f_classic":
        # 【经典】：Sepia 怀旧色矩阵
        img_f = img.astype(np.float32)
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        sepia = cv2.transform(img_f, kernel)
        return np.clip(sepia, 0, 255).astype(np.uint8)

    elif filter_name == "f_vintage":
        # 【复古】：暖色 + 暗角 + 降低对比度
        res = _adjust_saturation(img, 0.8)
        # 提升红色和绿色 (变黄)
        lut_r = np.interp(np.arange(256), [0, 255], [20, 235]).astype(np.uint8)
        lut_b = np.interp(np.arange(256), [0, 255], [0, 215]).astype(np.uint8) # 蓝色压暗
        res[:,:,0] = cv2.LUT(res[:,:,0], lut_r)
        res[:,:,2] = cv2.LUT(res[:,:,2], lut_b)
        return _apply_vignette(res, 0.6)

    # ---------------------------------------------------------
    # 2. 调色类滤镜 (基于 LUT 曲线和通道混合)
    # ---------------------------------------------------------
    
    # 准备工作：转为 float 方便计算，或者直接操作 LUT
    # 这里为了性能和效果平衡，混合使用
    
    res = img.copy()

    if filter_name == "f_dawn":
        # 【晨光】：低对比度，紫色/洋红倾向
        res = cv2.addWeighted(res, 1.1, np.zeros_like(res), 0, 10) # 提亮
        res[:,:,0] = cv2.LUT(res[:,:,0], np.arange(256).astype(np.uint8)) # R
        res[:,:,1] = cv2.LUT(res[:,:,1], np.interp(np.arange(256), [0, 255], [0, 230]).astype(np.uint8)) # G 减少
        res[:,:,2] = cv2.LUT(res[:,:,2], np.interp(np.arange(256), [0, 255], [20, 255]).astype(np.uint8)) # B 增加 (暗部偏蓝)

    elif filter_name == "f_pure":
        # 【纯净】：冷色调，高亮度
        res = _adjust_saturation(res, 0.9)
        res[:,:,2] = cv2.LUT(res[:,:,2], np.interp(np.arange(256), [0, 128, 255], [0, 138, 255]).astype(np.uint8)) # 提升蓝色中间调

    elif filter_name == "f_metallic":
        # 【金属】：极高对比度，极低饱和度
        res = _adjust_saturation(res, 0.3)
        # S型曲线增加对比度
        lut = np.interp(np.arange(256), [0, 64, 192, 255], [0, 40, 215, 255]).astype(np.uint8)
        res = cv2.LUT(res, lut)

    elif filter_name == "f_blue":
        # 【蓝调】：强烈的蓝色滤镜
        res[:,:,2] = cv2.LUT(res[:,:,2], np.interp(np.arange(256), [0, 255], [40, 255]).astype(np.uint8))

    elif filter_name == "f_cool":
        # 【清凉】：青色调 (减红，加蓝绿)
        res[:,:,0] = cv2.LUT(res[:,:,0], np.interp(np.arange(256), [0, 255], [0, 230]).astype(np.uint8))

    elif filter_name == "f_pink":
        # 【粉嫩】：增加红色和蓝色，提亮
        res[:,:,1] = cv2.LUT(res[:,:,1], np.interp(np.arange(256), [0, 255], [0, 240]).astype(np.uint8)) # 减绿
        res = cv2.addWeighted(res, 1.05, np.zeros_like(res), 0, 5)

    elif filter_name in ["f_soft", "f_fair", "f_netural"]:
        # 【柔和/白皙】：模拟柔光镜 (Glow)
        # 高斯模糊后与原图混合
        blur = cv2.GaussianBlur(res, (0, 0), 5)
        res = cv2.addWeighted(res, 0.7, blur, 0.3, 10)
        # 稍微提亮
        res = _adjust_saturation(res, 0.9)

    elif filter_name in ["f_impact", "f_halo"]:
        # 【冲击】：强对比度，高饱和
        res = _adjust_saturation(res, 1.3)
        lut = np.interp(np.arange(256), [0, 80, 175, 255], [0, 50, 205, 255]).astype(np.uint8)
        res = cv2.LUT(res, lut)

    elif filter_name == "f_moody":
        # 【情绪】：暗调，低饱和
        res = _adjust_saturation(res, 0.7)
        res = cv2.addWeighted(res, 0.8, np.zeros_like(res), 0, 0) # 压暗

    elif filter_name in ["f_blossom", "f_sweet"]:
        # 【桃花/甜美】：暖粉色
        lut_r = np.interp(np.arange(256), [0, 255], [10, 255]).astype(np.uint8)
        res[:,:,0] = cv2.LUT(res[:,:,0], lut_r)

    elif filter_name in ["f_caramel", "f_valencia"]:
        # 【焦糖】：暖黄，褪色感
        res[:,:,2] = cv2.LUT(res[:,:,2], np.interp(np.arange(256), [0, 255], [0, 220]).astype(np.uint8)) # 减蓝
        
        # 修复：cv2.addWeighted 不支持广播，必须创建同尺寸的覆盖层
        overlay = np.full_like(res, [20, 10, 0])
        res = cv2.addWeighted(res, 1.0, overlay, 0.1, 0) # 叠加暖色层

    elif filter_name == "f_memory":
        # 【回忆】：褪色黑 (Lifted Blacks)
        lut = np.interp(np.arange(256), [0, 40, 255], [30, 50, 255]).astype(np.uint8)
        res = cv2.LUT(res, lut)
        res[:,:,2] = cv2.LUT(res[:,:,2], np.interp(np.arange(256), [0, 255], [0, 230]).astype(np.uint8)) # 偏黄

    elif filter_name == "f_childhood":
        # 【童年】：高饱和，偏暖
        res = _adjust_saturation(res, 1.2)
        res = cv2.addWeighted(res, 1.05, np.zeros_like(res), 0, 0)

    elif filter_name in ["f_handsome", "f_sentimental"]:
        # 【帅气/感性】：冷色，低对比
        res = _adjust_saturation(res, 0.8)
        res[:,:,0] = cv2.LUT(res[:,:,0], np.interp(np.arange(256), [0, 255], [0, 230]).astype(np.uint8)) # 减红

    return res