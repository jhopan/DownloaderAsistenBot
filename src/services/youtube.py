# src/services/youtube.py
import yt_dlp
import logging
import os
import re
from service.downloader_base import get_human_readable_size, get_common_ydl_opts
from config import TEMP_DOWNLOAD_PATH

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
                        (f.get('filesize') or f.get('filesize_approx'))):
                        res_note = f.get('format_note', f.get('resolution', 'N/A'))
                        if res_note.isdigit(): res_note += 'p'
                        size_bytes = f.get('filesize') or f.get('filesize_approx')
                        formats_list.append({
                            'id': f['format_id'], 'res': res_note, 'ext': f['ext'],
                            'size_bytes': size_bytes,
                            'size_mb': get_human_readable_size(size_bytes), 'url': url,
                            'has_audio': f.get('acodec') != 'none'
                        })
                if not formats_list: return None
                unique_formats_dict = {}
                for fmt in formats_list:
                    if fmt['res'] != 'N/A':
                        if fmt['res'] not in unique_formats_dict or \
                           (fmt['has_audio'] and not unique_formats_dict[fmt['res']]['has_audio']) or \
                           (fmt['has_audio'] == unique_formats_dict[fmt['res']]['has_audio'] and \
                            (fmt.get('size_bytes') or 0) > (unique_formats_dict[fmt['res']].get('size_bytes') or 0)):
                            unique_formats_dict[fmt['res']] = fmt
                unique_formats = list(unique_formats_dict.values())
                unique_formats.sort(key=lambda x: int(x['res'][:-1]) if x['res'][:-1].isdigit() else 0, reverse=True)
                return unique_formats[:15]
            else:
                logger.warning(f"Kunci 'formats' tidak ditemukan dalam info YouTube untuk URL: {url}")
                return None
    except Exception as e:
        logger.error(f"Gagal mengambil format video YouTube ({url}): {e}", exc_info=True)
        return None

async def download_video(url: str, format_id: str) -> str | None:
    ydl_opts = get_common_ydl_opts()
    ydl_opts['format'] = f'{format_id}+bestaudio[ext=m4a]/bestaudio[ext=m4a]/{format_id}/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    ydl_opts['merge_output_format'] = 'mp4'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            logger.info(f"YouTube video diunduh: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh video YouTube ({url}, format: {format_id}): {e}", exc_info=True)
        return None

async def get_audio_formats(url: str) -> list | None:
    ydl_opts = {'quiet': True, 'no_warnings': True, 'noplaylist': True}
    audio_formats_list = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        abr = f.get('abr')
                        ext = f.get('ext')
                        format_id = f.get('format_id')
                        note = f.get('format_note', f.get('format', 'Audio'))
                        if abr is None and isinstance(note, str):
                            match = re.search(r'(\d+)k', note)
                            if match:
                                try: abr = int(match.group(1)[:-1])
                                except ValueError: pass
                        audio_formats_list.append({
                            'id': format_id, 'note': note, 'ext': ext, 'abr': abr,
                            'size_bytes': f.get('filesize') or f.get('filesize_approx'),
                            'size_mb': get_human_readable_size(f.get('filesize') or f.get('filesize_approx'))
                        })
                if not audio_formats_list:
                    logger.warning(f"Tidak ada format audio murni yang cocok ditemukan untuk YouTube ({url}).")
                    return None
                seen_ids = set()
                unique_audio_formats = []
                for item in audio_formats_list:
                    if item['id'] not in seen_ids:
                        unique_audio_formats.append(item)
                        seen_ids.add(item['id'])
                unique_audio_formats.sort(key=lambda x: x.get('abr') if x.get('abr') is not None else 0, reverse=True)
                return unique_audio_formats[:10]
            else:
                logger.warning(f"Kunci 'formats' tidak ditemukan dalam info YouTube untuk URL: {url}")
                return None
    except Exception as e:
        logger.error(f"Gagal mengambil format audio YouTube ({url}): {e}", exc_info=True)
        return None

async def download_audio(url: str, format_id: str = 'bestaudio/best', preferred_format: str = 'mp3') -> str | None:
    output_template = f"{TEMP_DOWNLOAD_PATH}%(title)s_%(id)s_audio.%(ext)s"
    ydl_opts = get_common_ydl_opts(output_template=output_template)
    ydl_opts['format'] = format_id
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
            if os.path.exists(filename) and filename != expected_filename:
                if not os.path.exists(expected_filename):
                    logger.warning(f"File hasil konversi {expected_filename} tidak ditemukan, menggunakan {filename}")
                else: filename = expected_filename
            if not os.path.exists(filename):
                 logger.error(f"File audio akhir {filename} tidak ditemukan setelah proses download/konversi.")
                 return None
            logger.info(f"YouTube audio diunduh dan dikonversi: {filename}")
            return filename
    except Exception as e:
        logger.error(f"Gagal mengunduh/mengonversi audio YouTube ({url}, format: {format_id}, to: {preferred_format}): {e}", exc_info=True)
        return None