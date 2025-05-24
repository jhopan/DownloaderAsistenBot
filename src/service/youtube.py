# src/services/youtube.py
import yt_dlp
import logging
# Ganti impor menjadi src.services
from .downloader_base import get_human_readable_size, get_common_ydl_opts

logger = logging.getLogger(__name__)

async def get_video_formats(url: str) -> list | None:
    ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True}
    formats_list = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'formats' in info:
                for f in info['formats']:
                    if (f.get('ext') == 'mp4' and
                        f.get('vcodec') != 'none' and
                        f.get('acodec') != 'none' and
                        f.get('filesize')):
                        res_note = f.get('format_note', f.get('resolution', 'N/A'))
                        if res_note.isdigit(): res_note += 'p'
                        formats_list.append({
                            'id': f['format_id'], 'res': res_note, 'ext': f['ext'],
                            'size_bytes': f['filesize'],
                            'size_mb': get_human_readable_size(f['filesize']), 'url': url
                        })
                unique_formats = list({v['res']:v for v in formats_list if v['res'] != 'N/A'}.values())
                unique_formats.sort(key=lambda x: int(x['res'][:-1]) if x['res'][:-1].isdigit() else 0, reverse=True)
                return unique_formats[:15]
    except Exception as e:
        logger.error(f"Gagal mengambil format YouTube ({url}): {e}")
        return None
    return None

async def download_video(url: str, format_id: str) -> str | None:
    ydl_opts = get_common_ydl_opts()
    ydl_opts['format'] = f'{format_id}+bestaudio[ext=m4a]/bestaudio/{format_id}/best[ext=mp4]/best'
    ydl_opts['merge_output_format'] = 'mp4'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh YouTube ({url}, format: {format_id}): {e}")
        return None