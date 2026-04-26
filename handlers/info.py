# handlers/info.py
from pyrogram import filters
from pyrogram.enums import ChatType
from bot import app
import config


@app.on_message(filters.command("id", prefixes=config.CMD_PREFIX) & filters.me)
def id_handler(client, message):
    lines = []

    chat = message.chat
    chat_label = {
        ChatType.PRIVATE:    "👤 User ID",
        ChatType.GROUP:      "👥 Group ID",
        ChatType.SUPERGROUP: "👥 Supergroup ID",
        ChatType.CHANNEL:    "📢 Channel ID",
    }.get(chat.type, "🆔 Chat ID")

    lines.append(f"{chat_label}: `{chat.id}`")

    reply = message.reply_to_message
    if reply:
        lines.append(f"✉️ Message ID: `{reply.id}`")
        if reply.from_user:
            u = reply.from_user
            name = f"{u.first_name or ''} {u.last_name or ''}".strip()
            lines.append(f"👤 User: {name}")
            lines.append(f"🔹 User ID: `{u.id}`")
            if u.username:
                lines.append(f"🔹 Username: @{u.username}")
        elif reply.sender_chat:
            sc = reply.sender_chat
            lines.append(f"📢 Sender chat: {sc.title}")
            lines.append(f"🔹 Chat ID: `{sc.id}`")

    message.edit_text("\n".join(lines))


@app.on_message(filters.command("whois", prefixes=config.CMD_PREFIX) & filters.me)
def whois_handler(client, message):
    args = message.command[1:]
    reply = message.reply_to_message

    target = None
    if reply and reply.from_user:
        target = reply.from_user
    elif args:
        try:
            target = client.get_users(args[0])
        except Exception:
            message.edit_text("❌ Пользователь не найден.")
            return
    else:
        message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.whois @username`")
        return

    u = target
    name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "—"

    lines = [f"👤 **{name}**"]
    lines.append(f"🔹 ID: `{u.id}`")

    if u.username:
        lines.append(f"🔹 Username: @{u.username}")
    else:
        lines.append("🔹 Username: —")

    if u.phone_number:
        lines.append(f"📞 Телефон: `+{u.phone_number}`")

    if getattr(u, "bio", None):
        lines.append(f"📝 Bio: {u.bio}")

    flags = []
    if u.is_bot:
        flags.append("🤖 Бот")
    if getattr(u, "is_premium", False):
        flags.append("⭐️ Premium")
    if u.is_verified:
        flags.append("✅ Верифицирован")
    if u.is_scam:
        flags.append("⚠️ Скам")
    if u.is_fake:
        flags.append("⚠️ Фейк")
    if flags:
        lines.append("  ".join(flags))

    try:
        common = client.get_common_chats(u.id)
        lines.append(f"👥 Общих групп: {len(common)}")
    except Exception:
        pass

    message.edit_text("\n".join(lines))
