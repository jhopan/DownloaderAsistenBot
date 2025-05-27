# src/telegram/handlers.py
import logging
import os
import re
import subprocess
import shlex
import sys

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from telegram.constants import ChatAction
from telegram.error import BadRequest, TimedOut, NetworkError

# Impor dari proyek Anda
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE_NUMBER_UPLOADER
)
from src.telegram.states import (
    SELECT_PLATFORM, SELECT_DOWNLOAD_TYPE, AWAIT_LINK,
    SELECT_RESOLUTION_VIDEO, SELECT_QUALITY_AUDIO
)
from src.telegram.keyboard import (
    build_platform_menu, build_download_type_menu,
    build_video_resolution_menu,
    build_audio_quality_menu
)
# --- PERBAIKAN DI SINI: service -> services ---
from src.service import youtube, instagram, tiktok
# ---------------------------------------------
from src.utils import url_parser

logger = logging.getLogger(__name__)

DOWNLOADER_MODULES = {
    "youtube": youtube, "instagram": instagram, "tiktok": tiktok, "other": youtube,
}
BOT_API_UPLOAD_LIMIT_BYTES = 30 * 1024 * 1024  # 30 MB
USER_BOT_MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024 # 2 GB

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.first_name} ({user.id}) /start.")
    await update.message.reply_text(
        "Selamat datang! 👋\nPilih platform:",
        reply_markup=build_platform_menu()
    )
    return SELECT_PLATFORM

async def platform_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    platform = query.data.split('_')[1]
    context.user_data['platform'] = platform
    await query.edit_message_text(
        f"Platform: {platform.capitalize()}.\nUnduh sebagai Video atau Audio?",
        reply_markup=build_download_type_menu(platform)
    )
    return SELECT_DOWNLOAD_TYPE

async def download_type_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split('_')
    download_type = data_parts[1]
    context.user_data['download_type'] = download_type
    platform = context.user_data.get('platform', 'Tidak diketahui')
    await query.edit_message_text(
        f"Anda memilih {download_type.capitalize()} dari {platform.capitalize()}.\nKirimkan link:"
    )
    return AWAIT_LINK

async def link_received_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text
    platform = context.user_data.get('platform')
    download_type = context.user_data.get('download_type')

    if not platform or not download_type:
        await update.message.reply_text("Sesi tidak valid. Silakan /start lagi.")
        return ConversationHandler.END

    if not re.match(r'https?://', url):
        await update.message.reply_text("Link tidak valid. Coba lagi.")
        return AWAIT_LINK

    message = await update.message.reply_text(f"🔎 Mencari info {download_type} untuk {platform.capitalize()}...")
    downloader = DOWNLOADER_MODULES.get(platform)

    if not downloader:
        await message.edit_text("Platform ini belum didukung.")
        return ConversationHandler.END

    context.user_data['url'] = url

    if download_type == 'video':
        formats = await downloader.get_video_formats(url)
        if not formats:
            await message.edit_text("Gagal menemukan format video. Pastikan link benar & publik.")
            return SELECT_DOWNLOAD_TYPE
        resolution_menu = build_video_resolution_menu(formats, platform)
        if resolution_menu:
            await message.edit_text("Pilih resolusi video:", reply_markup=resolution_menu)
            return SELECT_RESOLUTION_VIDEO
        else:
            await message.edit_text("Maaf, tidak ada format video yang cocok.")
            return SELECT_DOWNLOAD_TYPE
    elif download_type == 'audio':
        audio_formats = await downloader.get_audio_formats(url)
        quality_menu = build_audio_quality_menu(audio_formats, platform)
        if quality_menu:
            await message.edit_text("Pilih kualitas audio:", reply_markup=quality_menu)
            return SELECT_QUALITY_AUDIO
        else:
            await message.edit_text("Gagal menyiapkan opsi kualitas audio.")
            return SELECT_DOWNLOAD_TYPE
    return ConversationHandler.END # Fallback

