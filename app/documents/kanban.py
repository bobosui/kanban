"""Документы для хранения информации по kanban."""
from motorengine import StringField, ListField, IntField, ReferenceField
from documents.user import UserDocument
from system.document import BaseDocument


class BoardDocument(BaseDocument):
    """Доска на которой размещены списки с карточками.

    Доска может быть доступна для нескольких пользователей.

    :type title: str Заголовок доски;
    :type listsCards: list Набор списков карточек для конкретной доски;
    :type users: list Список пользователей имеющий доступ к доске;
    """
    __collection__ = "board"

    title = StringField(required=True)
    users = ListField(ReferenceField(UserDocument))

    def check_permission(self, document_user: UserDocument):
        """Проверка прав доступа к текущему документу у определенного пользователя."""
        return document_user._id in self.users


class ListCardsDocument(BaseDocument):
    """Список с карточками.

    :type title: str Заголовок списка;
    :type cards: list Набор карточек актуальных для списка;
    :type position: int Порядковый номер позиции в ряде списков;
    """
    __collection__ = "listCards"
    __lazy__ = False

    title = StringField(required=True)
    position = IntField(required=True)
    board = ReferenceField(BoardDocument)

    async def check_permission(self, document_user: UserDocument):
        """Проверка прав доступа к текущему документу у определенного пользователя."""
        collection_board = await BoardDocument().objects.filter({"_id": self.board._id}).find_all()
        if not collection_board:
            return False
        document_board = collection_board[-1]
        return document_board.check_permission(document_user)


class CardDocument(BaseDocument):
    """Данные по карточке.

    :type message: str Текст сообщения карточки;
    :type position: int Порядковый номер позиции в списке карточек;
    """
    __collection__ = "card"
    __lazy__ = False

    message = StringField(required=True)
    position = IntField(required=True)
    listCards = ReferenceField(ListCardsDocument)

    async def check_permission(self, document_user: UserDocument):
        """Проверка прав доступа к текущему документу у определенного пользователя."""
        collection_list_cards = await ListCardsDocument().objects.filter({"_id": self.listCards._id}).find_all()
        if not collection_list_cards:
            return False
        document_list_cards = collection_list_cards[-1]
        return document_list_cards.check_permission(document_user)
