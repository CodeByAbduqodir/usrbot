# handlers/badword.py
import os
import re
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from bot import app
import config

BADWORDS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "badwords.txt")

_cache: list[str] | None = None


def _read_file() -> list[str]:
    if not os.path.exists(BADWORDS_FILE):
        return []
    with open(BADWORDS_FILE, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def _write_file(words: list[str]):
    with open(BADWORDS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(words) + ("\n" if words else ""))


def get_words() -> list[str]:
    global _cache
    if _cache is None:
        _cache = _read_file()
    return _cache


def _invalidate():
    global _cache
    _cache = None


def _extract_words(text: str) -> list[str]:
    return list({w for w in re.findall(r'[а-яёa-z0-9]+', text.lower()) if len(w) >= 2})


@app.on_message(filters.command("badword", prefixes=config.CMD_PREFIX) & filters.me)
def badword_command(client, message):
    args = message.command[1:]

    # Reply mode: add all words from the replied message
    if not args and message.reply_to_message:
        replied_text = (
            message.reply_to_message.text or message.reply_to_message.caption or ""
        )
        if not replied_text:
            message.edit_text("❌ В том сообщении нет текста.")
            return

        extracted = _extract_words(replied_text)
        words = get_words()
        added = [w for w in extracted if w not in words]

        if not added:
            message.edit_text("⚠️ Все слова из этого сообщения уже в списке.")
            return

        words.extend(added)
        _write_file(words)
        _invalidate()
        preview = ", ".join(added[:10])
        suffix = f" (+ещё {len(added) - 10})" if len(added) > 10 else ""
        message.edit_text(f"✅ Добавлено {len(added)} слов: {preview}{suffix}")
        return

    if not args or args[0].lower() == "list":
        words = get_words()
        if not words:
            message.edit_text("📋 Список запрещённых слов пуст.")
        else:
            lines = "\n".join(f"{i}. {w}" for i, w in enumerate(words, 1))
            message.edit_text(f"📋 **Запрещённые слова ({len(words)}):**\n{lines}")
        return

    if args[0].lower() == "remove":
        if len(args) < 2:
            message.edit_text("❌ Укажи слово: `.badword remove <слово>`")
            return
        word = " ".join(args[1:]).lower()
        words = get_words()
        if word not in words:
            message.edit_text(f"❌ Слово «{word}» не найдено в списке.")
            return
        words.remove(word)
        _write_file(words)
        _invalidate()
        message.edit_text(f"✅ Слово «{word}» удалено из списка.")
        return

    word = " ".join(args).lower()
    words = get_words()
    if word in words:
        message.edit_text(f"⚠️ Слово «{word}» уже в списке.")
        return
    words.append(word)
    _write_file(words)
    _invalidate()
    message.edit_text(f"✅ Слово «{word}» добавлено в список запрещённых.")


@app.on_message(filters.group & ~filters.me)
def auto_delete_bad_words(client, message):
    words = get_words()
    if not words:
        return

    text = (message.text or message.caption or "").lower()
    if not text:
        return

    if not any(word in text for word in words):
        return

    try:
        me = client.get_me()
        member = client.get_chat_member(message.chat.id, me.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return
    except Exception:
        return

    try:
        message.delete()
    except Exception:
        pass
