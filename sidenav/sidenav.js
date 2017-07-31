angular.module('usefulAaltoMap')
.controller('sidenavController', function($scope, mapService, $state, $mdSidenav, $timeout, utils, object) {


  $scope.objects = mapService.data;

  $scope.object = object;
  

  $scope.get_lang = utils.get_lang;

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