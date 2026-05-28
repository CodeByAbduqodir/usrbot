# main.py
import logging

from bot import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from handlers import ping, status, logger as logger_handler, badword, mute, keepdelete, help, info, afk, shortcuts

def start_bot():
    logger.info("🚀 Starting Userbot...")
    app.run()

if __name__ == "__main__":
    start_bot()
