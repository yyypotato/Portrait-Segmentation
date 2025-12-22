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
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # 【关键修复1】确保宽度是 4 的倍数
            # QImage 默认要求每行字节数 4 字节对齐，如果宽度不对齐，显示时会花屏/倾斜
            new_w = (new_w // 4) * 4
            if new_w <= 0: new_w = 4
            
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            
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
            # 使用 (x - 127.5) * f + 127.5 公式，保持中间灰度不变
            f = 1.0 + self.params["contrast"] / 100.0
            img = (img - 127.5) * f + 127.5

        # 【关键修复】在转 uint8 之前必须 clip，否则负数或 >255 的数会回绕 (例如 -5 变成 251)
        # 这会导致调节对比度时出现杂色噪点
        img = np.clip(img, 0, 255).astype(np.uint8)

        # 饱和度 & 色相 (合并在 HSV 空间处理)
        if self.params["saturation"] != 0 or self.params["hue"] != 0:
            hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
            
            # 色相
            if self.params["hue"] != 0:
                # OpenCV H 范围 0-180
                hsv[:, :, 0] = (hsv[:, :, 0] + (self.params["hue"] / 2.0)) % 180
            
            # 饱和度
            if self.params["saturation"] != 0:
                scale = 1.0 + self.params["saturation"] / 100.0
                hsv[:, :, 1] *= scale
            
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # 转回 float32 继续处理锐化
        img = img.astype(np.float32)


        # 锐化 (USM)
        if self.params["sharpness"] > 0:
            blur = cv2.GaussianBlur(img, (0, 0), 3)
            img = cv2.addWeighted(img, 1.5 + self.params["sharpness"]/100.0, blur, -0.5 - self.params["sharpness"]/100.0, 0)

        # 【关键修复2】处理完所有数值计算后，必须转回 uint8
        # 如果这里返回 float32，QImage 显示时就会全是噪点/花屏
        img = np.clip(img, 0, 255).astype(np.uint8)

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

        # 【关键修复3】确保返回连续内存数组，防止 QImage 显示异常
        return np.ascontiguousarray(img)

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
    def generate_mosaic_image(self, img, style="pixel"):
        """
        生成全图的马赛克效果
        :param img: 原图 (numpy RGB)
        :param style: 'pixel', 'blur', 'triangle', 'hexagon'
        """
        h, w = img.shape[:2]
        
        if style == "pixel":
            # 像素风：缩小再放大
            scale = 0.05 # 像素块大小
            small = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            
        elif style == "blur":
            # 毛玻璃：高斯模糊
            ksize = max(1, int(min(w, h) * 0.05)) | 1 # 奇数
            return cv2.GaussianBlur(img, (ksize, ksize), 0)
            
        elif style == "triangle":
            # 模拟三角/晶格 (通过金字塔均值漂移或简单的多边形模拟，这里用简单的双边滤波+像素化模拟)
            # 先模糊
            blur = cv2.bilateralFilter(img, 9, 75, 75)
            # 再像素化
            scale = 0.08
            small = cv2.resize(blur, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            
        elif style == "hexagon":
            # 模拟纹理 (这里简单用中值模糊模拟油画感/去噪点)
            ksize = max(1, int(min(w, h) * 0.02)) | 1
            return cv2.medianBlur(img, ksize)
            
        return img

    def apply_mosaic_mask(self, original_img, mosaic_img, mask_qimage):
        """
        将马赛克图通过遮罩应用到原图
        """
        if mask_qimage.isNull(): return original_img
        
        # 1. Mask QImage -> numpy
        ptr = mask_qimage.bits()
        ptr.setsize(mask_qimage.height() * mask_qimage.width() * 4)
        mask_arr = np.frombuffer(ptr, np.uint8).reshape((mask_qimage.height(), mask_qimage.width(), 4))
        
        # 提取 Alpha 通道作为权重 (0-1)
        alpha = mask_arr[:, :, 3].astype(float) / 255.0
        
        # 确保尺寸匹配
        th, tw = original_img.shape[:2]
        if alpha.shape[:2] != (th, tw):
            alpha = cv2.resize(alpha, (tw, th), interpolation=cv2.INTER_LINEAR)
            
        alpha = np.expand_dims(alpha, axis=2)
        
        # 混合: out = mosaic * alpha + original * (1 - alpha)
        # 确保 mosaic_img 尺寸匹配
        if mosaic_img.shape[:2] != (th, tw):
            mosaic_img = cv2.resize(mosaic_img, (tw, th))
            
        out = mosaic_img.astype(float) * alpha + original_img.astype(float) * (1.0 - alpha)
        
        return np.clip(out, 0, 255).astype(np.uint8)
    
    def apply_label_layer(self, label_qimage, current_bg_img):
        """
        将标签层 (QImage) 叠加到背景图 (numpy array)
        """
        if label_qimage.isNull(): return current_bg_img
        
        # 1. QImage -> numpy (RGBA)
        ptr = label_qimage.bits()
        ptr.setsize(label_qimage.height() * label_qimage.width() * 4)
        label_arr = np.frombuffer(ptr, np.uint8).reshape((label_qimage.height(), label_qimage.width(), 4))
        
        # 2. 提取 Alpha 通道
        alpha = label_arr[:, :, 3].astype(float) / 255.0
        overlay_rgb = label_arr[:, :, :3]
        
        # 3. 调整尺寸以匹配 (防止尺寸不一致报错)
        h, w = current_bg_img.shape[:2]
        if alpha.shape[:2] != (h, w):
            alpha = cv2.resize(alpha, (w, h))
            overlay_rgb = cv2.resize(overlay_rgb, (w, h))
            
        alpha = np.expand_dims(alpha, axis=2)
        
        # 4. 混合
        # out = overlay * alpha + bg * (1 - alpha)
        out = overlay_rgb.astype(float) * alpha + current_bg_img.astype(float) * (1.0 - alpha)
        
        return np.clip(out, 0, 255).astype(np.uint8)