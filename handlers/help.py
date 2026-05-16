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
`{config.CMD_PREFIX}card` — красиво показать все карты
`{config.CMD_PREFIX}card humo` — найти карту по названию/заметке/номеру
→ Номер отправляется как банковская сущность Telegram: тапнул — скопировал

**Чёрный список слов**
`{config.CMD_PREFIX}badword <слово>` — добавить слово
`{config.CMD_PREFIX}badword` _(ответом)_ — добавить все слова из сообщения
`{config.CMD_PREFIX}badword remove <слово>` — удалить слово
`{config.CMD_PREFIX}badword list` — список слов
→ Сообщения с запрещёнными словами удаляются автоматически в группах где ты админ

**Авто-удаление пользователя**
`{config.CMD_PREFIX}keepdelete` _(ответом)_ — удалять сообщения юзера в текущем чате
`{config.CMD_PREFIX}keepdelete @username 1h` — временное авто-удаление
`{config.CMD_PREFIX}keepdelete global @username` — во всех чатах
`{config.CMD_PREFIX}keepdelete remove` _(ответом)_ — убрать из списка
`{config.CMD_PREFIX}keepdelete list` — список юзеров с чатами и сроками

**AFK**
`{config.CMD_PREFIX}afk текст` — включить простой AFK
`{config.CMD_PREFIX}afk off` — выключить простой AFK
`{config.CMD_PREFIX}afk night 23:00 08:00 текст` — ночной AFK
`{config.CMD_PREFIX}afk cooldown 6h` — кулдаун автоответа на человека
`{config.CMD_PREFIX}afk status` — статус AFK

**Шорткаты**
`{config.CMD_PREFIX}shrug`, `{config.CMD_PREFIX}brb`, `{config.CMD_PREFIX}gm`, `{config.CMD_PREFIX}gn`, `{config.CMD_PREFIX}ty`
`{config.CMD_PREFIX}shortcut list` — список
`{config.CMD_PREFIX}shortcut add name текст` — добавить свой

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
