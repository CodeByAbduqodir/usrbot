# handlers/afk.py
import json
import os
import re
import time
from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ChatType
from bot import app
import config

AFK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "afk.json")

_DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
_DURATION_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

DEFAULT_STATE = {
    "manual_enabled": False,
    "reason": "Я сейчас AFK, отвечу позже.",
    "since": None,
    "schedule_enabled": False,
    "schedule_start": "23:00",
    "schedule_end": "08:00",
    "schedule_reason": "Ночной режим: я сплю, отвечу утром.",
    "cooldown_seconds": 21600,
    "last_replies": {},
}

_state: dict | None = None
_me_id: int | None = None


def _read_state() -> dict:
    if not os.path.exists(AFK_FILE):
        return DEFAULT_STATE.copy()
    try:
        with open(AFK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()
    return {**DEFAULT_STATE, **data}


def _write_state(state: dict):
    with open(AFK_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_state() -> dict:
    global _state
    if _state is None:
        _state = _read_state()
    return _state


def _save(state: dict):
    global _state
    _state = state
    _write_state(state)


def _parse_duration(value: str) -> int | None:
    match = _DURATION_RE.match(value.lower())
    if not match:
        return None
    return int(match.group(1)) * _DURATION_SECONDS[match.group(2)]


def _in_schedule(now: datetime, start: str, end: str) -> bool:
    if not (_TIME_RE.match(start) and _TIME_RE.match(end)):
        return False

    current = now.hour * 60 + now.minute
    start_h, start_m = map(int, start.split(":"))
    end_h, end_m = map(int, end.split(":"))
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if start_minutes <= end_minutes:
        return start_minutes <= current < end_minutes
    return current >= start_minutes or current < end_minutes


def _active_reason(state: dict) -> str | None:
    if state.get("manual_enabled"):
        return state.get("reason") or DEFAULT_STATE["reason"]
    if state.get("schedule_enabled") and _in_schedule(
        datetime.now(),
        state.get("schedule_start", "23:00"),
        state.get("schedule_end", "08:00"),
    ):
        return state.get("schedule_reason") or DEFAULT_STATE["schedule_reason"]
    return None


def _get_me_id(client) -> int:
    global _me_id
    if _me_id is None:
        _me_id = client.get_me().id
    return _me_id


def _is_for_me(client, message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    if getattr(message, "mentioned", False):
        return True
    reply = message.reply_to_message
    return bool(reply and reply.from_user and reply.from_user.id == _get_me_id(client))


def _status_text(state: dict) -> str:
    active = _active_reason(state)
    manual = "вкл" if state.get("manual_enabled") else "выкл"
    night = "вкл" if state.get("schedule_enabled") else "выкл"
    return (
        "🌙 **AFK**\n"
        f"Сейчас: {'активен' if active else 'не активен'}\n"
        f"Простой режим: {manual}\n"
        f"Ночной режим: {night} "
        f"({state.get('schedule_start')}–{state.get('schedule_end')})\n"
        f"Кулдаун: {state.get('cooldown_seconds', 21600) // 60} мин"
    )


@app.on_message(filters.command("afk", prefixes=config.CMD_PREFIX) & filters.me)
def afk_command(client, message):
    args = message.command[1:]
    state = get_state()

    if args and args[0].lower() == "off":
        state["manual_enabled"] = False
        state["last_replies"] = {}
        _save(state)
        message.edit_text("✅ AFK выключен.")
        return

    if args and args[0].lower() == "status":
        message.edit_text(_status_text(state))
        return

    if args and args[0].lower() == "cooldown":
        if len(args) < 2 or not _parse_duration(args[1]):
            message.edit_text("❌ Формат: `.afk cooldown 6h`")
            return
        state["cooldown_seconds"] = _parse_duration(args[1])
        _save(state)
        message.edit_text(f"✅ AFK-кулдаун обновлён: {args[1]}.")
        return

    if args and args[0].lower() in ("night", "ночь"):
        if len(args) > 1 and args[1].lower() == "off":
            state["schedule_enabled"] = False
            _save(state)
            message.edit_text("✅ Ночной AFK выключен.")
            return

        if len(args) < 3 or not _TIME_RE.match(args[1]) or not _TIME_RE.match(args[2]):
            message.edit_text("❌ Формат: `.afk night 23:00 08:00 [текст]`")
            return

        state["schedule_enabled"] = True
        state["schedule_start"] = args[1]
        state["schedule_end"] = args[2]
        if len(args) > 3:
            state["schedule_reason"] = " ".join(args[3:])
        _save(state)
        message.edit_text(
            f"🌙 Ночной AFK включён: {args[1]}–{args[2]}.\n"
            f"Текст: {state['schedule_reason']}"
        )
        return

    reason = " ".join(args).strip() or DEFAULT_STATE["reason"]
    state["manual_enabled"] = True
    state["reason"] = reason
    state["since"] = int(time.time())
    state["last_replies"] = {}
    _save(state)
    message.edit_text(f"🌙 AFK включён.\nТекст: {reason}")


@app.on_message(~filters.me, group=2)
def afk_auto_reply(client, message):
    state = get_state()
    reason = _active_reason(state)
    if not reason or not _is_for_me(client, message):
        return

    sender_id = (
        message.from_user.id if message.from_user
        else message.sender_chat.id if message.sender_chat
        else None
    )
    if not sender_id:
        return

    now = time.time()
    key = str(sender_id)
    last = float(state.get("last_replies", {}).get(key, 0))
    if now - last < int(state.get("cooldown_seconds", 21600)):
        return

    state.setdefault("last_replies", {})[key] = now
    _save(state)

    try:
        message.reply_text(f"🌙 {reason}")
    except Exception:
        pass
