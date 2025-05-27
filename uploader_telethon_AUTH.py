# uploader_telethon_AUTH.py (KHUSUS UNTUK OTENTIKASI PERTAMA KALI)
import asyncio
import sys
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()

async def authenticate_session(api_id_int, api_hash_str, phone_str):
    session_name = f"user_session_{phone_str.replace('+', '')}"
    client = TelegramClient(session_name, api_id_int, api_hash_str)

    try:
        print(f"Otentikasi: Mencoba menghubungkan sebagai {phone_str}...")
        await client.connect()

        if not await client.is_user_authorized():
            print(f"Otentikasi: Sesi untuk {phone_str} belum terotorisasi. Memulai proses login...")
            await client.send_code_request(phone_str)
            try:
                code = input("Otentikasi: Masukkan kode yang Anda terima dari Telegram: ")
                await client.sign_in(phone_str, code)
            except SessionPasswordNeededError:
                password = input("Otentikasi: Akun Anda dilindungi 2FA. Masukkan password Anda: ")
                await client.sign_in(password=password)
            
            if await client.is_user_authorized():
                print("Otentikasi: Login BERHASIL! File sesi telah dibuat/diperbarui.")
            else:
                print("Otentikasi: Login GAGAL. Periksa kode/password atau coba lagi.")
        else:
            print(f"Otentikasi: Berhasil terhubung, sesi untuk {phone_str} sudah ada dan terotorisasi.")

    except Exception as e:
        print(f"Otentikasi: Terjadi kesalahan: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
        print("Otentikasi: Koneksi ditutup.")

if __name__ == '__main__':
    API_ID_FROM_ENV = os.getenv("TELEGRAM_API_ID")
    API_HASH_FROM_ENV = os.getenv("TELEGRAM_API_HASH")
    PHONE_FROM_ENV = os.getenv("TELEGRAM_PHONE_NUMBER_UPLOADER")

    if not all([API_ID_FROM_ENV, API_HASH_FROM_ENV, PHONE_FROM_ENV]):
        print("Error: Pastikan TELEGRAM_API_ID, TELEGRAM_API_HASH, dan TELEGRAM_PHONE_NUMBER_UPLOADER sudah diatur di file .env")
        sys.exit(1)
    
    try:
        api_id_int_env = int(API_ID_FROM_ENV)
    except ValueError:
        print(f"Error: TELEGRAM_API_ID '{API_ID_FROM_ENV}' di .env bukan angka yang valid.")
        sys.exit(1)

    print("Skrip ini HANYA untuk otentikasi manual pertama kali.")
    print("Ia akan mencoba login dan membuat file .session.")
    print("Tidak ada file yang akan diunggah oleh skrip ini.")
    
    asyncio.run(authenticate_session(api_id_int_env, API_HASH_FROM_ENV, PHONE_FROM_ENV))