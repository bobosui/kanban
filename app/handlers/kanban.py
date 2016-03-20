"""Обработчики для работы Kanban."""
import system.handler
import system.utils.exceptions
import collections
from documents.kanban import BoardDocument, CardDocument, ListCardsDocument, UserDocument
from bson.objectid import ObjectId


class BoardListHandler(system.handler.MainHandler):
    """Обработчики списка досок для пользователя."""

    async def get(self):
        """Получение списка досок доступных для пользователя."""
        document_user = await self.get_data_current_user()

        collection_board = await BoardDocument().objects.filter({BoardDocument.users.name: {"$in": [ObjectId(document_user._id)]}}).find_all()

        boards = [document_board.to_json() for document_board in collection_board]
        raise system.utils.exceptions.Result(content={"boards": boards})


class BoardItemHandler(system.handler.MainHandler):
    """Обработчики для работы с экземпляром доски."""

    async def get(self, board_id: str):
        """Получение всех списков конкретной доски и связанной с ними информации."""
        document_user = await self.get_data_current_user()
        collection_board = await BoardDocument().objects.filter({"_id": ObjectId(board_id)}).find_all()
        if not collection_board:
            raise system.utils.exceptions.NotFound()
        document_board = collection_board[-1]

        if not document_board.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        result = {
            "board": document_board.to_json()
        }

        # Для сохранения порядка в списках карточек используется OrderedDict
        result["board"]["lists"] = collections.OrderedDict()
        collection_list_cards = await ListCardsDocument()\
            .objects\
            .filter({ListCardsDocument.board.name: ObjectId(board_id)})\
            .sort(ListCardsDocument.position.name)\
            .find_all()

        for document_list_cards in collection_list_cards:
            result["board"]["lists"][str(document_list_cards._id)] = document_list_cards.to_json()
            collection_card = await CardDocument().objects.filter({CardDocument.listCards.name: ObjectId(document_list_cards._id)})\
                .sort(CardDocument.position.name)\
                .find_all()

            result["board"]["lists"][str(document_list_cards._id)]["cards"] = [document_card.to_json() for document_card in collection_card]

        collection_user = await UserDocument()\
            .objects\
            .filter({"_id": {"$in": document_board.users}})\
            .find_all()
        result["board"]["users"] = [document_user.username for document_user in collection_user]

        raise system.utils.exceptions.Result(content=result)

    async def post(self):
        """Создание новой доски для пользователя."""
        document_board = BoardDocument()
        document_board.fill_document_from_dict(self.get_bytes_body_source())

        document_user = await self.get_data_current_user()
        document_board.users = [ObjectId(document_user._id)]
        await document_board.save()
        raise system.utils.exceptions.Result(content={"boardId": str(document_board._id)})

    async def put(self):
        """Изменение информации по конкретной доске."""
        board_id = self.get_bytes_body_argument("boardId")
        collection_board = await BoardDocument().objects.filter({"_id": ObjectId(board_id)}).find_all()
        if not collection_board:
            raise system.utils.exceptions.NotFound()
        document_board = collection_board[-1]

        document_user = await self.get_data_current_user()
        if not document_board.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        document_board.fill_document_from_dict(self.get_bytes_body_source())
        await document_board.save()

        raise system.utils.exceptions.Result(content={})

    async def patch(self):
        """Изменение доступа пользователей к конкретной доске."""
        board_id = self.get_bytes_body_argument("boardId")
        username = self.get_bytes_body_argument("username")
        append = bool(self.get_bytes_body_argument("append"))

        collection_board = await BoardDocument().objects.filter({"_id": ObjectId(board_id)}).find_all()
        if not collection_board:
            raise system.utils.exceptions.NotFound()
        document_board = collection_board[-1]

        # Сам себя пользователь не может редактировать в правах доступа к доске
        document_user = await self.get_data_current_user()
        if (not document_board.check_permission(document_user)) or (document_user.username == username):
            raise system.utils.exceptions.ContentError()

        collection_user = await UserDocument().objects.filter({UserDocument.username.name: username}).find_all()
        if not collection_user:
            raise system.utils.exceptions.NotFound()
        document_user = collection_user[-1]

        if append:
            # Добавление нового пользователя к доске.
            if not str(document_user._id) in document_board.users:
                document_board.users.append(document_user._id)
                await document_board.save()
        else:
            # Удаление пользователя из спика, кому доступна доска.
            document_board.users = list(map(ObjectId, document_board.users))
            document_board.users.remove(document_user._id)
            await document_board.save()

        raise system.utils.exceptions.Result(content={})


