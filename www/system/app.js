/**
 *  App Module
 *
 *  Основной модуль - с конфигурациями и настройками.
 */

/**
 * Общий объект системы
 */
var chimera = {
    config: {
        baseUrl: "http://www.kanban.local/_",
        baseWWWUrl: "http://www.kanban.local"
    },
    system: {}
};


chimera.system.main = angular.module("main", [
    "ui.router",
    "board",
    "auth"
]);

/**
 * Перехват входящих/исходящих запросов.
 */
chimera.system.main.factory("sessionRecover", ["$q", "$location", function ($q, $location) {
    // Общая обработка ошибок.
    var parseError = function (error) {
        switch (error.code) {
            case 11:
                $.notify(error.message, "error");
                $location.path("/login").replace();
                break;
            default:
                $.notify(error.message, "error");
                break;
        }
    };

    return {
        /**
         * Роутинг запросов по статике и к системе.
         *
         * @param config
         * @returns {*}
         */
        request: function (config) {
            if (!s.startsWith(config.url, "//")) {
                // Внешние запросы остаются без модификаций.
                if (/.*\.(js|css|ico|htm|html|json)/.test(config.url)) {
                    // Запросы по статик файлам переадресуются на основной домен.
                    config.url = chimera.config.baseWWWUrl + config.url;
                } else {
                    // Запросы не относящиея к статик файлам идут к основной системе.
                    config.url = chimera.config.baseUrl + config.url;
                }
            }

            return config;
        },
        /**
         * Разбор ответов для определения соответствующей реакции на случай возникновения ошибок.
         *
         * @param response
         * @returns {*}
         */
        response: function (response) {
            var data = response.data;

            if (data && data.error && data.error.code) {
                parseError(data.error);
            }

            return response;
        },
        responseError: function (rejection) {
            var data = rejection.data;

            if (data && data.error && data.error.code) {
                parseError(data.error);
            }

            return $q.reject(rejection);
        }
    };
}]);

chimera.system.main.config(["$stateProvider", "$urlRouterProvider", "$locationProvider", "$httpProvider",
    function ($stateProvider, $urlRouterProvider, $locationProvider, $httpProvider) {
        // Перехват всех http запросов для определения ошибок и реакции на них.
        $httpProvider.interceptors.push("sessionRecover");
        // Отправка POST запросов в едином виде.
        //$httpProvider.defaults.headers.post = {"Content-Type": "application/x-www-form-urlencoded"};
        $httpProvider.defaults.headers.post = {"Content-Type": "multipart/form-data"};
        // html5Mode - без # в урле
        $locationProvider.html5Mode({
            enabled: true,
            requireBase: false
        });

        // Любые неопределенные url перенаправлять на страницу авторизации (при успешной авторизации произойдет редирект).
        $urlRouterProvider.otherwise("/login");

        // Определение состояний для всего приложения.
        $stateProvider
        /**
         * Форма входа.
         */
            .state("login", {
                url: "/login",
                views: {
                    "": {
                        templateUrl: "/system/templates/login.html",
                        controller: "AuthController"
                    }
                }
            })
        /**
         * Главное абстрактное состояние для системы. Включает в себя компоненты авторизованного пользователя
         * и основную контентную область.
         */
            .state("main", {
                abstract: true,
                url: "",
                views: {
                    "": {
                        templateUrl: "/system/templates/main.html",
                        controller: "ChimeraController"
                    }
                }
            })
            .state("main.boards", {
                url: "/boards",
                views: {
                    "content": {
                        templateUrl: "/system/templates/boards.html",
                        controller: "BoardListController"
                    }
                }
            })
            .state("main.board", {
                url: "/board/:boardId",
                views: {
                    "content": {
                        templateUrl: "/system/templates/board.html",
                        controller: "BoardItemController"
                    }
                }
            })
        ;

    }
]);

/**
 * Базовый контроллер.
 */
chimera.system.main.controller("ChimeraController", ["$scope", "$state", "authService",
    function ($scope, $state, authService) {
        $scope.main = {
            "title": "Kanban",
            "contentLoad": false,
            "foo": "BAAAAAR"
        };

        $scope.signOut = function () {
            authService.disconnect();
            $state.go("login");
        };

    }
]);

/**
 * Модуль авторизации.
 *
 * @type {module|*}
 */
chimera.system.auth = angular.module('auth', ['ngCookies']);

chimera.system.auth.controller("AuthController", ["$scope", "$state", "authService",
    function ($scope, $state, authService) {
        $scope.username = "";
        $scope.password = "";

        $scope.connectButton = function () {
            authService.connect($scope.username, $scope.password).then(function (response) {
                if (response.error.code == 0) {
                    $state.go("main.boards");
                }
            });
        };
    }
]);

chimera.system.auth.factory("authService", ["$q", "$http",
    function ($q, $http) {
        return {
            connect: function (username, password) {
                var deferred = $q.defer();

                $http.post("/login", {username: username, password: password}).success(function (data, status, headers, config) {
                    if (data.content.auth) {
                        deferred.resolve(data);
                    } else {
                        deferred.reject(data);
                    }
                });

                return deferred.promise;
            },
            disconnect: function () {
                $http.get("/logout");
            },
        }

    }
]);
