# handlers/keepdelete.py
import os
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from bot import app
import config

KEEPDELETE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "keepdelete.txt")

_cache: dict[int, str] | None = None
_me_id: int | None = None
_admin_cache: dict[int, tuple[bool, float]] = {}
_ADMIN_TTL = 300


def _read_file() -> dict[int, str]:
    if not os.path.exists(KEEPDELETE_FILE):
        return {}
    result = {}
    with open(KEEPDELETE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":", 1)
            try:
                uid = int(parts[0])
                name = parts[1] if len(parts) > 1 else str(uid)
                result[uid] = name
            except ValueError:
                continue
    return result


def _write_file(data: dict[int, str]):
    with open(KEEPDELETE_FILE, "w", encoding="utf-8") as f:
        for uid, name in data.items():
            f.write(f"{uid}:{name}\n")


def get_users() -> dict[int, str]:
    global _cache
    if _cache is None:
        _cache = _read_file()
    return _cache


def _invalidate():
    global _cache
    _cache = None


def _get_me_id(client) -> int:
    global _me_id
    if _me_id is None:
        _me_id = client.get_me().id
    return _me_id


def _is_admin(client, chat_id: int) -> bool:
    now = time.monotonic()
    cached = _admin_cache.get(chat_id)
    if cached and now - cached[1] < _ADMIN_TTL:
        return cached[0]
    try:
        member = client.get_chat_member(chat_id, _get_me_id(client))
        result = member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        result = False
    _admin_cache[chat_id] = (result, now)
    return result


def _user_label(user) -> str:
    return user.first_name or user.username or str(user.id)


def _get_target(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    args = message.command[1:]
    identifier = next((a for a in args if a.lower() not in ("remove", "list")), None)
    if identifier:
        try:
            return client.get_users(identifier)
        except Exception:
            return None
    return None


@app.on_message(filters.command("keepdelete", prefixes=config.CMD_PREFIX) & filters.me)
def keepdelete_command(client, message):
    args = message.command[1:]

    # Reply with no args → add user
    if not args and message.reply_to_message:
        args = ["_add_from_reply"]

    if not args or args[0].lower() == "list":
        users = get_users()
        if not users:
            message.edit_text("📋 Список авто-удаления пуст.")
        else:
            lines = "\n".join(
                f"{i}. {name} (ID: {uid})"
                for i, (uid, name) in enumerate(users.items(), 1)
            )
            message.edit_text(f"🗑 **Авто-удаление ({len(users)}):**\n{lines}")
        return

    if args[0].lower() == "remove":
        target = _get_target(client, message)
        if not target:
            message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.keepdelete remove @username`")
            return
        users = get_users()
        if target.id not in users:
            message.edit_text(f"❌ {_user_label(target)} не найден в списке.")
            return
        del users[target.id]
        _write_file(users)
        _invalidate()
        message.edit_text(f"✅ {_user_label(target)} убран из списка авто-удаления.")
        return

    target = _get_target(client, message)
    if not target:
        message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.keepdelete @username`")
        return

    users = get_users()
    if target.id in users:
        message.edit_text(f"⚠️ {_user_label(target)} уже в списке авто-удаления.")
        return

    users[target.id] = _user_label(target)
    _write_file(users)
    _invalidate()
    message.edit_text(f"🗑 Все сообщения от {_user_label(target)} будут автоматически удаляться.")


@app.on_message(filters.group & ~filters.me, group=1)
def auto_delete_user_messages(client, message):
    users = get_users()
    if not users:
        return

    sender_id = (
        message.from_user.id if message.from_user
        else message.sender_chat.id if message.sender_chat
        else None
    )
    if not sender_id or sender_id not in users:
        return

    if not _is_admin(client, message.chat.id):
        return

    message.delete()
