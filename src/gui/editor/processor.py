import cv2
import numpy as np

class ImageEditorEngine:
    def __init__(self):
        self.original_image = None
        self.preview_image = None
        self.current_image = None
        
        # 初始化所有参数
        self.params = {
            "brightness": 0,    # -100 ~ 100
            "contrast": 0,      # -100 ~ 100
            "saturation": 0,    # -100 ~ 100
            "sharpness": 0,     # 0 ~ 100
            "highlights": 0,    # -100 ~ 100 (高光压制/提亮)
            "shadows": 0,       # -100 ~ 100 (阴影提亮/压暗)
            "hue": 0,           # -180 ~ 180 (色相旋转)
            # 暂时保留之前的，防止报错，后续可整合
            "temperature": 0,
            "tint": 0,
            "vignette": 0,
        }
        self._lut_cache = None
        self._params_cache_key = None

    def load_image(self, image_path, max_preview_size=1920):
        """加载图片并生成预览代理图"""
        stream = np.fromfile(image_path, dtype=np.uint8)
        bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        self.original_image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        
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

        # 1. 基础 LUT (亮度、对比度、高光、阴影)
        # 将这四个最常用的调整合并为一个 LUT 以提升性能
        lut = self._get_combined_lut()
        result = cv2.LUT(src, lut)

        # 2. 色相 (Hue)
        if self.params["hue"] != 0:
            result = self.apply_hue(result, self.params["hue"])

        # 3. 饱和度 (Saturation)
        if self.params["saturation"] != 0:
            result = self.apply_saturation(result, self.params["saturation"])

        # 4. 锐化 (Sharpness)
        if self.params["sharpness"] > 0:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            amount = self.params["sharpness"] / 100.0
            sharp = cv2.filter2D(result, -1, kernel)
            result = cv2.addWeighted(result, 1.0 - amount * 0.2, sharp, amount * 0.2, 0)

        # 5. 其他遗留效果 (色温/暗角) - 暂时保留
        if self.params["temperature"] != 0 or self.params["tint"] != 0:
            result = self.apply_white_balance(result, self.params["temperature"], self.params["tint"])
        if self.params["vignette"] > 0:
            result = self.apply_vignette(result, self.params["vignette"])

        self.current_image = result
        return result

    def _get_combined_lut(self):
        """生成组合查找表：亮度 + 对比度 + 高光 + 阴影"""
        # 缓存键值
        current_key = (self.params["brightness"], self.params["contrast"], 
                       self.params["highlights"], self.params["shadows"])
        
        if self._params_cache_key == current_key and self._lut_cache is not None:
            return self._lut_cache

        x = np.arange(256, dtype=np.float32)
        
        # --- 1. 亮度 ---
        if self.params["brightness"] != 0:
            x = x + self.params["brightness"]

        # --- 2. 对比度 ---
        if self.params["contrast"] != 0:
            contrast = self.params["contrast"]
            factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
            x = factor * (x - 128) + 128

        # --- 3. 高光/阴影 (基于曲线调整) ---
        # 归一化到 0-1
        x = np.clip(x, 0, 255) / 255.0
        
        # 阴影调整 (针对暗部 x < 0.5)
        shadows = self.params["shadows"] / 100.0
        if shadows != 0:
            # 简单的阴影提亮/压暗公式
            # 当 shadows > 0, 提升暗部; shadows < 0, 压暗暗部
            mask = 1.0 - np.power(x, 0.5) # 暗部掩码
            x = x + mask * shadows * 0.5

        # 高光调整 (针对亮部 x > 0.5)
        highlights = self.params["highlights"] / 100.0
        if highlights != 0:
            # 当 highlights < 0, 压制高光 (恢复细节); highlights > 0, 提亮高光
            mask = np.power(x, 2.0) # 亮部掩码
            x = x + mask * highlights * 0.5

        # 反归一化
        x = np.clip(x * 255, 0, 255).astype(np.uint8)
        
        lut = np.dstack((x, x, x))
        self._lut_cache = lut
        self._params_cache_key = current_key
        return lut

    def apply_hue(self, img, shift):
        """
        色相旋转 (高精度版)
        使用 float32 进行计算，H 范围为 0-360，避免 uint8 (0-179) 带来的精度丢失和色彩断层。
        """
        if shift == 0: return img

        # 1. 转换为 float32，范围归一化到 0-1
        # 这一步非常关键，能消除色彩波纹和锯齿
        img_float = img.astype(np.float32) / 255.0

        # 2. 转换到 HSV 空间
        # 注意：对于 float32 图像，OpenCV 的 H 通道范围是 0-360，S/V 是 0-1
        hsv = cv2.cvtColor(img_float, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        # 3. 执行色相偏移
        # shift 输入范围是 -180 到 180
        h_new = h + shift

        # 4. 处理循环 (0-360)
        # 使用模运算处理旋转，比 if/else 更平滑
        h_new = np.mod(h_new, 360.0)
        
        # 5. 合并通道
        hsv_new = cv2.merge([h_new, s, v])

        # 6. 转回 RGB 并还原到 uint8
        img_new = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2RGB)
        # 限制范围并转换回整数
        img_new = (np.clip(img_new, 0, 1) * 255).astype(np.uint8)

        return img_new

    def apply_saturation(self, img, saturation):
        if saturation == 0: return img
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        s = hsv[:, :, 1]
        s = s * (1.0 + saturation / 100.0)
        hsv[:, :, 1] = np.clip(s, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    def apply_white_balance(self, img, temp, tint):
        b, g, r = cv2.split(img)
        if temp > 0:
            r = cv2.add(r, temp); b = cv2.subtract(b, temp)
        else:
            r = cv2.add(r, temp); b = cv2.subtract(b, temp)
        if tint != 0:
            g = cv2.subtract(g, tint)
        return cv2.merge([b, g, r])

    def apply_vignette(self, img, strength):
        rows, cols = img.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols/2)
        kernel_y = cv2.getGaussianKernel(rows, rows/2)
        kernel = kernel_y * kernel_x.T
        mask = 255 * kernel / np.linalg.norm(kernel)
        mask = mask / mask.max()
        strength = strength / 100.0
        mask_layer = 1.0 - (1.0 - mask) * strength
        mask_layer = np.dstack([mask_layer] * 3)
        return (img * mask_layer).astype(np.uint8)

    def render_final(self):
        return self.render(use_preview=True)