import cv2
import numpy as np

class FilterManager:
    """
    滤镜管理器
    提供多种风格的滤镜算法
    """
    
    @staticmethod
    def apply_filter(img, filter_name):
        if filter_name == "original":
            return img
        
        # 获取滤镜函数
        method_name = f"_filter_{filter_name}"
        if hasattr(FilterManager, method_name):
            return getattr(FilterManager, method_name)(img)
        return img

    # --- 基础工具函数 ---
    @staticmethod
    def _apply_lut(img, curve_b, curve_g, curve_r):
        """应用通道曲线"""
        lut = np.zeros((256, 1, 3), dtype=np.uint8)
        lut[:, 0, 0] = np.clip(curve_b, 0, 255)
        lut[:, 0, 1] = np.clip(curve_g, 0, 255)
        lut[:, 0, 2] = np.clip(curve_r, 0, 255)
        return cv2.LUT(img, lut)

    @staticmethod
    def _color_overlay(img, color, intensity=0.2):
        """叠加颜色层"""
        overlay = np.full(img.shape, color, dtype=np.uint8)
        return cv2.addWeighted(img, 1 - intensity, overlay, intensity, 0)

    # --- 具体滤镜实现 ---

    @staticmethod
    def _filter_classic(img):
        # 经典：微暖，稍高对比度
        x = np.arange(256)
        return FilterManager._apply_lut(img, x*0.95, x, x*1.05)

    @staticmethod
    def _filter_dawn(img):
        # 晨光：紫色调阴影，暖色高光
        return FilterManager._color_overlay(img, (100, 80, 120), 0.15)

    @staticmethod
    def _filter_pure(img):
        # 纯净：略微降低饱和度，提高亮度
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] *= 0.8 # 降饱和
        hsv[:, :, 2] *= 1.1 # 提亮
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    @staticmethod
    def _filter_mono(img):
        # 黑白
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    @staticmethod
    def _filter_metallic(img):
        # 金属：高对比度黑白
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    @staticmethod
    def _filter_blue(img):
        # 蓝调
        return FilterManager._color_overlay(img, (255, 100, 0), 0.2) # BGR: Blue is first channel in overlay logic if using BGR, but here input is RGB. 
        # Note: Input img is RGB. Overlay color should be RGB. (0, 100, 255) for Blue.
        # Let's stick to RGB logic.
        return FilterManager._color_overlay(img, (0, 100, 255), 0.15)

    @staticmethod
    def _filter_cool(img):
        # 清凉：偏青色
        x = np.arange(256)
        return FilterManager._apply_lut(img, x*1.1, x*1.05, x*0.9) # B, G, R (RGB order: R is last) -> R=0.9, G=1.05, B=1.1

    @staticmethod
    def _filter_netural(img):
        # 中性：低对比度
        img_float = img.astype(np.float32)
        return np.clip((img_float - 128) * 0.8 + 128, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_blossom(img):
        # 桃花：粉色调
        return FilterManager._color_overlay(img, (255, 180, 200), 0.15)

    @staticmethod
    def _filter_fair(img):
        # 白皙：提亮肤色 (简单提亮)
        img_float = img.astype(np.float32)
        return np.clip(img_float * 1.1 + 10, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_pink(img):
        # 粉嫩
        return FilterManager._color_overlay(img, (255, 192, 203), 0.2)

    @staticmethod
    def _filter_caramel(img):
        # 焦糖：棕褐色
        sepia_filter = np.array([[0.393, 0.769, 0.189],
                                 [0.349, 0.686, 0.168],
                                 [0.272, 0.534, 0.131]])
        img_sepia = cv2.transform(img, sepia_filter)
        return np.clip(img_sepia, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_soft(img):
        # 柔和：高斯模糊叠加
        blur = cv2.GaussianBlur(img, (15, 15), 0)
        return cv2.addWeighted(img, 0.7, blur, 0.3, 0)

    @staticmethod
    def _filter_impact(img):
        # 冲击：高对比度，高饱和
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] *= 1.3
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        img_sat = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        img_float = img_sat.astype(np.float32)
        return np.clip((img_float - 128) * 1.3 + 128, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_moody(img):
        # 情绪：暗调，低饱和
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] *= 0.6 # 降饱和
        hsv[:, :, 2] *= 0.8 # 降亮度
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    @staticmethod
    def _filter_valencia(img):
        # 瓦伦西亚：暖色，褪色感
        x = np.arange(256)
        img = FilterManager._apply_lut(img, x*0.9, x, x*1.1) # 提红
        return np.clip(img.astype(np.float32) + 20, 0, 255).astype(np.uint8) # 整体提亮

    @staticmethod
    def _filter_memory(img):
        # 回忆：绿色调，低对比
        return FilterManager._color_overlay(img, (100, 120, 80), 0.2)

    @staticmethod
    def _filter_vintage(img):
        # 复古：黄色调，暗角 (暗角在 processor 中有单独实现，这里只做色调)
        return FilterManager._color_overlay(img, (240, 230, 140), 0.2)

    @staticmethod
    def _filter_childhood(img):
        # 童年：暖洋洋
        return FilterManager._color_overlay(img, (255, 220, 180), 0.15)

    @staticmethod
    def _filter_halo(img):
        # 光晕：中心亮
        rows, cols = img.shape[:2]
        # 简单模拟：整体提亮 + 边缘压暗（类似暗角反向）
        return np.clip(img.astype(np.float32) * 1.1, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_sweet(img):
        # 甜美：粉紫
        return FilterManager._color_overlay(img, (255, 200, 255), 0.15)

    @staticmethod
    def _filter_handsome(img):
        # 帅气：冷色调，高对比
        x = np.arange(256)
        img = FilterManager._apply_lut(img, x*1.1, x*1.0, x*0.95)
        img_float = img.astype(np.float32)
        return np.clip((img_float - 128) * 1.1 + 128, 0, 255).astype(np.uint8)

    @staticmethod
    def _filter_sentimental(img):
        # 感性：黑白+噪点 (简化为低饱和度)
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] *= 0.3
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    @staticmethod
    def _filter_individuality(img):
        # 个性：反转色 (负片)
        return 255 - img

    @staticmethod
    def _filter_demist(img):
        # 去雾：简单模拟（提高对比度，降低亮度，增加饱和度）
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] *= 1.2 # 增加饱和
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        # 增加对比度
        img_float = img.astype(np.float32)
        return np.clip((img_float - 128) * 1.2 + 128, 0, 255).astype(np.uint8)