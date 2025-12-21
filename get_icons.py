import os
import urllib.request

# 1. 确保目录存在
save_dir = os.path.join("resources", "icons")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 2. 定义图标映射
base_url = "https://raw.githubusercontent.com/google/material-design-icons/master/png"

icons = {
    # --- 现有图标 (保持不变) ---
    "seg_icon":   f"{base_url}/action/face/materialicons/24dp/2x/baseline_face_black_24dp.png",
    "edit_icon":  f"{base_url}/image/photo_filter/materialicons/24dp/2x/baseline_photo_filter_black_24dp.png",
    "help_icon":  f"{base_url}/action/help_outline/materialicons/24dp/2x/baseline_help_outline_black_24dp.png",
    "exit_icon":  f"{base_url}/action/exit_to_app/materialicons/24dp/2x/baseline_exit_to_app_black_24dp.png",
    "crop":       f"{base_url}/image/crop/materialicons/24dp/2x/baseline_crop_black_24dp.png",
    "adjust":     f"{base_url}/image/tune/materialicons/24dp/2x/baseline_tune_black_24dp.png",
    "filter":     f"{base_url}/image/filter/materialicons/24dp/2x/baseline_filter_black_24dp.png",
    "doodle":     f"{base_url}/image/brush/materialicons/24dp/2x/baseline_brush_black_24dp.png",
    "mosaic":     f"{base_url}/image/grid_on/materialicons/24dp/2x/baseline_grid_on_black_24dp.png",
    "label":      f"{base_url}/action/label/materialicons/24dp/2x/baseline_label_black_24dp.png",
    "sticker":    f"{base_url}/action/face/materialicons/24dp/2x/baseline_face_black_24dp.png",
    "frame":      f"{base_url}/image/crop_free/materialicons/24dp/2x/baseline_crop_free_black_24dp.png",
    "brightness": f"{base_url}/image/brightness_6/materialicons/24dp/2x/baseline_brightness_6_black_24dp.png",
    "contrast":   f"{base_url}/image/tonality/materialicons/24dp/2x/baseline_tonality_black_24dp.png",
    "saturation": f"{base_url}/action/invert_colors/materialicons/24dp/2x/baseline_invert_colors_black_24dp.png",
    "sharpness":  f"{base_url}/action/change_history/materialicons/24dp/2x/baseline_change_history_black_24dp.png",
    "highlights": f"{base_url}/image/wb_sunny/materialicons/24dp/2x/baseline_wb_sunny_black_24dp.png",
    "shadows":    f"{base_url}/image/brightness_2/materialicons/24dp/2x/baseline_brightness_2_black_24dp.png",
    "hue":        f"{base_url}/image/palette/materialicons/24dp/2x/baseline_palette_black_24dp.png",

    # --- 新增：滤镜图标 (26个不重复) ---
    "f_original":     f"{base_url}/image/filter_none/materialicons/24dp/2x/baseline_filter_none_black_24dp.png",
    "f_classic":      f"{base_url}/image/filter_vintage/materialicons/24dp/2x/baseline_filter_vintage_black_24dp.png",
    "f_dawn":         f"{base_url}/image/wb_twilight/materialicons/24dp/2x/baseline_wb_twilight_black_24dp.png",
    "f_pure":         f"{base_url}/social/clean_hands/materialicons/24dp/2x/baseline_clean_hands_black_24dp.png",
    "f_mono":         f"{base_url}/image/filter_b_and_w/materialicons/24dp/2x/baseline_filter_b_and_w_black_24dp.png",
    "f_metallic":     f"{base_url}/action/settings_brightness/materialicons/24dp/2x/baseline_settings_brightness_black_24dp.png",
    "f_blue":         f"{base_url}/image/blur_on/materialicons/24dp/2x/baseline_blur_on_black_24dp.png",
    "f_cool":         f"{base_url}/places/ac_unit/materialicons/24dp/2x/baseline_ac_unit_black_24dp.png",
    "f_netural":      f"{base_url}/image/exposure_zero/materialicons/24dp/2x/baseline_exposure_zero_black_24dp.png",
    "f_blossom":      f"{base_url}/image/filter_drama/materialicons/24dp/2x/baseline_filter_drama_black_24dp.png",
    "f_fair":         f"{base_url}/image/face_retouching_natural/materialicons/24dp/2x/baseline_face_retouching_natural_black_24dp.png",
    "f_pink":         f"{base_url}/action/favorite/materialicons/24dp/2x/baseline_favorite_black_24dp.png",
    "f_caramel":      f"{base_url}/maps/local_cafe/materialicons/24dp/2x/baseline_local_cafe_black_24dp.png",
    "f_soft":         f"{base_url}/image/blur_linear/materialicons/24dp/2x/baseline_blur_linear_black_24dp.png",
    "f_impact":       f"{base_url}/image/flash_on/materialicons/24dp/2x/baseline_flash_on_black_24dp.png",
    "f_moody":        f"{base_url}/image/nightlife/materialicons/24dp/2x/baseline_nightlife_black_24dp.png",
    "f_valencia":     f"{base_url}/image/wb_iridescent/materialicons/24dp/2x/baseline_wb_iridescent_black_24dp.png",
    "f_memory":       f"{base_url}/action/history/materialicons/24dp/2x/baseline_history_black_24dp.png",
    "f_vintage":      f"{base_url}/image/camera_roll/materialicons/24dp/2x/baseline_camera_roll_black_24dp.png",
    "f_childhood":    f"{base_url}/places/child_care/materialicons/24dp/2x/baseline_child_care_black_24dp.png",
    "f_halo":         f"{base_url}/image/flare/materialicons/24dp/2x/baseline_flare_black_24dp.png",
    "f_sweet":        f"{base_url}/social/cake/materialicons/24dp/2x/baseline_cake_black_24dp.png",
    "f_handsome":     f"{base_url}/social/person/materialicons/24dp/2x/baseline_person_black_24dp.png",
    "f_sentimental":  f"{base_url}/av/music_note/materialicons/24dp/2x/baseline_music_note_black_24dp.png",
    "f_individuality":f"{base_url}/action/fingerprint/materialicons/24dp/2x/baseline_fingerprint_black_24dp.png",
    "f_demist":       f"{base_url}/image/dehaze/materialicons/24dp/2x/baseline_dehaze_black_24dp.png",
}

print(f"开始下载图标到 {save_dir} ...")

for name, url in icons.items():
    try:
        save_path = os.path.join(save_dir, f"{name}.png")
        if not os.path.exists(save_path):
            print(f"正在下载: {name}.png ...")
            urllib.request.urlretrieve(url, save_path)
        else:
            print(f"跳过已存在: {name}.png")
    except Exception as e:
        print(f"❌ 下载 {name} 失败: {e}")

print("✅ 图标准备就绪！")