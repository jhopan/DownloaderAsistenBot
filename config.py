# config.py
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv() # Memuat variabel dari file .env

# Kredensial utama Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TEMP_DOWNLOAD_PATH = "downloads/"

# Kredensial opsional untuk login Instagram
IG_USERNAME = os.getenv('IG_USERNAME')
IG_PASSWORD = os.getenv('IG_PASSWORD')

# Kredensial untuk Telethon (jika Anda mengimplementasikan uploader akun pribadi)
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_PHONE_NUMBER_UPLOADER = os.getenv('TELEGRAM_PHONE_NUMBER_UPLOADER')


# Validasi Token Bot Utama
if not TELEGRAM_BOT_TOKEN:
    logger.critical("KESALAHAN: TELEGRAM_BOT_TOKEN tidak ditemukan di .env.")
    exit("TELEGRAM_BOT_TOKEN tidak ditemukan.")

logger.info("Konfigurasi berhasil dimuat.")

# Membuat folder unduhan jika belum ada
if not os.path.exists(TEMP_DOWNLOAD_PATH):
    try:
        os.makedirs(TEMP_DOWNLOAD_PATH)
        logger.info(f"Folder '{TEMP_DOWNLOAD_PATH}' dibuat.")
    except Exception as e:
        logger.critical(f"Gagal membuat folder '{TEMP_DOWNLOAD_PATH}': {e}")
        exit(f"Gagal membuat folder '{TEMP_DOWNLOAD_PATH}'.")