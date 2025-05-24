# # src/services/membership.py
# import logging
# from telegram import Update
# from telegram.ext import ContextTypes
# from telegram.error import BadRequest, Forbidden, TimedOut
# from config import TARGET_GROUP_ID # Impor dari config.py di root

# logger = logging.getLogger(__name__)

# async def check_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
#     """Mengecek apakah user adalah anggota grup target."""
#     if not TARGET_GROUP_ID:
#         logger.warning("TARGET_GROUP_ID tidak di-set, pengecekan keanggotaan dilewati.")
#         return True # Anggap anggota jika ID grup tidak diset

#     try:
#         # Panggil API Telegram untuk mendapatkan status anggota
#         member = await context.bot.get_chat_member(chat_id=TARGET_GROUP_ID, user_id=user_id)
#         logger.info(f"User {user_id} status in group {TARGET_GROUP_ID}: {member.status}")
#         # Status 'left' atau 'kicked' berarti bukan anggota
#         return member.status not in ['left', 'kicked']
#     except (BadRequest, Forbidden) as e:
#         # Error ini biasanya berarti bot tidak di grup atau tidak punya izin admin
#         logger.error(f"Error checking membership for user {user_id}: {e} - Pastikan bot adalah admin di grup.")
#         return False # Anggap bukan anggota jika ada error izin
#     except TimedOut:
#         logger.error(f"Timeout checking membership for user {user_id}.")
#         return False # Anggap bukan anggota jika timeout
#     except Exception as e:
#         logger.error(f"Unexpected error checking membership: {e}")
#         return False # Anggap bukan anggota jika ada error lain