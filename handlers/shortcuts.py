# handlers/shortcuts.py
import json
import os
import re
from pyrogram import filters, enums, types
from bot import app
import config

SHORTCUTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shortcuts.json")
MONO_RE = re.compile(r"`([^`\n]+)`")
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}\d(?!\d)")

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


def _decode_shortcut_text(text: str) -> str:
    return text.replace("\\n", "\n").replace("\\t", "\t")


def _preview(text: str, limit: int = 60) -> str:
    text = text.replace("\n", "\\n")
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _mono_entity(offset: int, value: str):
    return types.MessageEntity(
        type=enums.MessageEntityType.CODE,
        offset=offset,
        length=_utf16_len(value),
    )


def _render_shortcut(text: str):
    output = []
    entities = []
    cursor = 0

    for match in MONO_RE.finditer(text):
        before = text[cursor:match.start()]
        output.append(before)
        value = match.group(1)
        offset = _utf16_len("".join(output))
        output.append(value)
        entities.append(_mono_entity(offset, value))
        cursor = match.end()

    output.append(text[cursor:])
    rendered = "".join(output)

    occupied = [
        (entity.offset, entity.offset + entity.length)
        for entity in entities
    ]
    for match in CARD_RE.finditer(rendered):
        value = match.group(0).strip()
        if len(re.sub(r"\D", "", value)) < 14:
            continue
        offset = _utf16_len(rendered[:match.start()])
        length = _utf16_len(value)
        if any(not (offset + length <= start or offset >= end) for start, end in occupied):
            continue
        entities.append(_mono_entity(offset, value))

    return rendered, entities


@app.on_message(filters.command("shortcut", prefixes=config.CMD_PREFIX) & filters.me)
def shortcut_command(client, message):
    args = message.command[1:]
    shortcuts = get_shortcuts()

    if not args or args[0].lower() == "list":
        lines = "\n".join(
            f"`{config.CMD_PREFIX}{name}` — {_preview(text)}"
            for name, text in sorted(shortcuts.items())
        )
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
        text = _decode_shortcut_text(text)
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

    text, entities = _render_shortcut(shortcuts[name])
    message.edit_text(text, entities=entities)
