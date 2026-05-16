# handlers/keepdelete.py
import json
import os
import re
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from bot import app
import config

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LEGACY_FILE = os.path.join(BASE_DIR, "keepdelete.txt")
KEEPDELETE_FILE = os.path.join(BASE_DIR, "keepdelete.json")

_DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_DURATION_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

_cache: list[dict] | None = None
_me_id: int | None = None
_admin_cache: dict[int, tuple[bool, float]] = {}
_ADMIN_TTL = 300


def _read_legacy_file() -> list[dict]:
    if not os.path.exists(LEGACY_FILE):
        return []

    entries = []
    with open(LEGACY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":", 1)
            try:
                uid = int(parts[0])
            except ValueError:
                continue
            entries.append({
                "user_id": uid,
                "name": parts[1] if len(parts) > 1 else str(uid),
                "chat_id": None,
                "chat_title": "Все чаты",
                "expires_at": None,
            })
    return entries


def _read_file() -> list[dict]:
    if os.path.exists(KEEPDELETE_FILE):
        try:
            with open(KEEPDELETE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []
    return _read_legacy_file()


def _write_file(entries: list[dict]):
    with open(KEEPDELETE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def get_entries() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = _prune_expired(_read_file())
    return _cache


def _invalidate():
    global _cache
    _cache = None


def _prune_expired(entries: list[dict]) -> list[dict]:
    now = time.time()
    return [
        entry for entry in entries
        if not entry.get("expires_at") or float(entry["expires_at"]) > now
    ]


def _parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = _DURATION_RE.match(value.lower())
    if not match:
        return None
    return int(match.group(1)) * _DURATION_SECONDS[match.group(2)]


def _duration_label(seconds: int | None) -> str:
    if not seconds:
        return "навсегда"
    for unit, size, label in (("d", 86400, "д"), ("h", 3600, "ч"), ("m", 60, "мин"), ("s", 1, "сек")):
        if seconds % size == 0:
            return f"{seconds // size}{label}"
    return f"{seconds}сек"


def _expires_label(expires_at) -> str:
    if not expires_at:
        return "навсегда"
    left = int(float(expires_at) - time.time())
    if left <= 0:
        return "истекло"
    return _duration_label(left)


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


def _chat_title(message, global_scope: bool) -> str:
    if global_scope:
        return "Все чаты"
    return message.chat.title or message.chat.first_name or str(message.chat.id)


def _command_args(message) -> list[str]:
    return message.command[1:]


def _get_target(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    skip = {"remove", "list", "global", "here"}
    identifier = next((
        arg for arg in _command_args(message)
        if arg.lower() not in skip and not _DURATION_RE.match(arg.lower())
    ), None)
    if identifier:
        try:
            return client.get_users(identifier)
        except Exception:
            return None
    return None


def _scope_from_args(message) -> tuple[int | None, str, bool]:
    args = [arg.lower() for arg in _command_args(message)]
    global_scope = "global" in args
    if message.chat.type == ChatType.PRIVATE or global_scope:
        return None, "Все чаты", True
    return message.chat.id, _chat_title(message, False), False


def _find_entry(entries: list[dict], user_id: int, chat_id: int | None):
    return next((
        entry for entry in entries
        if int(entry.get("user_id", 0)) == user_id and entry.get("chat_id") == chat_id
    ), None)


@app.on_message(filters.command("keepdelete", prefixes=config.CMD_PREFIX) & filters.me)
def keepdelete_command(client, message):
    args = _command_args(message)

    if not args and message.reply_to_message:
        args = ["_add_from_reply"]

    entries = get_entries()

    if not args or args[0].lower() == "list":
        entries = _prune_expired(entries)
        if not entries:
            message.edit_text("📋 Список авто-удаления пуст.")
            return

        lines = []
        for i, entry in enumerate(entries, 1):
            chat = entry.get("chat_title") or "Все чаты"
            ttl = _expires_label(entry.get("expires_at"))
            lines.append(
                f"{i}. {entry.get('name', entry['user_id'])} "
                f"(ID: {entry['user_id']})\n   Чат: {chat} · Срок: {ttl}"
            )
        message.edit_text(f"🗑 **Авто-удаление ({len(entries)}):**\n" + "\n".join(lines))
        return

    chat_id, chat_title, global_scope = _scope_from_args(message)

    if args[0].lower() == "remove":
        target = _get_target(client, message)
        if not target:
            message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.keepdelete remove @username`")
            return

        entry = _find_entry(entries, target.id, chat_id)
        if not entry and not global_scope:
            entry = _find_entry(entries, target.id, None)
        if not entry:
            message.edit_text(f"❌ {_user_label(target)} не найден в списке.")
            return

        entries.remove(entry)
        _write_file(entries)
        _invalidate()
        message.edit_text(f"✅ {_user_label(target)} убран из авто-удаления: {entry.get('chat_title', 'Все чаты')}.")
        return

    target = _get_target(client, message)
    if not target:
        message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.keepdelete @username [1h]`")
        return

    duration_arg = next((arg for arg in args if _DURATION_RE.match(arg.lower())), None)
    seconds = _parse_duration(duration_arg)
    expires_at = time.time() + seconds if seconds else None

    existing = _find_entry(entries, target.id, chat_id)
    if existing:
        existing.update({
            "name": _user_label(target),
            "chat_title": chat_title,
            "expires_at": expires_at,
        })
        action = "обновлено"
    else:
        entries.append({
            "user_id": target.id,
            "name": _user_label(target),
            "chat_id": chat_id,
            "chat_title": chat_title,
            "expires_at": expires_at,
        })
        action = "включено"

    _write_file(entries)
    _invalidate()
    message.edit_text(
        f"🗑 Авто-удаление для {_user_label(target)} {action}.\n"
        f"Чат: {chat_title}\n"
        f"Срок: {_duration_label(seconds)}"
    )


@app.on_message(filters.group & ~filters.me, group=1)
def auto_delete_user_messages(client, message):
    entries = get_entries()
    if not entries:
        return

    sender_id = (
        message.from_user.id if message.from_user
        else message.sender_chat.id if message.sender_chat
        else None
    )
    if not sender_id:
        return

    active = [
        entry for entry in entries
        if int(entry.get("user_id", 0)) == sender_id
        and (entry.get("chat_id") is None or entry.get("chat_id") == message.chat.id)
    ]
    if not active:
        return

    if not _is_admin(client, message.chat.id):
        return

    message.delete()
