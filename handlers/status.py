# handlers/status.py
from pyrogram import filters
from bot import app
import config
import psutil
import time

@app.on_message(filters.command("status", prefixes=config.CMD_PREFIX) & filters.me)
def status_handler(client, message):
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        uptime = time.time() - psutil.boot_time()
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        
        text = (
            f"<b>🖥 Server Status:</b>\n\n"
            f"<b>CPU:</b> {cpu_percent}%\n"
            f"<b>RAM:</b> {ram.percent}% ({ram.used / (1024**3):.1f}GB / {ram.total / (1024**3):.1f}GB)\n"
            f"<b>Disk:</b> {disk.percent}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)\n"
            f"<b>Uptime:</b> {days}d {hours}h {minutes}m"
        )
        message.edit_text(text)
    except Exception as e:
        message.edit_text(f"❌ Error fetching status: {str(e)}")
