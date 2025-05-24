# src/services/tiktok.py
import yt_dlp
import logging
from .downloader_base import get_human_readable_size, get_common_ydl_opts

logger = logging.getLogger(__name__)

async def get_video_formats(url: str) -> list | None:
    ydl_opts = {'quiet': True, 'no_warnings': True}
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
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh TikTok ({url}): {e}")
        return None