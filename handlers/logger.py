# handlers/logger.py
from pyrogram import filters
from bot import app
import config
import logging

logger = logging.getLogger(__name__)

@app.on_deleted_messages()
def deleted_messages_handler(client, messages):
    if not config.LOG_CHAT_ID:
        return
    
    for message in messages:
        if message.chat.type == "private":
            try:
                client.copy_message(
                    chat_id=config.LOG_CHAT_ID,
                    from_chat_id=message.chat.id,
                    message_id=message.id
                )
                logger.info(f"Logged deleted message from {message.chat.id}")
            except Exception as e:
                logger.error(f"Failed to log deleted message: {e}")
