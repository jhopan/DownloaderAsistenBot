# src/services/tiktok.py
import yt_dlp
import logging
import os
from .downloader_base import get_human_readable_size, get_common_ydl_opts
from config import TEMP_DOWNLOAD_PATH

logger = logging.getLogger(__name__)

async def get_video_formats(url: str) -> list | None:
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            size = info.get('filesize') or info.get('filesize_approx')
            return [{'id': 'best', 'res': 'Best Quality',
                     'size_mb': get_human_readable_size(size) if size else 'Unknown',
                     'size_bytes': size, 'url': url, 'has_audio': True}]
    except Exception as e:
        logger.warning(f"Gagal mendapatkan info format video TikTok ({url}): {e}. Menawarkan opsi default.")
        return [{'id': 'best', 'res': 'Best Quality', 'size_mb': 'Unknown',
                 'size_bytes': None, 'url': url, 'has_audio': True}]

async def download_video(url: str, format_id: str = 'best') -> str | None:
    ydl_opts = get_common_ydl_opts()
    ydl_opts['format'] = 'best'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            logger.info(f"TikTok video diunduh: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh video TikTok ({url}): {e}")
        return None

async def get_audio_formats(url: str) -> list | None:
    logger.info(f"get_audio_formats dipanggil untuk TikTok ({url}), akan menawarkan konversi default.")
    return None

async def download_audio(url: str, format_id: str = 'best_video_for_audio_extraction', preferred_format: str = 'mp3') -> str | None:
    output_template = f"{TEMP_DOWNLOAD_PATH}%(title)s_%(id)s_audio.%(ext)s"
    ydl_opts = get_common_ydl_opts(output_template=output_template)
    ydl_opts['format'] = 'bestvideo+bestaudio/best'
    ydl_opts['extract_audio'] = True
    ydl_opts['audioformat'] = preferred_format
    ydl_opts['audioquality'] = '0'
    if preferred_format == 'mp3':
        ydl_opts['postprocessor_args'] = ['-b:a', '192k']
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, current_ext = os.path.splitext(filename)
            expected_filename = f"{base}.{preferred_format}"
            if current_ext != f".{preferred_format}" and os.path.exists(filename):
                if os.path.exists(expected_filename):
                    logger.info(f"File audio target {expected_filename} sudah ada.")
                    filename = expected_filename
                else:
                    try:
                        os.rename(filename, expected_filename)
                        logger.info(f"Audio di-rename dari {filename} ke: {expected_filename}")
                        filename = expected_filename
                    except Exception as e_rename:
                        logger.error(f"Gagal rename audio file dari {filename} ke {expected_filename}: {e_rename}")
            if not os.path.exists(filename):
                 logger.error(f"File audio akhir {filename} tidak ditemukan setelah proses download/konversi.")
                 return None
            logger.info(f"TikTok audio diunduh dan dikonversi: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh/mengonversi audio TikTok ({url}, to: {preferred_format}): {e}")
        return None