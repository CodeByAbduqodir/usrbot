# handlers/help.py
from pyrogram import filters
from bot import app
import config

HELP_TEXT = f"""**Userbot — команды** (`{config.CMD_PREFIX}`)

**Основное**
`{config.CMD_PREFIX}ping` — проверка работы бота
`{config.CMD_PREFIX}status` — CPU, RAM, диск, аптайм сервера
`{config.CMD_PREFIX}help` — это сообщение

**Карты**
`{config.CMD_PREFIX}card` — показать все карты (номер скрыт)
`{config.CMD_PREFIX}card full` — показать с полным номером
`{config.CMD_PREFIX}card note` — показать с примечанием первым
`{config.CMD_PREFIX}card <название/номер>` — найти карту

**Чёрный список слов**
`{config.CMD_PREFIX}badword <слово>` — добавить слово
`{config.CMD_PREFIX}badword` _(ответом)_ — добавить все слова из сообщения
`{config.CMD_PREFIX}badword remove <слово>` — удалить слово
`{config.CMD_PREFIX}badword list` — список слов
→ Сообщения с запрещёнными словами удаляются автоматически в группах где ты админ

**Авто-удаление пользователя**
`{config.CMD_PREFIX}keepdelete` _(ответом)_ — удалять все сообщения от юзера
`{config.CMD_PREFIX}keepdelete @username` — то же по юзернейму
`{config.CMD_PREFIX}keepdelete remove` _(ответом)_ — убрать из списка
`{config.CMD_PREFIX}keepdelete list` — список юзеров

**Инфо**
`{config.CMD_PREFIX}id` — ID текущего чата; ответом — ID юзера и сообщения
`{config.CMD_PREFIX}whois` _(ответом / @username)_ — подробная инфа о пользователе

**Мут**
`{config.CMD_PREFIX}mute` _(ответом)_ — замьютить навсегда
`{config.CMD_PREFIX}mute 10m` _(ответом)_ — замьютить на 10 минут
`{config.CMD_PREFIX}mute @username 2h` — замьютить на 2 часа
`{config.CMD_PREFIX}unmute` _(ответом / @username)_ — размьютить
→ Единицы: `s` сек, `m` мин, `h` часы, `d` дни"""


@app.on_message(filters.command("help", prefixes=config.CMD_PREFIX) & filters.me)
def help_handler(client, message):
    message.edit_text(HELP_TEXT)
