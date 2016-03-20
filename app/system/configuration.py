"""Файл конфигурации системы.

Содержит настройки подключения к внешним ресурсам, роутинг и настройки работы системы.

todo реализовать проверки по наличию соединений с базой, кешем и др.

"""

from tornado.options import define
import motorengine
import system.handler

import handlers.kanban


# Базовые настройки запуска системы
SYSTEM_PORT = 8888
define("port", default=SYSTEM_PORT, help="run on the given port", type=int)

# Роутинг
handlers = [
    # Index
    (r"/_/logout", system.handler.LogoutHandler),
    (r"/_/login", system.handler.LoginHandler),

    # Kanban
    (r"/_/boards", handlers.kanban.BoardListHandler),
    (r"/_/board", handlers.kanban.BoardItemHandler),
    (r"/_/board/([\w-]+)", handlers.kanban.BoardItemHandler),

    (r"/_/list", handlers.kanban.ListCardsHandler),
    (r"/_/list/([\w-]+)", handlers.kanban.ListCardsHandler),
    (r"/_/card", handlers.kanban.CardHandler),
    (r"/_/card/([\w-]+)", handlers.kanban.CardHandler),
]

# Настройки подключения к базе данных MongoDB
DB_HOST = "localhost"
DB_PORT = 27017
DB_NAME = "kanban"

motorengine.connect(db=DB_NAME, host=DB_HOST, port=DB_PORT)

# Настройки приложения - доступны внутри хендлеров через self.settings
settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url": "/login",
}
