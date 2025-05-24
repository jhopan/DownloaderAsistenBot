# src/services/instagram.py
import yt_dlp
import logging
from .downloader_base import get_human_readable_size, get_common_ydl_opts
from config import IG_USERNAME, IG_PASSWORD

logger = logging.getLogger(__name__)

async def get_video_formats(url: str) -> list | None:
    ydl_opts = {'quiet': True, 'no_warnings': True}
    if IG_USERNAME and IG_PASSWORD:
        ydl_opts['username'] = IG_USERNAME
        ydl_opts['password'] = IG_PASSWORD
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            size = info.get('filesize') or info.get('filesize_approx')
            return [{'id': 'best', 'res': 'Best Quality', 'size_mb': get_human_readable_size(size) if size else 'Unknown', 'size_bytes': size, 'url': url}]
    except Exception:
        return [{'id': 'best', 'res': 'Best Quality', 'size_mb': 'Unknown', 'size_bytes': None, 'url': url}]

async def download_video(url: str, format_id: str = 'best') -> str | None:
    ydl_opts = get_common_ydl_opts()
    ydl_opts['format'] = 'best'
    if IG_USERNAME and IG_PASSWORD:
        ydl_opts['username'] = IG_USERNAME
        ydl_opts['password'] = IG_PASSWORD
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh Instagram ({url}): {e}")
        return None