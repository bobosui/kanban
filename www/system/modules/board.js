chimera.system.board = angular.module("board", ["ngResource", "ngSanitize"]);

/**
 * BoardListMainHandler - Контроллер для списка доступных досок.
 */
chimera.system.board.controller("BoardListController", ["$scope", "$state", "boardListService", "boardItemService",
    function ($scope, $state, boardListService, boardItemService) {
        $scope.main.contentLoad = true;
        boardListService.get({}, function (response) {
            $scope.boards = response.content.boards;
            $scope.main.contentLoad = false;
        });

        // Создание новой доски и редирект на ее страницу в случае успешного создания.
        $scope.addBoard = function () {
            bootbox.prompt("Введите название доски", function (title) {
                if (title) {
                    boardItemService.save({title: title}).$promise.then(function (response) {
                        if (response.error.code == 0) {
                            $.notify("Доска создана", "success");
                            $state.go("main.board", {"boardId": response.content.boardId});
                        }
                    });
                }

            });
        };
    }
]);

/**
 * BoardItemHandler - Контрллер для работы с определенной доской.
 *
 * Включает в себя методы по управлению списками, карточками и пользователями.
 */
chimera.system.board.controller("BoardItemController", ["$scope", "$state", "boardItemService", "listCardsService", "cardService",
    function ($scope, $state, boardItemService, listCardsService, cardService) {
        var refreshBoard, refreshListCards, changeUsers;

        /**
         * Обновление данных доски и инициализация jq ui плагина для сортировки карточек.
         */
        refreshBoard = function () {
            $scope.main.contentLoad = true;
            boardItemService.get({boardId: $state.params.boardId}, function (response) {
                $scope.board = response.content.board;
                $scope.main.contentLoad = false;

                // Инициализация сортировки карточек
                $scope.$watch("board", function () {
                    console.log($(".list-cards__items"));
                    $(".list-cards__items").sortable({
                        connectWith: ".list-cards__items",
                        /**
                         * Завершение сортировки. Определение текущего положения элемента и отправка актуальных данных на сервер.
                         */
                        stop: function (event, ui) {
                            var cardId = $(ui.item).data("card-id"),
                                $listCards = $(ui.item).closest(".list-cards")
                            listCardsId = $listCards.data("list-cards-id");

                            cards = _.map($listCards.find(".card"), function (card) {
                                return $(card).data("card-id");
                            });
                            listCardsService.reorder({cards: cards, listCardsId: listCardsId}).$promise.then(function (response) {
                                if (response.error.code == 0) {
                                    $.notify("Порядок сохранен", "success");
                                }
                            });
                            console.log(cardId, listCardsId, cards);
                        }
                    });
                });
            });
        };

        /**
         * Обновление данных определенного списка.
         */
        refreshListCards = function (listCardsId) {
            $scope.main.contentLoad = true;
            listCardsService.get({listCardsId: listCardsId}, function (response) {
                $scope.board.lists[listCardsId] = response.content.listCards;
                $scope.main.contentLoad = false;
            });
        };

        /**
         * Изменение доступа пользователей к текущей доске.
         */
        changeUsers = function (username, boardId, append) {
            if (username) {
                boardItemService.changeUsers({username: username, boardId: boardId, append: append}).$promise.then(function (response) {
                    if (response.error.code == 0) {
                        $.notify("Список пользователей обновлен", "success");
                        refreshBoard();
                    }
                });
            }
        };

        refreshBoard();

        /**
         * Добавление к доске нового списка карточек.
         */
        $scope.addListCards = function () {
            bootbox.prompt("Введите название списка задач", function (title) {

                if (title) {
                    listCardsService.save({title: title, boardId: $state.params.boardId}).$promise.then(function (response) {
                        if (response.error.code == 0) {
                            $.notify("Список создан", "success");
                            refreshBoard();
                        }
                    });
                }
            });
        };

        /**
         * Изменение названия у списка карточек.
         */
        $scope.changeListCards = function (listCardsId, title) {
            bootbox.prompt({
                title: "Введите название списка задач",
                value: title,
                callback: function (title) {

                    if (title) {
                        listCardsService.update({title: title, listCardsId: listCardsId}).$promise.then(function (response) {
                            if (response.error.code == 0) {
                                $.notify("Список изменен", "success");
                                refreshBoard();
                            }
                        });
                    }
                }
            });
        };

        /**
         * Добавление новой задачи к списку карточек.
         */
        $scope.addCard = function (listCardsId) {
            bootbox.prompt("Введите текст задачи", function (message) {
                if (message) {
                    cardService.save({message: message, listCardsId: listCardsId}).$promise.then(function (response) {
                        if (response.error.code == 0) {
                            $.notify("Задача создана", "success");
                            refreshListCards(listCardsId)
                        }
                    });
                }
            });
        };

        /**
         * Удаление определенной карточки.
         */
        $scope.deleteCard = function (cardId, listCardsId) {
            bootbox.confirm("Удалить задачу?", function (result) {
                if (result) {
                    cardService.remove({cardId: cardId}).$promise.then(function (response) {
                        if (response.error.code == 0) {
                            $.notify("Задача удалена", "success");
                            refreshListCards(listCardsId)
                        }
                    });
                }
            });
        };

        /**
         * Изменение названия доски.
         */
        $scope.changeBoard = function (boardId, title) {
            bootbox.prompt({
                title: "Введите название доски",
                value: title,
                callback: function (title) {
                    if (title) {
                        boardItemService.update({title: title, boardId: boardId}).$promise.then(function (response) {
                            if (response.error.code == 0) {
                                $.notify("Доска изменена", "success");
                                refreshBoard();
                            }
                        });
                    }
                }
            });
        };

        /**
         * Добавление пользователя к работе с доской.
         */
        $scope.addUser = function (boardId) {
            bootbox.prompt({
                title: "Введите имя пользователя",
                value: '',
                callback: function (username) {
                    changeUsers(username, boardId, 1)
                }
            });
        };

        /**
         * Удаление пользователя.
         */
        $scope.deleteUser = function (boardId, username) {
            bootbox.confirm("Удалить " + username + " из списка пользователей доски?", function (result) {
                changeUsers(username, boardId, 0)
            });
        };

    }
]);

chimera.system.board.factory("cardService", ["$resource",
    function ($resource) {
        return $resource("/card/:cardId", {}, {
            save: {method: "POST", params: {cardId: null}},
        });
    }
]);

chimera.system.board.factory("listCardsService", ["$resource",
    function ($resource) {
        return $resource("/list/:listCardsId", {}, {
            save: {method: "POST", params: {listCardsId: null}},
            update: {method: "PUT", params: {listCardsId: null}},
            reorder: {method: "PATCH", params: {listCardsId: null}},
        });
    }
]);

chimera.system.board.factory("boardItemService", ["$resource",
    function ($resource) {
        return $resource("/board/:boardId", {}, {
            save: {method: "POST", params: {boardId: null}},
            update: {method: "PUT"},
            changeUsers: {method: "PATCH"}
        });
    }
]);

chimera.system.board.factory("boardListService", ["$resource",
    function ($resource) {
        return $resource("/boards");
    }
]);