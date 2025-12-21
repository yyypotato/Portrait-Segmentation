import cv2
import numpy as np

class ImageEditorEngine:
    def __init__(self):
        self.original_image = None
        self.preview_image = None
        self.current_image = None
        
        self.params = {
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "temperature": 0, # 新增：色温 (蓝 <-> 黄)
            "tint": 0,        # 新增：色调 (绿 <-> 洋红)
            "vignette": 0,    # 新增：暗角
            "sharpness": 0,
        }
        self._lut_cache = None
        self._params_cache_key = None

    def load_image(self, image_path, max_preview_size=1920):
        """加载图片并生成预览代理图"""
        stream = np.fromfile(image_path, dtype=np.uint8)
        bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        self.original_image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        
        # 生成预览图 (限制最大边长，保证实时性)
        h, w = self.original_image.shape[:2]
        scale = min(max_preview_size / w, max_preview_size / h, 1.0)
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            self.preview_image = cv2.resize(self.original_image, new_size, interpolation=cv2.INTER_AREA)
        else:
            self.preview_image = self.original_image.copy()
            
        self.current_image = self.preview_image.copy()
        return self.current_image

    def update_param(self, key, value):
        self.params[key] = value

    def render(self, use_preview=True):
        src = self.preview_image if use_preview else self.original_image
        if src is None: return None

        # 1. 基础 LUT (亮/对)
        lut = self._get_combined_lut()
        result = cv2.LUT(src, lut)

        # 2. 色温/色调 (White Balance) - 性能优化版
        if self.params["temperature"] != 0 or self.params["tint"] != 0:
            result = self.apply_white_balance(result, self.params["temperature"], self.params["tint"])

        # 3. 饱和度
        if self.params["saturation"] != 0:
            result = self.apply_saturation(result, self.params["saturation"])

        # 4. 锐化
        if self.params["sharpness"] > 0:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            amount = self.params["sharpness"] / 100.0
            sharp = cv2.filter2D(result, -1, kernel)
            result = cv2.addWeighted(result, 1.0 - amount * 0.2, sharp, amount * 0.2, 0)

        # 5. 暗角 (Vignette)
        if self.params["vignette"] > 0:
            result = self.apply_vignette(result, self.params["vignette"])

        self.current_image = result
        return result

    def _get_combined_lut(self):
        # ... (保持之前的 LUT 逻辑不变) ...
        # 检查缓存
        current_key = (self.params["brightness"], self.params["contrast"]) # 只缓存这两个
        if self._params_cache_key == current_key and self._lut_cache is not None:
            return self._lut_cache

        x = np.arange(256, dtype=np.float32)
        
        # 亮度
        if self.params["brightness"] != 0:
            x = x + self.params["brightness"]

        # 对比度
        if self.params["contrast"] != 0:
            contrast = self.params["contrast"]
            factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
            x = factor * (x - 128) + 128

        x = np.clip(x, 0, 255).astype(np.uint8)
        lut = np.dstack((x, x, x))
        
        self._lut_cache = lut
        self._params_cache_key = current_key
        return lut

    def apply_saturation(self, img, saturation):
        """独立处理饱和度 (因为很难合并进 1D LUT)"""
        if saturation == 0: return img
        
        # 转换为 HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        # S 通道调整
        s = hsv[:, :, 1]
        s = s * (1.0 + saturation / 100.0)
        hsv[:, :, 1] = np.clip(s, 0, 255)
        
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    def apply_white_balance(self, img, temp, tint):
        """
        色温: 调整 B/R 通道
        色调: 调整 G 通道
        """
        b, g, r = cv2.split(img)
        
        # 色温: 正值变黄(加R减B)，负值变蓝(加B减R)
        if temp > 0:
            r = cv2.add(r, temp)
            b = cv2.subtract(b, temp)
        else:
            r = cv2.add(r, temp) # temp is negative
            b = cv2.subtract(b, temp)

        # 色调: 正值变洋红(减G)，负值变绿(加G)
        if tint != 0:
            g = cv2.subtract(g, tint)

        return cv2.merge([b, g, r])
    
    def apply_vignette(self, img, strength):
        """添加暗角"""
        rows, cols = img.shape[:2]
        # 生成高斯核
        kernel_x = cv2.getGaussianKernel(cols, cols/2)
        kernel_y = cv2.getGaussianKernel(rows, rows/2)
        kernel = kernel_y * kernel_x.T
        
        # 归一化并反转
        mask = 255 * kernel / np.linalg.norm(kernel)
        mask = mask / mask.max() # 0-1
        
        # 强度控制
        strength = strength / 100.0
        mask_layer = 1.0 - (1.0 - mask) * strength
        mask_layer = np.dstack([mask_layer] * 3)
        
        return (img * mask_layer).astype(np.uint8)

    def render_final(self):
        return self.render(use_preview=True)