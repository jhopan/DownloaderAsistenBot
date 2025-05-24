# src/telegram/keyboard.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.service.downloader_base import get_human_readable_size

def build_platform_menu() -> InlineKeyboardMarkup:
    """Membuat keyboard untuk memilih platform."""
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

def build_resolution_menu(formats: list, platform: str) -> InlineKeyboardMarkup | None:
    """Membuat keyboard untuk memilih resolusi video."""
    if not formats:
        return None

    keyboard = []
    MAX_BUTTONS = 10

    def sort_key(f):
        size = f.get('size_bytes')
        if size is not None:
            return size
        res_str = f['res'][:-1] if f['res'].endswith('p') else f['res']
        if res_str.isdigit():
            return int(res_str)
        return 0

    formats.sort(key=sort_key)

    for f in formats[:MAX_BUTTONS]:
        size_bytes = f.get('size_bytes')

        # Hanya lakukan perbandingan jika size_bytes BUKAN None
        if size_bytes is not None and size_bytes > 1990 * 1024 * 1024:
            continue

        callback_data = f"res_{f['id']}_{platform}"
        size_str = f['size_mb']
        keyboard.append([InlineKeyboardButton(f"{f['res']} ({size_str})", callback_data=callback_data)])

    if not keyboard:
        return None

    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)