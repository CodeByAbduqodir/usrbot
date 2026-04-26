# handlers/ping.py
from pyrogram import filters
from bot import app
import config

@app.on_message(filters.command("ping", prefixes=config.CMD_PREFIX) & filters.me)
def ping_handler(client, message):
    message.edit_text("🏓 Pong! Userbot is alive and kicking.")
