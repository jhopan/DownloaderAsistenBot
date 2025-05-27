# src/services/downloader_base.py
import logging
from config import TEMP_DOWNLOAD_PATH

logger = logging.getLogger(__name__)

def get_human_readable_size(size_bytes):
    """Mengubah byte menjadi format yang mudah dibaca (MB atau GB)."""
    if size_bytes is None: return "N/A"
    try:
        size_bytes = int(size_bytes)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb < 1024:
            return f"{size_mb:.2f} MB"
        else:
            return f"{size_mb / 1024:.2f} GB"
    except (ValueError, TypeError):
        return "N/A"

def get_common_ydl_opts(output_template=None):
    """Mengembalikan opsi yt-dlp yang umum digunakan untuk unduhan."""
    if output_template is None:
        output_template = f"{TEMP_DOWNLOAD_PATH}%(title)s_%(id)s.%(ext)s"

    return {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 1990 * 1024 * 1024, # Batas ukuran file unduhan ~1.99GB
        'noplaylist': True,
        'nocheckcertificate': True,
        'retries': 3,
        'fragment_retries': 3,
    }
