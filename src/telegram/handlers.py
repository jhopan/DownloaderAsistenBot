# src/telegram/handlers.py
import logging
import os
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from telegram.constants import ChatAction
from telegram.error import BadRequest, TimedOut

# Impor dari proyek Anda
from config import TELEGRAM_BOT_TOKEN
from src.telegram.states import SELECT_PLATFORM, AWAIT_LINK, SELECT_RESOLUTION
from src.telegram.keyboard import build_platform_menu, build_resolution_menu
from src.service import youtube, instagram, tiktok # Pastikan ini 'services'
from src.utils import url_parser

logger = logging.getLogger(__name__)

DOWNLOADER_MODULES = {
    "youtube": youtube,
    "instagram": instagram,
    "tiktok": tiktok,
    "other": youtube, # Default 'other' ke youtube
}

# --- Fungsi-fungsi Handler untuk Conversation ---

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
        f"Anda memilih {platform.capitalize()}.\nKirimkan link videonya:"
    )
    return AWAIT_LINK

async def link_received_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text
    detected_platform = url_parser.identify_platform(url)
    platform = context.user_data.get('platform', detected_platform)

    if not re.match(r'https?://', url):
        await update.message.reply_text("Link tidak valid. Coba lagi.")
        return AWAIT_LINK

    message = await update.message.reply_text("🔎 Mencari info video...")
    downloader = DOWNLOADER_MODULES.get(platform)

    if not downloader:
        await message.edit_text("Platform ini belum didukung.")
        return ConversationHandler.END

    formats = await downloader.get_video_formats(url)

    if not formats:
        await message.edit_text("Gagal menemukan format. Pastikan link benar & publik.")
        return SELECT_PLATFORM

    context.user_data['url'] = url
    context.user_data['formats'] = formats
    context.user_data['platform'] = platform

    resolution_menu = build_resolution_menu(formats, platform)
    if resolution_menu:
        await message.edit_text("Pilih resolusi:", reply_markup=resolution_menu)
        return SELECT_RESOLUTION
    else:
        await message.edit_text("Maaf, tidak ada format (< 2GB) yang ditemukan.")
        return SELECT_PLATFORM

async def resolution_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    try:
        _, format_id, platform = query.data.split('_', 2)
    except ValueError:
        await query.edit_message_text("Error: Data tidak valid.")
        return ConversationHandler.END

    url = context.user_data.get('url')
    if not url:
        await query.edit_message_text("Sesi berakhir. /start lagi.")
        return ConversationHandler.END

    await query.edit_message_text("⚙️ Mengunduh... Mohon tunggu.")
    await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.UPLOAD_VIDEO)

    downloader = DOWNLOADER_MODULES.get(platform)
    video_path = None
    try:
        video_path = await downloader.download_video(url, format_id)
        if video_path and os.path.exists(video_path):
            file_size_bytes = os.path.getsize(video_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            logger.info(f"Video diunduh: {video_path}, Ukuran: {file_size_mb:.2f} MB")
            await query.edit_message_text(f"⬆️ Mengunggah video ({file_size_mb:.2f} MB)...")

            with open(video_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=video_file,
                    supports_streaming=True,
                    caption="✅ Selesai!\nTerimakasih sudah menggunakan bot ini 😊",
                    write_timeout=300
                )
            await query.delete_message()
        else:
            await query.edit_message_text("Maaf, gagal mengunduh video dari sumbernya.")
    except TimedOut:
        logger.error(f"Timeout saat mengirim video {url}", exc_info=True)
        try:
            await query.edit_message_text("Gagal mengirim video: Waktu unggah habis (Timeout). Videonya mungkin terlalu besar atau jaringan lambat.")
        except BadRequest:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Gagal mengirim video: Waktu unggah habis (Timeout).")
    except Exception as e:
        logger.error(f"Error download/send lainnya: {e}", exc_info=True)
        try:
            await query.edit_message_text("Terjadi kesalahan tak terduga saat memproses video Anda.")
        except BadRequest:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Terjadi kesalahan tak terduga.")
    finally:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Operasi dibatalkan."
    if update.callback_query:
        query = update.callback_query
        try:
            await query.answer()
            await query.edit_message_text(text)
        except BadRequest:
            pass
    else:
        await update.message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

# --- Fungsi Utama untuk Menjalankan Bot ---

def run_bot():
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(300)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            SELECT_PLATFORM: [CallbackQueryHandler(platform_selected_callback, pattern='^platform_')],
            AWAIT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'https?://'), link_received_handler)],
            SELECT_RESOLUTION: [CallbackQueryHandler(resolution_selected_callback, pattern='^res_')],
        },
        fallbacks=[
            CommandHandler('start', start_command),
            CommandHandler('cancel', cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern='^cancel$'),
        ],
        per_user=True,
        conversation_timeout=600
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logger.info("Bot siap dan mulai polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)