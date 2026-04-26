# config.example.py — скопируй в config.py и заполни своими данными
# Получить API_ID и API_HASH: https://my.telegram.org/apps

API_ID = 12345678
API_HASH = "your_api_hash_here"

SESSION_NAME = "my_userbot"

CMD_PREFIX = "."

LOG_CHAT_ID = None  # ID чата для логов удалённых сообщений (или None)

# Список банковских карт
CARDS = [
    {
        "title": "Humo",           # короткое название
        "holder": "Имя Фамилия",   # держатель карты
        "number": "0000 0000 0000 0000",  # номер карты
        "note": "Основная",        # примечание (опционально)
    },
]
