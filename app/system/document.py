"""Набор классов реализующих базовые методы для работы с MongoDB.

Через них будет происходить обращение к базе данных и тут будут реализованы методы исправляющие некоторые косяки
при работе с MotorEngine и другими библиотеками для доступа к БД.

"""
import motorengine.fields.datetime_field
from motorengine import Document
from motorengine.queryset import QuerySet
from motorengine import BaseField, StringField, IntField, FloatField, JsonField, DateTimeField

list_simple_types = [StringField, IntField, FloatField, JsonField, DateTimeField]


class BaseDocument(Document):
    """Базовый документ.

    От него необходимо наследовать все документы с котороыми будет происходить работа.

    """

    def __init__(self, **kw):
        """Инициализация воспроизводит действия основного документа-родителя"""
        Document.__init__(self, **kw)

    def to_json(self) -> dict:
        """Подготовка документа для перевода его в JSON."""
        data = {'id': str(self._id)}

        for name, field in list(self._fields.items()):
            value = self.get_field_value(name)

            try:
                result = field.to_son(value)
            except Exception:
                result = value

            if type(result) is list:
                result = list(map(str, result))
            elif type(result) is dict:
                # result = list(map(str, result))
                pass
            else:
                result = str(result)

            data[field.db_field] = result

        return data

    def _is_simple_field(self, field: BaseField) -> bool:
        """Метод проверит отношение предаваемого поля к типам не составных полей.

        :param field: Поле из документа - наследик базового типа BaseField;
        :type field: BaseField
        :return: True если поле относится к простым типам;
        :rtype: bool
        """
        for simple_type in list_simple_types:
            if isinstance(field, simple_type):
                return True
        return False

    def fill_document_from_dict(self, dict_with_data: dict) -> None:
        """Заполнит документ по совпадающим полям из переданного словаря.

        Составные поля из других документов и списки игнорируются.

        :param dict_with_data: Словарь с данными для заполнения документа;
        :type dict_with_data: dict
        """
        for name, field in list(self._fields.items()):
            if name in dict_with_data:
                if self._is_simple_field(field):
                    val = dict_with_data[name]
                    # Для простых полей проводятся дополнительные проверки при несовпадении типа нового значения.
                    if isinstance(val, list):
                        val = val[0]
                    else:
                        val = str(val)

                    # Байтовые строки приводим к обычным.
                    if isinstance(val, bytes):
                        val = val.decode('utf-8')
                    setattr(self, name, val)

# Хаки по восполнению недостающего функционала.


def sort(self, field_name, direction=1):
    """Функция сортировки order_by имеет левые проверки которые позволяют применять сортировку только по полям главной модели.

    :param field_name:
    :param direction:
    :return:
    """
    self._order_fields.append((field_name, direction))
    return self

QuerySet.sort = sort

# Добавление микросекунд к парсингу времени
motorengine.fields.datetime_field.FORMAT = "%Y-%m-%d %H:%M:%S.%f"