async def process_file_upload(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, file_path: str, caption: str, is_video: bool):
    if not os.path.exists(file_path):
        logger.error(f"File tidak ditemukan untuk diunggah: {file_path}")
        await query.edit_message_text("Error internal: File unduhan tidak ditemukan.")
        return

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    logger.info(f"File diunduh: {file_path}, Ukuran: {file_size_mb:.2f} MB")
    target_chat_id = query.message.chat_id

    if file_size_bytes <= BOT_API_UPLOAD_LIMIT_BYTES:
        await query.edit_message_text(f"⬆️ Mengunggah via Bot API ({file_size_mb:.2f} MB)...")
        await context.bot.send_chat_action(chat_id=target_chat_id, action=ChatAction.UPLOAD_VIDEO if is_video else ChatAction.UPLOAD_AUDIO)
        with open(file_path, 'rb') as f_to_send:
            if is_video:
                await context.bot.send_video(chat_id=target_chat_id, video=f_to_send, supports_streaming=True, caption=caption, write_timeout=None)
            else:
                await context.bot.send_audio(chat_id=target_chat_id, audio=f_to_send, caption=caption, write_timeout=None)
        await query.delete_message()
        logger.info(f"File {file_path} berhasil dikirim via Bot API.")
        if os.path.exists(file_path): # Hapus setelah Bot API upload
            try: os.remove(file_path); logger.info(f"File {file_path} dihapus setelah Bot API upload.")
            except Exception as e_remove: logger.error(f"Gagal hapus {file_path} setelah Bot API upload: {e_remove}")

    elif BOT_API_UPLOAD_LIMIT_BYTES < file_size_bytes <= USER_BOT_MAX_UPLOAD_BYTES:
        await query.edit_message_text(f"Ukuran file ({file_size_mb:.2f} MB) besar. Menggunakan pengunggah khusus via akun pribadi... Ini mungkin sangat lama.")
        logger.info(f"Mencoba unggah {file_path} via Telethon uploader ke chat ID {target_chat_id}")

        if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER_UPLOADER]):
            logger.error("Kredensial Telethon (API_ID, API_HASH, PHONE_NUMBER) tidak lengkap di .env")
            await query.edit_message_text("Gagal memulai pengunggah khusus: Konfigurasi tidak lengkap.")
            if os.path.exists(file_path): # Hapus jika config Telethon tidak lengkap
                try: os.remove(file_path); logger.info(f"File {file_path} dihapus karena config Telethon tidak lengkap.")
                except Exception as e_remove: logger.error(f"Gagal hapus {file_path} (config Telethon tdk lengkap): {e_remove}")
            return

        python_executable = sys.executable
        command = [
            python_executable,
            "uploader_telethon.py",
            str(target_chat_id),
            file_path,
            caption
        ]
        try:
            logger.info(f"Menjalankan perintah: {' '.join(shlex.quote(c) for c in command)}")
            process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=7200) # Timeout 2 jam

            if process.returncode == 0:
                logger.info(f"Skrip uploader_telethon.py berhasil untuk {file_path}. Output: {process.stdout}")
                await query.edit_message_text(f"✅ File ({file_size_mb:.2f} MB) berhasil dikirim via pengunggah khusus!")
                # Skrip uploader_telethon.py yang idealnya menghapus file jika sukses (sudah diimplementasikan di uploader_telethon.py)
            else:
                logger.error(f"Skrip uploader_telethon.py gagal untuk {file_path}. Return code: {process.returncode}. Output: {process.stdout}. Error: {process.stderr}")
                await query.edit_message_text(f"⚠️ Gagal mengirim file ({file_size_mb:.2f} MB) via pengunggah khusus. Cek log bot.")
                if os.path.exists(file_path): # Hapus jika Telethon gagal
                    try: os.remove(file_path); logger.info(f"File {file_path} dihapus setelah Telethon uploader gagal.")
                    except Exception as e_remove: logger.error(f"Gagal hapus {file_path} (Telethon gagal): {e_remove}")
        except subprocess.TimeoutExpired:
            logger.error(f"Skrip uploader_telethon.py timeout untuk {file_path}.")
            await query.edit_message_text(f"⚠️ Pengiriman file ({file_size_mb:.2f} MB) via pengunggah khusus timeout.")
            if os.path.exists(file_path): # Hapus jika Telethon timeout
                try: os.remove(file_path); logger.info(f"File {file_path} dihapus setelah Telethon uploader timeout.")
                except Exception as e_remove: logger.error(f"Gagal hapus {file_path} (Telethon timeout): {e_remove}")
        except Exception as e_subproc:
            logger.error(f"Error menjalankan uploader_telethon.py: {e_subproc}", exc_info=True)
            await query.edit_message_text("Terjadi kesalahan internal saat mencoba pengunggah khusus.")
            if os.path.exists(file_path): # Hapus jika error lain
                try: os.remove(file_path); logger.info(f"File {file_path} dihapus karena error subproses Telethon.")
                except Exception as e_remove: logger.error(f"Gagal hapus {file_path} (error subproses Telethon): {e_remove}")
    else: # File > USER_BOT_MAX_UPLOAD_BYTES
        await query.edit_message_text(
            f"Video/Audio ({file_size_mb:.2f} MB) terlalu besar untuk diunggah "
            f"(maks {USER_BOT_MAX_UPLOAD_BYTES / (1024*1024):.0f} MB).\n"
            "Silakan pilih resolusi/kualitas yang lebih rendah."
        )
        if os.path.exists(file_path): # Hapus karena terlalu besar
            try: os.remove(file_path); logger.info(f"File {file_path} dihapus karena terlalu besar.")
            except Exception as e_remove: logger.error(f"Gagal hapus {file_path} (terlalu besar): {e_remove}")

