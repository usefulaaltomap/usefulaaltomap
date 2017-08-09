angular.module('usefulAaltoMap')
.controller('sidenavController', function($scope, mapService, $state, $mdSidenav, $timeout, utils, object) {


  $scope.objects = mapService.data;

  $scope.object = object;
  

  $scope.get_lang = utils.get_lang;

  $scope.name = utils.get_lang(object, 'name');
  var name = $scope.name;
  var name_en = utils.get_lang(object, 'name', 'en');
  var name_fi = utils.get_lang(object, 'name', 'fi');
  var name_sv = utils.get_lang(object, 'name', 'sv');
  if (name != name_en) $scope.name_en = name_en;
  if (name != name_fi) $scope.name_fi = name_fi;
  if (name != name_sv && name_sv != name_fi && name_sv != name_en)
    $scope.name_sv = utils.get_lang(object, 'name', 'sv');


  $scope.selectChild = function(id) {

  }

  $timeout(function() {
  	mapService.zoomOnObject(object)
  	
  	$mdSidenav('left').open();

	$mdSidenav('left').onClose(function () {
	  $timeout(function() {
	  	$state.go('app.map')
	  }, 200)
	});
  })

})