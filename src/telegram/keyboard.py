# src/telegram/keyboard.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.service.downloader_base import get_human_readable_size

def build_platform_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("YouTube", callback_data="platform_youtube"),
            InlineKeyboardButton("Instagram", callback_data="platform_instagram"),
        ],
        [
            InlineKeyboardButton("TikTok", callback_data="platform_tiktok"),
            InlineKeyboardButton("Lainnya", callback_data="platform_other"),
        ],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_download_type_menu(platform: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🎬 Video", callback_data=f"dltype_video_{platform}"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"dltype_audio_{platform}"),
        ],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_video_resolution_menu(formats: list, platform: str) -> InlineKeyboardMarkup | None:
    if not formats: return None
    keyboard = []
    MAX_BUTTONS = 10
    def sort_key(f):
        size = f.get('size_bytes')
        if size is not None: return size
        res_str = f['res'][:-1] if f['res'].endswith('p') else f['res']
        if res_str.isdigit(): return int(res_str)
        return 0
    formats.sort(key=sort_key)
    for f in formats[:MAX_BUTTONS]:
        size_bytes = f.get('size_bytes')
        if size_bytes is not None and size_bytes > 1990 * 1024 * 1024: continue
        callback_data = f"res_video_{f['id']}_{platform}"
        size_str = f['size_mb']
        keyboard.append([InlineKeyboardButton(f"{f['res']} ({size_str})", callback_data=callback_data)])
    if not keyboard: return None
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def build_audio_quality_menu(formats: list | None, platform: str) -> InlineKeyboardMarkup | None:
    keyboard = []
    MAX_BUTTONS = 10
    
    keyboard.append([InlineKeyboardButton("🎵 Kualitas Terbaik (MP3)", callback_data=f"res_audio_best-mp3_{platform}")])

    if formats:
        formats.sort(key=lambda x: x.get('abr') if x.get('abr') is not None else 0, reverse=True)
        count = 0
        for f in formats:
            if count >= MAX_BUTTONS -1 : break
            format_id = f.get('id', 'unknown')
            note = f.get('note', 'Audio')
            ext = f.get('ext', 'N/A').lower()
            abr = f.get('abr')
            display_text = f"{note} ({ext.upper()})"
            if abr: display_text += f" ~{abr}kbps"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=f"res_audio_{format_id}-{ext}_{platform}")])
            count += 1
            
    if not keyboard: return None
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)