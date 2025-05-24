# bot.py
import logging
import os
from src.telegram.handlers import run_bot

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log")
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Memulai bot dari bot.py...")
    try:
        run_bot()
    except Exception as e:
        logger.critical(f"Bot berhenti karena error fatal: {e}", exc_info=True)
    finally:
        logger.info("Bot berhenti.")