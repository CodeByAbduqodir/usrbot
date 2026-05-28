# handlers/shortcuts.py
import json
import os
from pyrogram import filters
from bot import app
import config

SHORTCUTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shortcuts.json")

DEFAULT_SHORTCUTS = {
    "shrug": "¯\\_(ツ)_/¯",
    "brb": "Скоро вернусь.",
    "gm": "Доброе утро!",
    "gn": "Спокойной ночи!",
    "ty": "Спасибо!",
    "np": "Без проблем.",
}

_cache: dict[str, str] | None = None


def _read_shortcuts() -> dict[str, str]:
    if not os.path.exists(SHORTCUTS_FILE):
        return DEFAULT_SHORTCUTS.copy()
    try:
        with open(SHORTCUTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SHORTCUTS.copy()
    return {**DEFAULT_SHORTCUTS, **data}


def _write_shortcuts(shortcuts: dict[str, str]):
    custom = {
        key: value for key, value in shortcuts.items()
        if DEFAULT_SHORTCUTS.get(key) != value
    }
    with open(SHORTCUTS_FILE, "w", encoding="utf-8") as f:
        json.dump(custom, f, ensure_ascii=False, indent=2)


def get_shortcuts() -> dict[str, str]:
    global _cache
    if _cache is None:
        _cache = _read_shortcuts()
    return _cache


def _save(shortcuts: dict[str, str]):
    global _cache
    _cache = shortcuts
    _write_shortcuts(shortcuts)


@app.on_message(filters.command("shortcut", prefixes=config.CMD_PREFIX) & filters.me)
def shortcut_command(client, message):
    args = message.command[1:]
    shortcuts = get_shortcuts()

    if not args or args[0].lower() == "list":
        lines = "\n".join(f"`{config.CMD_PREFIX}{name}` — {text}" for name, text in sorted(shortcuts.items()))
        message.edit_text(f"⚡ **Шорткаты ({len(shortcuts)}):**\n{lines}")
        return

    action = args[0].lower()
    if action == "add":
        if len(args) < 2:
            message.edit_text("❌ Формат: `.shortcut add name текст` или ответом `.shortcut add name`")
            return
        name = args[1].lower().strip()
        text = " ".join(args[2:]).strip()
        if not text and message.reply_to_message:
            text = (
                message.reply_to_message.text
                or message.reply_to_message.caption
                or ""
            ).strip()
        if not text:
            message.edit_text("❌ Дай текст шортката или ответь на сообщение.")
            return
        if not name.isalnum():
            message.edit_text("❌ Название шортката должно быть из букв и цифр.")
            return
        shortcuts[name] = text
        _save(shortcuts)
        message.edit_text(f"✅ Шорткат `.{name}` сохранён.")
        return

    if action == "remove":
        if len(args) < 2:
            message.edit_text("❌ Формат: `.shortcut remove name`")
            return
        name = args[1].lower().strip()
        if name in DEFAULT_SHORTCUTS:
            shortcuts[name] = DEFAULT_SHORTCUTS[name]
        elif name in shortcuts:
            del shortcuts[name]
        else:
            message.edit_text(f"❌ Шорткат `.{name}` не найден.")
            return
        _save(shortcuts)
        message.edit_text(f"✅ Шорткат `.{name}` удалён.")


@app.on_message(filters.me, group=50)
def shortcut_expander(client, message):
    text = message.text or ""
    prefix = getattr(config, "CMD_PREFIX", ".")
    if not text.startswith(prefix) or " " in text.strip():
        return

    name = text[len(prefix):].strip().lower()
    shortcuts = get_shortcuts()
    if name not in shortcuts or name == "shortcut":
        return

    message.edit_text(shortcuts[name])
