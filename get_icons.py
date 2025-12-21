import os
import urllib.request
import ssl

# 1. 确保目录存在
icon_dir = os.path.join("resources", "icons")
label_dir = os.path.join("resources", "images", "labels") # 新增标签素材目录
sticker_root = os.path.join("resources", "images", "stickers") # 新增贴纸目录

# 定义贴纸分类
categories = ["time", "location", "food", "drink", "mood", "text"]

for d in [icon_dir, label_dir, sticker_root]:
    if not os.path.exists(d):
        os.makedirs(d)

for cat in categories:
    cat_dir = os.path.join(sticker_root, cat)
    if not os.path.exists(cat_dir):
        os.makedirs(cat_dir)

# 2. 定义图标映射
base_url = "https://raw.githubusercontent.com/google/material-design-icons/master/png"

# 创建 SSL 上下文，忽略证书验证 (防止某些环境下的 SSL 错误)
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    ssl_context = None

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
    # --- 样式编辑图标 (新增) ---
    "style_bold":     f"{base_url}/editor/format_bold/materialicons/24dp/2x/baseline_format_bold_black_24dp.png",
    "style_italic":   f"{base_url}/editor/format_italic/materialicons/24dp/2x/baseline_format_italic_black_24dp.png",
    "style_shadow":   f"{base_url}/image/filter_drama/materialicons/24dp/2x/baseline_filter_drama_black_24dp.png", # 用云朵代表阴影
    "style_color":    f"{base_url}/image/palette/materialicons/24dp/2x/baseline_palette_black_24dp.png",
    "style_align_left": f"{base_url}/editor/format_align_left/materialicons/24dp/2x/baseline_format_align_left_black_24dp.png",
    "style_align_center": f"{base_url}/editor/format_align_center/materialicons/24dp/2x/baseline_format_align_center_black_24dp.png",
  
    # --- 操作图标 (已修正路径) ---
    "action_check":   f"{base_url}/navigation/check/materialicons/24dp/2x/baseline_check_black_24dp.png", # 修正: action -> navigation
    "action_close":   f"{base_url}/navigation/close/materialicons/24dp/2x/baseline_close_black_24dp.png",

    # --- 贴纸分类图标 (UI) ---
    "cat_time":       f"{base_url}/device/access_time/materialicons/24dp/2x/baseline_access_time_black_24dp.png",
    "cat_location":   f"{base_url}/maps/place/materialicons/24dp/2x/baseline_place_black_24dp.png",
    "cat_food":       f"{base_url}/maps/restaurant/materialicons/24dp/2x/baseline_restaurant_black_24dp.png",
    "cat_drink":      f"{base_url}/maps/local_cafe/materialicons/24dp/2x/baseline_local_cafe_black_24dp.png",
    "cat_mood":       f"{base_url}/social/emoji_emotions/materialicons/24dp/2x/baseline_emoji_emotions_black_24dp.png",
    "cat_text":       f"{base_url}/editor/title/materialicons/24dp/2x/baseline_title_black_24dp.png",

}
labels = {
    "bubble_oval": "https://img.icons8.com/ios-filled/100/ffffff/speech-bubble.png",
    "bubble_rect": "https://img.icons8.com/ios-filled/100/ffffff/comments.png", # 修正: message -> comments
    "bubble_cloud": "https://img.icons8.com/ios-filled/100/ffffff/thinking-bubble.png", # 修正: thought-bubble -> thinking-bubble
    "bubble_round": "https://img.icons8.com/ios-filled/100/ffffff/chat.png",
}

# --- 贴纸素材 (彩色图片) ---
sticker_base = "https://img.icons8.com/color/128"
stickers = {
    "time": [
        ("clock", f"{sticker_base}/clock.png"),
        ("calendar", f"{sticker_base}/calendar.png"),
        ("alarm", f"{sticker_base}/alarm-clock.png"),
        ("watch", f"{sticker_base}/apple-watch.png"), # 修正: watch -> apple-watch
        ("schedule", f"{sticker_base}/planner.png"), # 修正: schedule -> planner
        ("sand_watch", f"{sticker_base}/hourglass.png"), # 修正: sand-watch -> hourglass
        ("time_machine", f"{sticker_base}/time-machine.png"),
    ],
    "location": [
        ("pin", f"{sticker_base}/marker.png"),
        ("map", f"{sticker_base}/map.png"),
        ("globe", f"{sticker_base}/globe.png"),
        ("sign", f"{sticker_base}/signpost.png"),
        ("navigation", f"{sticker_base}/compass.png"), # 修正: navigation -> compass
        ("city", f"{sticker_base}/city.png"),
        ("island", f"{sticker_base}/island-on-water.png"),
    ],
    "food": [
        ("burger", f"{sticker_base}/hamburger.png"),
        ("pizza", f"{sticker_base}/pizza.png"),
        ("taco", f"{sticker_base}/taco.png"),
        ("sushi", f"{sticker_base}/sushi.png"),
        ("fries", f"{sticker_base}/french-fries.png"),
        ("donut", f"{sticker_base}/doughnut.png"),
        ("ice_cream", f"{sticker_base}/ice-cream-cone.png"),
        ("cake", f"{sticker_base}/cake.png"),
    ],
    "drink": [
        ("coffee", f"{sticker_base}/coffee-to-go.png"),
        ("tea", f"{sticker_base}/tea-cup.png"),
        ("cocktail", f"{sticker_base}/cocktail.png"),
        ("soda", f"{sticker_base}/soda-bottle.png"),
        ("beer", f"{sticker_base}/beer.png"),
        ("wine", f"{sticker_base}/wine-glass.png"),
        ("milk", f"{sticker_base}/milk-bottle.png"),
    ],
    "mood": [
        ("smile", f"{sticker_base}/happy.png"),
        ("cool", f"{sticker_base}/cool.png"),
        ("love", f"{sticker_base}/heart-with-arrow.png"),
        ("star", f"{sticker_base}/star.png"),
        ("like", f"{sticker_base}/facebook-like.png"),
        ("fire", f"{sticker_base}/fire-element.png"),
        ("party", f"{sticker_base}/confetti.png"),
    ],
    "text": [
        ("speech", f"{sticker_base}/speech-bubble.png"),
        ("chat", f"{sticker_base}/chat.png"),
        ("quote", f"{sticker_base}/quote-left.png"),
        ("badge", f"{sticker_base}/badge.png"),
        ("sale", f"{sticker_base}/sale.png"),
        ("new", f"{sticker_base}/new.png"),
    ]
}

print("开始下载图标...")
for name, url in icons.items():
    save_path = os.path.join(icon_dir, f"{name}.png")
    if not os.path.exists(save_path):
        try:
            urllib.request.urlretrieve(url, save_path)
            print(f"Downloaded {name}")
        except Exception as e:
            print(f"Error {name}: {e}")

print("开始下载标签素材...")
for name, url in labels.items():
    save_path = os.path.join(label_dir, f"{name}.png")
    if not os.path.exists(save_path):
        try:
            # 伪装 User-Agent 防止 403
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Downloaded {name}")
        except Exception as e:
            print(f"Error {name}: {e}")

print("开始下载贴纸素材...")
for category, items in stickers.items():
    cat_path = os.path.join(sticker_root, category)
    for name, url in items:
        save_path = os.path.join(cat_path, f"{name}.png")
        if not os.path.exists(save_path):
            try:
                # 伪装 User-Agent 防止 403
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Downloaded Sticker [{category}]: {name}")
            except Exception as e:
                print(f"Error Sticker [{category}] {name}: {e}")
print("完成!")