async def video_resolution_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        _, _, format_id, platform = query.data.split('_', 3)
    except ValueError:
        await query.edit_message_text("Error: Data callback video tidak valid.")
        return ConversationHandler.END
    url = context.user_data.get('url')
    if not url:
        await query.edit_message_text("Sesi berakhir. /start lagi.")
        return ConversationHandler.END
    await query.edit_message_text(f"⚙️ Mengunduh video ({format_id})... Mohon tunggu.")
    downloader = DOWNLOADER_MODULES.get(platform)
    video_path = None
    try:
        video_path = await downloader.download_video(url, format_id)
        if video_path and os.path.exists(video_path):
            await process_file_upload(query, context, video_path, "✅ Video Selesai!\nTerimakasih sudah menggunakan bot ini 😊", is_video=True)
        else:
            logger.error(f"Download_video mengembalikan path tidak valid atau file tidak ada: {video_path} untuk URL {url}")
            await query.edit_message_text("Maaf, gagal mengunduh video dari sumbernya (file tidak ditemukan setelah download).")
    except Exception as e:
        logger.error(f"Error saat proses download_video: {e}", exc_info=True)
        await query.edit_message_text("Terjadi kesalahan saat mengunduh video.")
    finally:
        # File akan dihapus oleh process_file_upload jika dihandle Bot API atau jika gagal/timeout di Telethon
        # atau jika terlalu besar. Jika Telethon sukses, skrip Telethon yang menghapus.
        # Jika download_video gagal sebelum process_file_upload, file perlu dihapus di sini.
        if video_path and os.path.exists(video_path):
            # Cek apakah file masih ada (belum dihapus oleh process_file_upload atau Telethon)
            # Ini adalah fallback jika proses tidak sampai ke penghapusan di process_file_upload
            # atau jika Telethon tidak menghapusnya.
            # Untuk menghindari error jika file sudah dihapus, kita cek lagi.
            try:
                # Jika file tidak diserahkan ke Telethon (karena ukuran atau error config), maka hapus di sini.
                file_size_bytes_check = os.path.getsize(video_path)
                if not (BOT_API_UPLOAD_LIMIT_BYTES < file_size_bytes_check <= USER_BOT_MAX_UPLOAD_BYTES and \
                        all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER_UPLOADER])):
                    os.remove(video_path)
                    logger.info(f"File sementara {video_path} dihapus dari finally video_resolution_selected.")
            except FileNotFoundError:
                logger.info(f"File {video_path} sudah dihapus sebelumnya (mungkin oleh process_file_upload atau Telethon).")
            except Exception as e_remove:
                logger.error(f"Gagal hapus file {video_path} di finally video_res: {e_remove}")
    context.user_data.clear()
    return ConversationHandler.END

