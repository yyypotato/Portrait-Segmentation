import cv2
import numpy as np

class ImageProcessor:
    @staticmethod
    def composite_images(fg_rgb, mask_raw, bg_rgb, 
                         use_harmonize=False,  # 新增：自动色彩一致
                         use_light_wrap=False, # 新增：环境光溢出
                         brightness=0, 
                         roi_rects=None, 
                         display_size=None):
        
        h, w = fg_rgb.shape[:2]
        
        # 1. 背景适配
        if bg_rgb.shape[:2] != (h, w):
            bg_resized = cv2.resize(bg_rgb, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            bg_resized = bg_rgb

        # 2. 准备前景和 Mask
        fg = fg_rgb.copy()
        mask = mask_raw.copy()
        
        # 基础羽化 (保留一点点，防止锯齿，但不需要用户调了)
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        alpha = mask.astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=2)

        # --- 核心改进 A: 自动色彩一致 (Color Harmonization) ---
        if use_harmonize:
            # 使用 Reinhard 颜色迁移算法，将背景的色调统计特征应用到前景
            fg = ImageProcessor.color_transfer(bg_resized, fg)

        # --- 基础亮度调整 ---
        if brightness != 0:
            beta = brightness * 2
            lut = np.arange(256, dtype=np.int16) + beta
            lut = np.clip(lut, 0, 255).astype(np.uint8)
            fg = cv2.LUT(fg, lut)

        # --- 合成 ---
        fg_float = fg.astype(np.float32)
        bg_float = bg_resized.astype(np.float32)
        
        # 标准 Alpha 混合
        composite = fg_float * alpha + bg_float * (1.0 - alpha)

        # --- 核心改进 B: 环境光溢出 (Light Wrap) ---
        if use_light_wrap:
            # 逻辑：模糊背景 -> 提取前景边缘 -> 将模糊背景叠加到边缘
            # 1. 模糊背景
            bg_blur = cv2.GaussianBlur(bg_resized, (21, 21), 0)
            
            # 2. 制作边缘 Mask (反转 Mask 后模糊，再与原 Mask 相乘)
            mask_inv = 255 - mask
            edge_mask = cv2.GaussianBlur(mask_inv, (15, 15), 0) # 边缘宽度
            edge_mask = (edge_mask.astype(np.float32) / 255.0) * (mask.astype(np.float32) / 255.0)
            edge_mask = np.expand_dims(edge_mask, axis=2)
            
            # 3. 叠加 (Screen 模式或直接加权)
            # 这里使用简单的加权，让背景光“吃”进前景边缘
            wrap_layer = bg_blur.astype(np.float32)
            composite = composite * (1.0 - edge_mask * 0.6) + wrap_layer * (edge_mask * 0.6)

        composite = np.clip(composite, 0, 255).astype(np.uint8)

        # --- 局部虚化 (保持不变) ---
        if roi_rects and display_size:
            disp_w, disp_h = display_size
            scale_x = w / disp_w
            scale_y = h / disp_h
            for rect in roi_rects:
                x = int(rect.x() * scale_x); y = int(rect.y() * scale_y)
                rw = int(rect.width() * scale_x); rh = int(rect.height() * scale_y)
                if rw < 1 or rh < 1: continue
                x = max(0, x); y = max(0, y)
                x2 = min(w, x + rw); y2 = min(h, y + rh)
                roi = composite[y:y2, x:x2]
                if roi.size > 0:
                    composite[y:y2, x:x2] = cv2.GaussianBlur(roi, (51, 51), 20)

        return composite

    @staticmethod
    def color_transfer(source, target):
        """
        Reinhard 颜色迁移算法：让 target(前景) 拥有 source(背景) 的色调
        """
        # 转换到 LAB 空间 (L=亮度, A=红绿, B=黄蓝)
        source_lab = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_RGB2LAB).astype(np.float32)

        # 计算均值和标准差
        src_mean, src_std = cv2.meanStdDev(source_lab)
        tgt_mean, tgt_std = cv2.meanStdDev(target_lab)

        src_mean = src_mean.flatten()
        src_std = src_std.flatten()
        tgt_mean = tgt_mean.flatten()
        tgt_std = tgt_std.flatten()

        # 避免除零
        tgt_std[tgt_std == 0] = 1e-5

        # 核心公式：(x - mean_tgt) * (std_src / std_tgt) + mean_src
        # 但为了不让肤色变得太奇怪，我们通常减弱 L 通道(亮度)的影响，主要迁移 A/B 通道(色调)
        
        res_lab = target_lab.copy()
        
        # L 通道 (亮度)：只迁移 50% 的特征，保留原图光影
        l_scale = src_std[0] / tgt_std[0]
        res_lab[:,:,0] = (target_lab[:,:,0] - tgt_mean[0]) * l_scale * 0.5 + src_mean[0] * 0.5 + tgt_mean[0] * 0.5
        
        # A/B 通道 (色度)：完全迁移
        for i in range(1, 3):
            scale = src_std[i] / tgt_std[i]
            res_lab[:,:,i] = (target_lab[:,:,i] - tgt_mean[i]) * scale + src_mean[i]

        res_lab = np.clip(res_lab, 0, 255).astype(np.uint8)
        return cv2.cvtColor(res_lab, cv2.COLOR_LAB2RGB)