class ListCardsHandler(system.handler.MainHandler):
    """Обработчики для работы с конкретным списком карточек."""

    async def get(self, list_cards_id: str):
        """Информация по определенному списку задач."""
        collection_list_cards = await ListCardsDocument().objects.filter({"_id": ObjectId(list_cards_id)}).find_all()
        if not collection_list_cards:
            raise system.utils.exceptions.NotFound()
        document_list_cards = collection_list_cards[-1]

        document_user = await self.get_data_current_user()
        if not await document_list_cards.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        result = {"listCards": document_list_cards.to_json()}
        collection_card = await CardDocument()\
            .objects\
            .filter({CardDocument.listCards.name: ObjectId(document_list_cards._id)})\
            .sort(CardDocument.position.name)\
            .find_all()

        result["listCards"]["cards"] = [document_card.to_json() for document_card in collection_card]

        raise system.utils.exceptions.Result(content=result)

    async def post(self):
        """Создание нового списка карточек."""
        board_id = self.get_bytes_body_argument("boardId")

        collection_board = await BoardDocument().objects.filter({"_id": ObjectId(board_id)}).find_all()
        if not collection_board:
            raise system.utils.exceptions.NotFound()
        document_board = collection_board[-1]

        document_user = await self.get_data_current_user()
        if not document_board.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        count_list_cards = await ListCardsDocument().objects.filter({ListCardsDocument.board.name: ObjectId(board_id)}).count()

        document_list_cards = ListCardsDocument()
        document_list_cards.fill_document_from_dict(self.get_bytes_body_source())
        document_list_cards.board = document_board._id
        document_list_cards.position = count_list_cards + 1
        await document_list_cards.save()
        raise system.utils.exceptions.Result(content=document_list_cards.to_json())

    async def put(self):
        """Редактирование существующего списка карточек."""
        list_cards_id = self.get_bytes_body_argument("listCardsId")
        title = self.get_bytes_body_argument("title")

        collection_list_cards = await ListCardsDocument().objects.filter({"_id": ObjectId(list_cards_id)}).find_all()
        if not collection_list_cards:
            raise system.utils.exceptions.NotFound()
        document_list_cards = collection_list_cards[-1]

        document_user = await self.get_data_current_user()
        if not await document_list_cards.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        document_list_cards.title = title
        await document_list_cards.save()

        raise system.utils.exceptions.Result(content={})

    async def patch(self):
        """Перенос карточек (пересортировка) с одной позиции в другую и сохранение этих изменений."""
        list_cards_id = self.get_bytes_body_argument("listCardsId")
        cards = self.get_bytes_body_argument("cards")

        collection_list_cards = await ListCardsDocument().objects.filter({"_id": ObjectId(list_cards_id)}).find_all()
        if not collection_list_cards:
            raise system.utils.exceptions.NotFound()
        document_list_cards = collection_list_cards[-1]

        document_user = await self.get_data_current_user()
        if not await document_list_cards.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        # Выстраивание карточек по переданному порядку и обновление их принадлежности к списку.
        collection_card = await CardDocument().objects.filter({"_id": {"$in": list(map(ObjectId, cards))}}).find_all()
        for document_card in collection_card:
            document_card.listCards = document_list_cards
            document_card.position = cards.index(str(document_card._id))
            await document_card.save()

        raise system.utils.exceptions.Result(content={})


class CardHandler(system.handler.MainHandler):
    """Обработчики для работы с конкретной карточкой."""

    async def post(self):
        """Создание новой карточки."""
        list_cards_id = self.get_bytes_body_argument("listCardsId")

        collection_list_cards = await ListCardsDocument().objects.filter({"_id": ObjectId(list_cards_id)}).find_all()
        if not collection_list_cards:
            raise system.utils.exceptions.NotFound()
        document_list_cards = collection_list_cards[-1]

        document_user = await self.get_data_current_user()
        if not await document_list_cards.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        count_card = await CardDocument().objects.filter({CardDocument.listCards.name: ObjectId(document_list_cards._id)}).count()

        document_card = CardDocument()
        document_card.fill_document_from_dict(self.get_bytes_body_source())
        document_card.listCards = document_list_cards
        document_card.position = count_card + 1

        await document_card.save()
        raise system.utils.exceptions.Result(content={})

    async def delete(self, card_id: str):
        """Редактирование существующей карточки."""
        collection_card = await CardDocument().objects.filter({"_id": ObjectId(card_id)}).find_all()
        if not collection_card:
            raise system.utils.exceptions.NotFound()
        document_card = collection_card[-1]

        document_user = await self.get_data_current_user()
        if not await document_card.check_permission(document_user):
            raise system.utils.exceptions.ContentError()

        await document_card.delete()

        raise system.utils.exceptions.Result(content={})