async def audio_quality_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split('_')
        format_id_or_quality = parts[2]
        platform = parts[-1]
        preferred_format = 'mp3'
        format_id = 'bestaudio/best'
        if '-' in format_id_or_quality:
            quality_part, format_part = format_id_or_quality.split('-', 1)
            preferred_format = format_part
            if quality_part != 'best': format_id = quality_part
        elif format_id_or_quality != 'best':
            format_id = format_id_or_quality
    except Exception as e:
        logger.error(f"Error parsing callback data audio: {query.data}, error: {e}")
        await query.edit_message_text("Error: Data callback audio tidak valid.")
        return ConversationHandler.END
    url = context.user_data.get('url')
    if not url:
        await query.edit_message_text("Sesi berakhir. /start lagi.")
        return ConversationHandler.END
    await query.edit_message_text(f"⚙️ Mengunduh audio ({format_id_or_quality} sebagai {preferred_format})... Mohon tunggu.")
    downloader = DOWNLOADER_MODULES.get(platform)
    audio_path = None
    try:
        audio_path = await downloader.download_audio(url, format_id=format_id, preferred_format=preferred_format)
        if audio_path and os.path.exists(audio_path):
            await process_file_upload(query, context, audio_path, "🎵 Audio Selesai!\nTerimakasih sudah menggunakan bot ini 😊", is_video=False)
        else:
            logger.error(f"Download_audio mengembalikan path tidak valid atau file tidak ada: {audio_path} untuk URL {url}")
            await query.edit_message_text("Maaf, gagal mengunduh audio dari sumbernya (file tidak ditemukan setelah download).")
    except Exception as e:
        logger.error(f"Error saat proses download_audio: {e}", exc_info=True)
        await query.edit_message_text("Terjadi kesalahan saat mengunduh audio.")
    finally:
        # Logika penghapusan file sama seperti untuk video
        if audio_path and os.path.exists(audio_path):
            try:
                file_size_bytes_check = os.path.getsize(audio_path)
                if not (BOT_API_UPLOAD_LIMIT_BYTES < file_size_bytes_check <= USER_BOT_MAX_UPLOAD_BYTES and \
                        all([TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER_UPLOADER])):
                    os.remove(audio_path)
                    logger.info(f"File sementara {audio_path} dihapus dari finally audio_quality_selected.")
            except FileNotFoundError:
                logger.info(f"File {audio_path} sudah dihapus sebelumnya.")
            except Exception as e_remove:
                logger.error(f"Gagal hapus file {audio_path} di finally audio_quality: {e_remove}")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Operasi dibatalkan."
    if update.callback_query:
        query = update.callback_query
        try: await query.answer()
        except BadRequest: pass
        try: await query.edit_message_text(text)
        except BadRequest: pass
    else:
        await update.message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

def run_bot():
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(None)
        .read_timeout(None)
        .write_timeout(None)
        .pool_timeout(None)
        .build()
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            SELECT_PLATFORM: [CallbackQueryHandler(platform_selected_callback, pattern='^platform_')],
            SELECT_DOWNLOAD_TYPE: [CallbackQueryHandler(download_type_selected_callback, pattern='^dltype_')],
            AWAIT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'https?://'), link_received_handler)],
            SELECT_RESOLUTION_VIDEO: [CallbackQueryHandler(video_resolution_selected_callback, pattern='^res_video_')],
            SELECT_QUALITY_AUDIO: [CallbackQueryHandler(audio_quality_selected_callback, pattern='^res_audio_')],
        },
        fallbacks=[
            CommandHandler('start', start_command), CommandHandler('cancel', cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern='^cancel$'), ],
        per_user=True, conversation_timeout=None
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    logger.info("Bot siap dan mulai polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)