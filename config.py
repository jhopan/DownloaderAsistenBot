# config.py
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TEMP_DOWNLOAD_PATH = "downloads/"
IG_USERNAME = os.getenv('IG_USERNAME')
IG_PASSWORD = os.getenv('IG_PASSWORD')

if not TELEGRAM_BOT_TOKEN:
    logger.critical("KESALAHAN: TELEGRAM_BOT_TOKEN tidak ditemukan di .env.")
    exit("TELEGRAM_BOT_TOKEN tidak ditemukan.")

logger.info("Konfigurasi berhasil dimuat.")

if not os.path.exists(TEMP_DOWNLOAD_PATH):
    try:
        os.makedirs(TEMP_DOWNLOAD_PATH)
        logger.info(f"Folder '{TEMP_DOWNLOAD_PATH}' dibuat.")
    except Exception as e:
        logger.critical(f"Gagal membuat folder '{TEMP_DOWNLOAD_PATH}': {e}")
        exit(f"Gagal membuat folder '{TEMP_DOWNLOAD_PATH}'.")