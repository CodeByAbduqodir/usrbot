# bot.py
from pyrogram import Client

import config


app = Client(
    config.SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    workdir="sessions/"
)
