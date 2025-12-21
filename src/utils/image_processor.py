import cv2
import numpy as np

class ImageProcessor:
    @staticmethod
    def composite_images(fg_rgb, mask_raw, bg_rgb, 
                         use_harmonize=False, 
                         use_light_wrap=False, 
                         brightness=0, 
                         roi_rects=None, 
                         display_size=None):
        
        h, w = fg_rgb.shape[:2]
        
        # 1. 背景适配
        if bg_rgb.shape[:2] != (h, w):
            bg_resized = cv2.resize(bg_rgb, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            bg_resized = bg_rgb

        # 2. 优化 Mask (消除锯齿和白边)
        mask = mask_raw.copy()
        # 轻微腐蚀边缘 (1像素)，去掉白边
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        # 轻微模糊，让边缘平滑
        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        
        alpha = mask.astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=2)

        # 3. 准备前景
        fg = fg_rgb.copy()

        # --- 改进 A: 温和的色彩一致 (Color Harmonization) ---
        if use_harmonize:
            # 计算环境色
            harmonized = ImageProcessor.color_transfer(bg_resized, fg)
            # 关键修改：只应用 50% 的环境色，保留 50% 原本肤色，防止变色太夸张
            fg = cv2.addWeighted(harmonized, 0.5, fg, 0.5, 0)

        # --- 亮度调整 ---
        if brightness != 0:
            beta = brightness * 2
            lut = np.arange(256, dtype=np.int16) + beta
            lut = np.clip(lut, 0, 255).astype(np.uint8)
            fg = cv2.LUT(fg, lut)

        # --- 基础合成 ---
        fg_float = fg.astype(np.float32)
        bg_float = bg_resized.astype(np.float32)
        
        # 前景 * alpha + 背景 * (1 - alpha)
        composite = fg_float * alpha + bg_float * (1.0 - alpha)

        # --- 改进 B: 自然的环境光溢出 (Light Wrap) ---
        if use_light_wrap:
            # 1. 大范围模糊背景 (模拟漫反射光)
            bg_blur = cv2.GaussianBlur(bg_resized, (51, 51), 0)
            
            # 2. 提取边缘区域 (反转Mask -> 模糊 -> 乘回原Mask)
            mask_inv = 255 - mask
            edge_mask = cv2.GaussianBlur(mask_inv, (21, 21), 0) # 边缘宽度
            # 归一化并限制在前景边缘
            edge_factor = (edge_mask.astype(np.float32) / 255.0) * (mask.astype(np.float32) / 255.0)
            edge_factor = np.expand_dims(edge_factor, axis=2)
            
            # 3. 叠加光效 (使用 Add 模式，让边缘变亮变暖)
            # 强度设为 0.7
            light_layer = bg_blur.astype(np.float32) * edge_factor * 0.7
            composite = cv2.add(composite, light_layer)

        composite = np.clip(composite, 0, 255).astype(np.uint8)

        # --- 局部虚化 ---
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
        """Reinhard 颜色迁移 (保持不变)"""
        source_lab = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target, cv2.COLOR_RGB2LAB).astype(np.float32)

        src_mean, src_std = cv2.meanStdDev(source_lab)
        tgt_mean, tgt_std = cv2.meanStdDev(target_lab)

        src_mean = src_mean.flatten(); src_std = src_std.flatten()
        tgt_mean = tgt_mean.flatten(); tgt_std = tgt_std.flatten()
        tgt_std[tgt_std == 0] = 1e-5

        res_lab = target_lab.copy()
        # L通道只迁移 50%
        l_scale = src_std[0] / tgt_std[0]
        res_lab[:,:,0] = (target_lab[:,:,0] - tgt_mean[0]) * l_scale * 0.5 + src_mean[0] * 0.5 + tgt_mean[0] * 0.5
        
        for i in range(1, 3):
            scale = src_std[i] / tgt_std[i]
            res_lab[:,:,i] = (target_lab[:,:,i] - tgt_mean[i]) * scale + src_mean[i]

        res_lab = np.clip(res_lab, 0, 255).astype(np.uint8)
        return cv2.cvtColor(res_lab, cv2.COLOR_LAB2RGB)