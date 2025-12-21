import os
import urllib.request

# 1. 确保目录存在
save_dir = os.path.join("resources", "icons")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 2. 定义图标映射
base_url = "https://raw.githubusercontent.com/google/material-design-icons/master/png"

icons = {
    # --- 现有图标 ---
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

    # --- 滤镜图标 (已修正路径) ---
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
    # 修正: nightlife 在 places 目录
    "f_moody":        f"{base_url}/maps/nightlife/materialicons/24dp/2x/baseline_nightlife_black_24dp.png",
    "f_valencia":     f"{base_url}/image/wb_iridescent/materialicons/24dp/2x/baseline_wb_iridescent_black_24dp.png",
    "f_memory":       f"{base_url}/action/history/materialicons/24dp/2x/baseline_history_black_24dp.png",
    "f_vintage":      f"{base_url}/image/camera_roll/materialicons/24dp/2x/baseline_camera_roll_black_24dp.png",
    "f_childhood":    f"{base_url}/places/child_care/materialicons/24dp/2x/baseline_child_care_black_24dp.png",
    "f_halo":         f"{base_url}/image/flare/materialicons/24dp/2x/baseline_flare_black_24dp.png",
    "f_sweet":        f"{base_url}/social/cake/materialicons/24dp/2x/baseline_cake_black_24dp.png",
    "f_handsome":     f"{base_url}/social/person/materialicons/24dp/2x/baseline_person_black_24dp.png",
    # 修正: music_note 在 image 目录
    "f_sentimental":  f"{base_url}/image/music_note/materialicons/24dp/2x/baseline_music_note_black_24dp.png",
    "f_individuality":f"{base_url}/action/fingerprint/materialicons/24dp/2x/baseline_fingerprint_black_24dp.png",
    "f_demist":       f"{base_url}/image/dehaze/materialicons/24dp/2x/baseline_dehaze_black_24dp.png",
    # --- 裁剪工具图标 ---
    "rotate_left":    f"{base_url}/image/rotate_left/materialicons/24dp/2x/baseline_rotate_left_black_24dp.png",
    "flip":           f"{base_url}/image/flip/materialicons/24dp/2x/baseline_flip_black_24dp.png", # Material Design 没有直接的 flip icon，通常用 flip_camera 或类似代替，这里暂用 flip
    # 如果 flip 404，可以用这个:
    "flip_alt":       f"{base_url}/image/flip_camera_android/materialicons/24dp/2x/baseline_flip_camera_android_black_24dp.png",
    
    # --- 比例图标 (使用形状代替) ---
    "ratio_custom":   f"{base_url}/image/crop/materialicons/24dp/2x/baseline_crop_black_24dp.png",
    "ratio_full":     f"{base_url}/image/crop_free/materialicons/24dp/2x/baseline_crop_free_black_24dp.png",
    "ratio_1_1":      f"{base_url}/image/crop_square/materialicons/24dp/2x/baseline_crop_square_black_24dp.png",
    "ratio_3_4":      f"{base_url}/image/crop_portrait/materialicons/24dp/2x/baseline_crop_portrait_black_24dp.png",
    "ratio_4_3":      f"{base_url}/image/crop_landscape/materialicons/24dp/2x/baseline_crop_landscape_black_24dp.png",
    "ratio_16_9":     f"{base_url}/hardware/desktop_mac/materialicons/24dp/2x/baseline_desktop_mac_black_24dp.png", # 暂代
    # --- 涂鸦工具图标 (已修正路径) ---
    "doodle_eraser":  f"{base_url}/action/delete/materialicons/24dp/2x/baseline_delete_black_24dp.png",
    "doodle_curve":   f"{base_url}/content/gesture/materialicons/24dp/2x/baseline_gesture_black_24dp.png", # 修正: image -> content
    "doodle_arrow":   f"{base_url}/action/trending_flat/materialicons/24dp/2x/baseline_trending_flat_black_24dp.png",
    "doodle_line":    f"{base_url}/content/remove/materialicons/24dp/2x/baseline_remove_black_24dp.png", # 修正: editor -> content
    "doodle_rect":    f"{base_url}/image/crop_square/materialicons/24dp/2x/baseline_crop_square_black_24dp.png",
    "doodle_circle":  f"{base_url}/image/panorama_fish_eye/materialicons/24dp/2x/baseline_panorama_fish_eye_black_24dp.png",
    # --- 马赛克工具 (新增) ---
    "mosaic_pixel":   f"{base_url}/image/grid_on/materialicons/24dp/2x/baseline_grid_on_black_24dp.png",
    "mosaic_blur":    f"{base_url}/image/blur_on/materialicons/24dp/2x/baseline_blur_on_black_24dp.png",
    "mosaic_triangle":f"{base_url}/image/details/materialicons/24dp/2x/baseline_details_black_24dp.png",
    "mosaic_hexagon": f"{base_url}/image/texture/materialicons/24dp/2x/baseline_texture_black_24dp.png",
    "mosaic_eraser":  f"{base_url}/action/delete/materialicons/24dp/2x/baseline_delete_black_24dp.png",

    # --- 操作图标 (已修正路径) ---
    "action_check":   f"{base_url}/navigation/check/materialicons/24dp/2x/baseline_check_black_24dp.png", # 修正: action -> navigation
    "action_close":   f"{base_url}/navigation/close/materialicons/24dp/2x/baseline_close_black_24dp.png",
}

print(f"开始下载图标到 {save_dir} ...")

for name, url in icons.items():
    try:
        save_path = os.path.join(save_dir, f"{name}.png")
        # 如果文件不存在或大小为0(下载失败残留)，则重新下载
        if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
            print(f"正在下载: {name}.png ...")
            urllib.request.urlretrieve(url, save_path)
        else:
            print(f"跳过已存在: {name}.png")
    except Exception as e:
        print(f"❌ 下载 {name} 失败: {e}")

print("✅ 图标准备就绪！")