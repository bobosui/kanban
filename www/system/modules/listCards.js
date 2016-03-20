/**
 * Дирекива для построения списка карточек.
 */
chimera.system.main.directive('listCards', function () {
    return {
        restrict: 'EA',
        scope: {
            cards: '=',
            listCardsId: '=',
            deleteCard: '='
        },
        templateUrl: "/system/templates/listCards.html"
    };
});