# uploader_telethon.py
import asyncio
import sys
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv() # Muat variabel dari .env

async def main_uploader(api_id_int, api_hash_str, phone_str, target_chat_id_str, file_path_str, caption_str):
    session_name = f"user_session_{phone_str.replace('+', '')}"
    try:
        target_chat_id = int(target_chat_id_str)
    except ValueError:
        print(f"Error: CHAT_ID_TUJUAN '{target_chat_id_str}' bukan angka yang valid.")
        return 1 # Kode error

    if not os.path.exists(file_path_str):
        print(f"Error: File tidak ditemukan di '{file_path_str}'")
        return 1

    client = TelegramClient(session_name, api_id_int, api_hash_str)
    return_code = 1 # Default ke error

    try:
        print(f"Uploader: Mencoba menghubungkan sebagai {phone_str}...")
        await client.connect()
        if not await client.is_user_authorized():
            print(f"Uploader: Sesi untuk {phone_str} belum terotorisasi. Silakan otentikasi manual dulu.")
            # Untuk skrip yang dipanggil otomatis, otentikasi interaktif sulit.
            # Pastikan sesi sudah dibuat dengan menjalankan skrip ini manual sekali.
            return 1
        else:
            print(f"Uploader: Berhasil terhubung sebagai {phone_str}.")

        print(f"Uploader: Mengirim file: {file_path_str} ke chat ID: {target_chat_id}...")
        try:
            entity = await client.get_input_entity(target_chat_id)
        except Exception as e_entity:
            print(f"Uploader: Tidak bisa mendapatkan entity untuk chat ID {target_chat_id}. Error: {e_entity}")
            return 1
            
        message = await client.send_file(entity, file_path_str, caption=caption_str)
        print(f"Uploader: File berhasil dikirim! ID Pesan: {message.id}")
        return_code = 0 # Sukses
    except Exception as e:
        print(f"Uploader: Terjadi kesalahan: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
        print("Uploader: Koneksi ditutup.")
        
        # Penting: Hapus file setelah berhasil diunggah atau jika gagal (opsional)
        # Jika Anda ingin skrip ini yang menghapus file:
        if return_code == 0 and os.path.exists(file_path_str): # Hanya hapus jika sukses
             try:
                 os.remove(file_path_str)
                 print(f"Uploader: File sementara {file_path_str} berhasil dihapus.")
             except Exception as e_remove:
                 print(f"Uploader: Gagal menghapus file sementara {file_path_str}: {e_remove}")
        elif os.path.exists(file_path_str): # Jika gagal, mungkin ingin tetap dihapus
            print(f"Uploader: Pengiriman gagal, file {file_path_str} tidak dihapus oleh uploader.")


    return return_code


if __name__ == '__main__':
    API_ID_FROM_ENV = os.getenv("TELEGRAM_API_ID")
    API_HASH_FROM_ENV = os.getenv("TELEGRAM_API_HASH")
    PHONE_FROM_ENV = os.getenv("TELEGRAM_PHONE_NUMBER_UPLOADER")

    if not all([API_ID_FROM_ENV, API_HASH_FROM_ENV, PHONE_FROM_ENV]):
        print("Error: TELEGRAM_API_ID, TELEGRAM_API_HASH, atau TELEGRAM_PHONE_NUMBER_UPLOADER tidak ditemukan di file .env")
        sys.exit(1)
    try:
        api_id_int_env = int(API_ID_FROM_ENV)
    except ValueError:
        print(f"Error: TELEGRAM_API_ID '{API_ID_FROM_ENV}' di .env bukan angka yang valid.")
        sys.exit(1)

    if len(sys.argv) < 4:
        print("Penggunaan: python uploader_telethon.py <target_chat_id> <file_path> \"<caption>\"")
        sys.exit(1)
    
    _target_chat_id = sys.argv[1]
    _file_path = sys.argv[2]
    _caption = sys.argv[3]

    # Jalankan loop asyncio dan dapatkan return code
    exit_code = asyncio.run(main_uploader(api_id_int_env, API_HASH_FROM_ENV, PHONE_FROM_ENV, _target_chat_id, _file_path, _caption))
    sys.exit(exit_code) # Keluar dengan kode status dari main_uploader