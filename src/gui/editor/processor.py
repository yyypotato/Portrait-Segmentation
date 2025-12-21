import cv2
import numpy as np
from PyQt6.QtCore import QObject
from src.gui.editor.filters import FilterManager

class ImageEditorEngine(QObject):
    def __init__(self):
        super().__init__()
        self.original_image = None # 原始全分辨率图 (RGB)
        self.preview_image = None  # 缩放后的预览图 (RGB)
        self.preview_scale = 1.0
        
        # 参数状态
        self.params = {
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "hue": 0,
            "highlights": 0,
            "shadows": 0,
            "sharpness": 0,
            "vignette": 0
        }
        
        # 新增：当前滤镜
        self.current_filter = "original"

        # LUT 缓存
        self._lut_cache = None
        self._params_cache_key = None

    def load_image(self, image_path, max_preview_size=1920):
        # 读取图片 (处理中文路径)
        stream = np.fromfile(image_path, dtype=np.uint8)
        bgr = cv2.imdecode(stream, cv2.IMREAD_COLOR)
        if bgr is None: return None
        
        self.original_image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        
        # 生成预览图
        h, w = self.original_image.shape[:2]
        if max(h, w) > max_preview_size:
            scale = max_preview_size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            self.preview_image = cv2.resize(self.original_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self.preview_scale = scale
        else:
            self.preview_image = self.original_image.copy()
            self.preview_scale = 1.0
            
        return self.preview_image

    def update_param(self, key, value):
        self.params[key] = value
        # 参数改变，LUT 缓存失效
        if key in ["brightness", "contrast", "highlights", "shadows"]:
            # _lut_cache 会在 _get_combined_lut 中根据 key 自动更新
            pass

    def update_filter(self, filter_name):
        """更新滤镜"""
        self.current_filter = filter_name

    def render(self, use_preview=True):
        """渲染图像管线"""
        if self.original_image is None: return None
        
        # 1. 选择源图像
        src = self.preview_image if use_preview else self.original_image
        img = src.copy()

        # 2. 应用滤镜 (Filter) - 放在最前面作为基调
        img = FilterManager.apply_filter(img, self.current_filter)

        # 3. 应用色相 (Hue)
        img = self.apply_hue(img, self.params["hue"])

        # 4. 应用饱和度 (Saturation)
        img = self.apply_saturation(img, self.params["saturation"])

        # 5. 应用 LUT (亮度/对比度/高光/阴影)
        lut = self._get_combined_lut()
        img = cv2.LUT(img, lut)

        # 6. 应用锐化 (Sharpness)
        if self.params["sharpness"] > 0:
            img = self.apply_sharpness(img, self.params["sharpness"])

        # 7. 应用暗角 (Vignette)
        if self.params["vignette"] > 0:
            img = self.apply_vignette(img, self.params["vignette"])

        return img

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
        x = np.clip(x, 0, 255) / 255.0
        
        shadows = self.params["shadows"] / 100.0
        if shadows != 0:
            mask = 1.0 - np.power(x, 0.5)
            x = x + mask * shadows * 0.5

        highlights = self.params["highlights"] / 100.0
        if highlights != 0:
            mask = np.power(x, 2.0)
            x = x + mask * highlights * 0.5

        x = np.clip(x * 255, 0, 255).astype(np.uint8)
        
        lut = np.dstack((x, x, x))
        self._lut_cache = lut
        self._params_cache_key = current_key
        return lut

    def apply_hue(self, img, shift):
        if shift == 0: return img
        img_float = img.astype(np.float32) / 255.0
        hsv = cv2.cvtColor(img_float, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)
        h_new = np.mod(h + shift, 360.0)
        hsv_new = cv2.merge([h_new, s, v])
        img_new = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2RGB)
        return (np.clip(img_new, 0, 1) * 255).astype(np.uint8)

    def apply_saturation(self, img, saturation):
        if saturation == 0: return img
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        sat_scale = 1.0 + (saturation / 100.0)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_scale, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    def apply_sharpness(self, img, amount):
        # 简单的 USM 锐化
        blur = cv2.GaussianBlur(img, (0, 0), 3)
        img_float = img.astype(np.float32)
        blur_float = blur.astype(np.float32)
        strength = amount / 50.0 # 0-2.0
        sharpened = cv2.addWeighted(img_float, 1.0 + strength, blur_float, -strength, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)

    def apply_vignette(self, img, amount):
        rows, cols = img.shape[:2]
        # 生成径向渐变蒙版
        kernel_x = cv2.getGaussianKernel(cols, cols/2)
        kernel_y = cv2.getGaussianKernel(rows, rows/2)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        
        # 强度控制
        strength = amount / 100.0
        mask = 1.0 - (1.0 - mask) * strength
        
        # 应用蒙版
        img_float = img.astype(np.float32)
        res = img_float * mask[:, :, np.newaxis]
        return np.clip(res, 0, 255).astype(np.uint8)