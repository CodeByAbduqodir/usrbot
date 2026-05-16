# handlers/card.py
from pyrogram import filters, enums, types
from bot import app
import config


def _utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def _match_card(cards, selector: str):
    selector = selector.strip().lower()
    if not selector:
        return cards
    if selector.isdigit():
        i = int(selector) - 1
        return [cards[i]] if 0 <= i < len(cards) else []
    return [c for c in cards if any(
        selector in str(c.get(f, "")).lower()
        for f in ("title", "holder", "note", "number")
    )]


def _format_card_number(number: str) -> str:
    digits = "".join(ch for ch in str(number) if ch.isdigit())
    if not digits:
        return str(number)
    return " ".join(digits[i:i + 4] for i in range(0, len(digits), 4))


def _build_message(cards):
    lines = []
    entities = []

    def current_offset():
        return sum(_utf16_len(l) + 1 for l in lines)

    for i, card in enumerate(cards):
        title = card.get("title", f"Card {i + 1}")
        holder = card.get("holder", "")
        number = _format_card_number(card.get("number", ""))
        note = card.get("note", "")

        header = f"💳 {title.upper()}"
        if note:
            header += f"\n   {note}"
        lines.append(header)

        if holder:
            lines.append(f"👤 {holder}")

        prefix = "📋 "
        entities.append(types.MessageEntity(
            type=enums.MessageEntityType.BANK_CARD,
            offset=current_offset() + _utf16_len(prefix),
            length=_utf16_len(number),
        ))
        lines.append(f"{prefix}{number}")

        if i < len(cards) - 1:
            lines.append("━━━━━━━━━━━━")

    return "\n".join(lines), entities


@app.on_message(filters.command(["card", "karta"], prefixes=config.CMD_PREFIX) & filters.me)
def card_handler(client, message):
    selector = " ".join(message.command[1:]).strip()
    cards = _match_card(config.CARDS, selector)

    if not cards:
        message.edit_text("❌ Карта не найдена.")
        return

    text, entities = _build_message(cards)
    message.edit_text(text, entities=entities)
