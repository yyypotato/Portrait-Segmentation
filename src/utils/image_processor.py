import cv2
import numpy as np

class ImageProcessor:
    @staticmethod
    def composite_images(fg_rgb, mask_raw, bg_rgb, feather=0, brightness=0, bg_blur=0, roi_rects=None, display_size=None):
        """
        高性能图像合成
        """
        # --- 1. 预处理背景 (最耗时步骤之一) ---
        # 实际项目中，这一步应该在外部缓存，但为了简化逻辑，这里先优化算法
        h, w = fg_rgb.shape[:2]
        
        # 如果背景尺寸不匹配，先缩放 (耗时)
        if bg_rgb.shape[:2] != (h, w):
            bg_resized = cv2.resize(bg_rgb, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            bg_resized = bg_rgb

        # 背景虚化 (耗时)
        # 优化：只有当 blur > 0 时才计算，且使用步长更大的核
        if bg_blur > 0:
            # 放大虚化效果：滑块值 * 2 + 1 -> 滑块值 * 4 + 1
            k_size = int(bg_blur * 4) + 1 
            bg_final = cv2.GaussianBlur(bg_resized, (k_size, k_size), 0)
        else:
            bg_final = bg_resized

        # --- 2. 处理前景 (亮度/对比度) ---
        fg = fg_rgb.copy()
        if brightness != 0:
            # 优化：使用查找表 (LUT) 加速像素运算，比直接加减快且安全
            # 亮度范围扩大：-100 到 100
            beta = brightness * 2 
            # 简单的亮度调整公式
            lut = np.arange(256, dtype=np.int16) + beta
            lut = np.clip(lut, 0, 255).astype(np.uint8)
            fg = cv2.LUT(fg, lut)

        # --- 3. 处理 Mask (羽化) ---
        mask = mask_raw.copy()
        if feather > 0:
            # 优化：先腐蚀一点边缘，再模糊，消除白边效果更好
            # 限制腐蚀大小，防止人没了
            erode_size = max(1, feather // 2)
            kernel = np.ones((erode_size, erode_size), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            
            # 模糊
            k_size = feather * 4 + 1
            mask = cv2.GaussianBlur(mask, (k_size, k_size), 0)
        
        # 归一化 Mask (0.0 - 1.0)
        # 优化：使用 float32 运算比 float64 快
        alpha = mask.astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=2)

        # --- 4. 快速合成 ---
        # 使用 float32 进行矩阵运算
        fg_float = fg.astype(np.float32)
        bg_float = bg_final.astype(np.float32)
        
        composite = cv2.addWeighted(fg_float, 1.0, bg_float, 0.0, 0.0) # 占位
        composite = fg_float * alpha + bg_float * (1.0 - alpha)
        composite = np.clip(composite, 0, 255).astype(np.uint8)

        # --- 5. 局部虚化 (ROI) ---
        if roi_rects and display_size:
            disp_w, disp_h = display_size
            scale_x = w / disp_w
            scale_y = h / disp_h

            for rect in roi_rects:
                x = int(rect.x() * scale_x)
                y = int(rect.y() * scale_y)
                rw = int(rect.width() * scale_x)
                rh = int(rect.height() * scale_y)
                
                # 快速边界检查
                if rw < 1 or rh < 1: continue
                x = max(0, x); y = max(0, y)
                x2 = min(w, x + rw); y2 = min(h, y + rh)
                
                roi = composite[y:y2, x:x2]
                if roi.size > 0:
                    # 强力模糊
                    composite[y:y2, x:x2] = cv2.GaussianBlur(roi, (51, 51), 20)

        return composite