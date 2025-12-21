import os
import urllib.request

# 1. 确保目录存在
save_dir = os.path.join("resources", "icons")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 2. 定义图标映射
base_url = "https://raw.githubusercontent.com/google/material-design-icons/master/png"

icons = {
    # --- 主菜单图标 ---
    "seg_icon":   f"{base_url}/action/face/materialicons/24dp/2x/baseline_face_black_24dp.png",
    "edit_icon":  f"{base_url}/image/photo_filter/materialicons/24dp/2x/baseline_photo_filter_black_24dp.png",
    # 新增：帮助和退出
    "help_icon":  f"{base_url}/action/help_outline/materialicons/24dp/2x/baseline_help_outline_black_24dp.png",
    "exit_icon":  f"{base_url}/action/exit_to_app/materialicons/24dp/2x/baseline_exit_to_app_black_24dp.png",

    # --- 编辑器图标 ---
    "crop":       f"{base_url}/image/crop/materialicons/24dp/2x/baseline_crop_black_24dp.png",
    "adjust":     f"{base_url}/image/tune/materialicons/24dp/2x/baseline_tune_black_24dp.png",
    "filter":     f"{base_url}/image/filter/materialicons/24dp/2x/baseline_filter_black_24dp.png",
    "doodle":     f"{base_url}/image/brush/materialicons/24dp/2x/baseline_brush_black_24dp.png",
    "mosaic":     f"{base_url}/image/grid_on/materialicons/24dp/2x/baseline_grid_on_black_24dp.png",
    "label":      f"{base_url}/action/label/materialicons/24dp/2x/baseline_label_black_24dp.png",
    "sticker":    f"{base_url}/action/face/materialicons/24dp/2x/baseline_face_black_24dp.png",
    "frame":      f"{base_url}/image/crop_free/materialicons/24dp/2x/baseline_crop_free_black_24dp.png",
    
    # --- 调节工具 ---
    "brightness": f"{base_url}/image/brightness_6/materialicons/24dp/2x/baseline_brightness_6_black_24dp.png",
    "contrast":   f"{base_url}/image/tonality/materialicons/24dp/2x/baseline_tonality_black_24dp.png",
    "saturation": f"{base_url}/action/invert_colors/materialicons/24dp/2x/baseline_invert_colors_black_24dp.png",
    "sharpness":  f"{base_url}/action/change_history/materialicons/24dp/2x/baseline_change_history_black_24dp.png",
    "highlights": f"{base_url}/image/wb_sunny/materialicons/24dp/2x/baseline_wb_sunny_black_24dp.png",
    "shadows":    f"{base_url}/image/brightness_2/materialicons/24dp/2x/baseline_brightness_2_black_24dp.png",
    "hue":        f"{base_url}/image/palette/materialicons/24dp/2x/baseline_palette_black_24dp.png",
}

print(f"开始下载图标到 {save_dir} ...")

for name, url in icons.items():
    try:
        save_path = os.path.join(save_dir, f"{name}.png")
        # 只有文件不存在时才下载，避免重复
        if not os.path.exists(save_path):
            print(f"正在下载: {name}.png ...")
            urllib.request.urlretrieve(url, save_path)
        else:
            print(f"跳过已存在: {name}.png")
    except Exception as e:
        print(f"❌ 下载 {name} 失败: {e}")

print("✅ 图标准备就绪！")