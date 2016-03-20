"""Группа основных обработчиков запросов по выводу результатов работы, авторизации в системе, обработки исключений и т.д.

Основной обработчик запросов торнадо tornado.web.RequestHandler от которого наследуем все остальные обработчики
через базовый BaseHandler в котором воплощены основные используемые функции.

GET — получение;
POST — создание;
PUT — обновление;
DELETE — удаление;
"""
import tornado.web
import tornado.escape
import system.utils.exceptions
from json.decoder import JSONDecodeError
from documents.user import UserDocument


class BaseHandler(tornado.web.RequestHandler):
    """BaseHandler - основной перекрытый обработчик от которого наследовать все остальные."""

    def initialize(self):
        """Инициализация базового обработчика запросов."""
        pass

    def on_finish(self):
        """Завершение обработки запроса.

        Не может редактировать содержимое выводимого результата (не может ничего отправлять пользователю в принципе).

        """

    def write_error(self, status_code, **kwargs):
        """Перехват ошибок и других событий возникающих через исключения.

        :param status_code:
        :param kwargs:
        """
        exc_info = kwargs['exc_info']
        type_exception = exc_info[0]
        exception = exc_info[1]
        traceback = exc_info[0]

        # Попытка привести исключение к строковому виду.
        if isinstance(exception, system.utils.exceptions.Result):
            # Успешная отработка запроса
            self.set_status(200)
            result = str(exception)
        elif isinstance(exception, system.utils.exceptions.ChimeraException):
            # Относительно успешная отработка запроса - исключение которое не было правильно обработано.
            result = str(exception)
        else:
            # Системное исключение которое было возбуждено феймворком - попытка отработать его корректно для клиента.
            result_message = system.utils.exceptions.ResultMessage(error_message=str(exception), error_code=1)
            result = str(result_message)

        # Вывод результата обработки исключения.
        self.write(result)
        self.finish()

    def set_default_headers(self):
        """Перекрытый метод установки ряда стандартных заголовков необходимых для CORS."""
        self.set_header('Content-Type', 'application/json; charset="utf-8"')

    def get_current_user(self):
        """Перекрытый метод определения пользователя."""
        return self.get_secure_cookie("chimera_user")

    async def options(self, *args, **kwargs):
        """Обработчик запроса по методу OPTIONS."""
        raise system.utils.exceptions.Result(content={"hello": "world"})

    async def get_data_current_user(self) -> UserDocument:
        """Вернет данные из базы по текущему пользователю."""
        username = self.get_current_user().decode()
        collection_user = await UserDocument().objects.filter({UserDocument.username.name: username}).find_all()

        if not collection_user:
            raise system.utils.exceptions.UserNotAuth()
        return collection_user[-1]

    def get_bytes_body_argument(self, name, default=None) -> str:
        """Вернет значение переданного параметра от клиента.

        Тестовый хак для обработки данных приходящих с приложения angular

        :param name: Название свойства (поля) с которого будут считываться данные;
        :param default: Значение по умолчанию в случае отсутствия данных;
        :return: Обычно данные будут приходить в строковом формате;
        """
        return self.get_bytes_body_source().get(name, default)

    def get_bytes_body_source(self) -> dict:
        """Вернет словарь пришедших данных от клиента.

        Декодировка данных в теле запроса self.request.body и представление в виде словаря.

        :return: dict с клиентскими данными;
        """
        try:
            body_arguments = tornado.escape.to_unicode(self.request.body)
            return tornado.escape.json_decode(body_arguments)
        except (TypeError, JSONDecodeError):
            return {}


class MainHandler(BaseHandler):
    """Главный обработчик наследники которого требуют авторизацию со стороны пользователя для своих действий."""

    def prepare(self):
        """Перекрытие срабатывает перед вызовом обработчиков и в случае отсутствия данных по пользователю возбуждает исключение."""
        if not self.get_current_user():
            raise system.utils.exceptions.UserNotAuth()


class LoginHandler(BaseHandler):
    """Класс через который будет проводится представление пользователя системе, прошедшего авторизацию."""

    async def post(self):
        """Авторизация."""
        username = self.get_bytes_body_argument("username")
        password = self.get_bytes_body_argument("password")

        result = {"auth": False}
        collection_user = await UserDocument().objects.filter({UserDocument.username.name: username}).find_all()
        if not collection_user:
            document_user = UserDocument()
            document_user.username = username
            document_user.password = password
            await document_user.save()
            result["auth"] = True
        else:
            document_user = collection_user[-1]
            if document_user.password == password:
                result["auth"] = True
            else:
                raise system.utils.exceptions.UserNotAuth()

        self.set_secure_cookie("chimera_user", username)

        raise system.utils.exceptions.Result(content=result)


class LogoutHandler(MainHandler):
    """Класс для выхода из системы - очистка кук."""

    async def get(self):
        """Сброс авторизации."""
        self.clear_cookie("chimera_user")
