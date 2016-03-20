"""Документы для хранения информации по пользователям."""
from motorengine import StringField
from system.document import BaseDocument


class UserDocument(BaseDocument):
    """Пользовательская информация.

    :type name: str Имя для идентификации пользователя;
    :type password: str Пароль для авторизации пользователя;
    """
    __collection__ = "user"

    username = StringField(required=True, unique=True)
    password = StringField(required=True)
