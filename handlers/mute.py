# handlers/mute.py
import re
from datetime import datetime, timedelta, timezone
from pyrogram import filters
from pyrogram.types import ChatPermissions
from pyrogram.enums import ChatMemberStatus
from bot import app
import config

_DURATION_RE = re.compile(r'^(\d+)([smhd])$')
_DURATION_MAP = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
_DURATION_LABEL = {'s': 'сек', 'm': 'мин', 'h': 'ч', 'd': 'д'}


def _parse_duration(s: str) -> timedelta | None:
    m = _DURATION_RE.match(s.lower())
    if not m:
        return None
    return timedelta(**{_DURATION_MAP[m.group(2)]: int(m.group(1))})


def _is_admin(client, chat_id) -> bool:
    try:
        me = client.get_me()
        member = client.get_chat_member(chat_id, me.id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


def _get_target(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    args = message.command[1:]
    identifier = next((a for a in args if not _DURATION_RE.match(a.lower())), None)
    if identifier:
        try:
            return client.get_users(identifier)
        except Exception:
            return None
    return None


def _user_label(user) -> str:
    return user.first_name or user.username or str(user.id)


@app.on_message(filters.command("mute", prefixes=config.CMD_PREFIX) & filters.me & filters.group)
def mute_handler(client, message):
    if not _is_admin(client, message.chat.id):
        message.edit_text("❌ Ты не являешься админом в этой группе.")
        return

    target = _get_target(client, message)
    if not target:
        message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.mute @username [10m]`")
        return

    duration_str = next((a for a in message.command[1:] if _DURATION_RE.match(a.lower())), None)
    until_date = None
    label = "навсегда"

    if duration_str:
        delta = _parse_duration(duration_str)
        if delta:
            until_date = datetime.now(timezone.utc) + delta
            m = _DURATION_RE.match(duration_str.lower())
            label = f"{m.group(1)}{_DURATION_LABEL[m.group(2)]}"

    try:
        client.restrict_chat_member(
            message.chat.id,
            target.id,
            ChatPermissions(),
            until_date=until_date,
        )
        message.edit_text(f"🔇 {_user_label(target)} замьючен на {label}.")
    except Exception as e:
        message.edit_text(f"❌ Не удалось замьютить: {e}")


@app.on_message(filters.command("unmute", prefixes=config.CMD_PREFIX) & filters.me & filters.group)
def unmute_handler(client, message):
    if not _is_admin(client, message.chat.id):
        message.edit_text("❌ Ты не являешься админом в этой группе.")
        return

    target = _get_target(client, message)
    if not target:
        message.edit_text("❌ Укажи пользователя: ответь на сообщение или `.unmute @username`")
        return

    try:
        chat = client.get_chat(message.chat.id)
        perms = chat.permissions or ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        client.restrict_chat_member(message.chat.id, target.id, perms)
        message.edit_text(f"🔊 {_user_label(target)} размьючен.")
    except Exception as e:
        message.edit_text(f"❌ Не удалось размьютить: {e}")
