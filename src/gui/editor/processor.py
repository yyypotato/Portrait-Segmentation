import cv2
import numpy as np
from PyQt6.QtGui import QImage
from .filters import apply_filter

class ImageEditorEngine:
    def __init__(self):
        self.original_image = None # 原始全尺寸图 (numpy array)
        self.preview_image = None  # 用于显示的图 (可能被缩放)
        
        # 调节参数
        self.params = {
            "brightness": 0, "contrast": 0, "saturation": 0, 
            "sharpness": 0, "highlights": 0, "shadows": 0, "hue": 0
        }
        
        # 几何参数
        self.geo_params = {
            "rotate_angle": 0, # 自由旋转 (-45~45)
            "rotate_90": 0,    # 90度旋转次数 (0~3)
            "flip_h": False,   # 水平翻转
            "crop_rect": None  # (x, y, w, h) 归一化坐标
        }
        
        self.current_filter = "original"

    def load_image(self, path):
        # 读取图片，处理中文路径
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None: return None
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 限制最大尺寸以保证性能 (例如 2000px)
        h, w = img.shape[:2]
        max_dim = 2000
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
            
        self.original_image = img
        self.preview_image = img.copy()
        
        # 重置参数
        for k in self.params: self.params[k] = 0
        self.geo_params = {"rotate_angle": 0, "rotate_90": 0, "flip_h": False, "crop_rect": None}
        self.current_filter = "original"
        
        return self.preview_image

    def update_param(self, key, value):
        if key in self.params:
            self.params[key] = value

    def update_geo_param(self, key, value):
        if key in self.geo_params:
            self.geo_params[key] = value

    def update_filter(self, filter_name):
        self.current_filter = filter_name

    def render(self, use_preview=True, include_crop=True):
        """
        渲染图像处理管线
        1. 基础调整 (亮度/对比度等)
        2. 滤镜
        3. 几何变换 (旋转/翻转)
        4. 裁剪 (可选)
        """
        src = self.preview_image if use_preview and self.preview_image is not None else self.original_image
        if src is None: return None
        
        img = src.astype(np.float32)
        
        # 1. 基础调整
        # 亮度
        if self.params["brightness"] != 0:
            img += self.params["brightness"]
            
        # 对比度
        if self.params["contrast"] != 0:
            alpha = 1.0 + self.params["contrast"] / 100.0
            img = cv2.addWeighted(img, alpha, img, 0, 128 * (1 - alpha))
            
        # 饱和度
        if self.params["saturation"] != 0:
            hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 1] *= (1.0 + self.params["saturation"] / 100.0)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

        # 色相
        if self.params["hue"] != 0:
            hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 0] = (hsv[:, :, 0] + self.params["hue"]) % 180
            img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

        img = np.clip(img, 0, 255).astype(np.uint8)

        # 锐化 (USM)
        if self.params["sharpness"] > 0:
            blur = cv2.GaussianBlur(img, (0, 0), 3)
            img = cv2.addWeighted(img, 1.5 + self.params["sharpness"]/100.0, blur, -0.5 - self.params["sharpness"]/100.0, 0)

        # 2. 滤镜
        if self.current_filter != "original":
            img = apply_filter(img, self.current_filter)

        # 3. 几何变换
        # 90度旋转
        rot90 = self.geo_params["rotate_90"] % 4
        if rot90 == 1: img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rot90 == 2: img = cv2.rotate(img, cv2.ROTATE_180)
        elif rot90 == 3: img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        
        # 水平翻转
        if self.geo_params["flip_h"]:
            img = cv2.flip(img, 1)
            
        # 自由旋转
        angle = self.geo_params["rotate_angle"]
        if angle != 0:
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

        # 4. 裁剪
        if include_crop and self.geo_params["crop_rect"]:
            nx, ny, nw, nh = self.geo_params["crop_rect"]
            h, w = img.shape[:2]
            x, y = int(nx * w), int(ny * h)
            cw, ch = int(nw * w), int(nh * h)
            
            # 边界检查
            x = max(0, x)
            y = max(0, y)
            cw = min(w - x, cw)
            ch = min(h - y, ch)
            
            if cw > 0 and ch > 0:
                img = img[y:y+ch, x:x+cw]

        return img

    def apply_doodle_layer(self, doodle_pixmap, current_display_img):
        """
        将涂鸦层 (QPixmap) 合并到当前图像 (numpy array)
        :param doodle_pixmap: 涂鸦层
        :param current_display_img: 当前显示的图像 (numpy RGB)
        :return: 合并后的图像 (numpy RGB)
        """
        if doodle_pixmap.isNull(): return current_display_img
        
        # 1. QPixmap -> QImage -> numpy
        # 修复：使用 PyQt6 枚举 QImage.Format.Format_RGBA8888
        qimg = doodle_pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        
        w, h = qimg.width(), qimg.height()
        ptr = qimg.bits()
        ptr.setsize(h * w * 4)
        doodle_arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        
        # 2. 调整大小以匹配目标图像 (如果需要)
        th, tw = current_display_img.shape[:2]
        if (h, w) != (th, tw):
            doodle_arr = cv2.resize(doodle_arr, (tw, th), interpolation=cv2.INTER_LINEAR)
            
        # 3. Alpha 混合
        # 分离通道
        r, g, b, a = cv2.split(doodle_arr)
        foreground = cv2.merge((r, g, b)) 
        alpha = a.astype(float) / 255.0
        alpha = np.expand_dims(alpha, axis=2)
        
        background = current_display_img.astype(float)
        foreground = foreground.astype(float)
        
        # 混合: out = fg * alpha + bg * (1 - alpha)
        out = foreground * alpha + background * (1.0 - alpha)
        
        return np.clip(out, 0, 255).astype(np.uint8)