# src/telegram/states.py

# Definisi State (Scene) untuk ConversationHandler
# Setiap angka mewakili satu langkah atau 'scene' dalam percakapan.
(SELECT_PLATFORM, AWAIT_LINK, SELECT_RESOLUTION) = range(3)