angular.module('usefulAaltoMap')
.controller('sidenavController', function($scope, mapService, $state, $mdSidenav, $timeout, utils, object, routeIdx) {


  $scope.objects = mapService.data;

  $scope.object = object;
  $scope.routeIdx = routeIdx.value === null ? false : routeIdx.value;

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

  $scope.goToState = function(stateName, params) {
    $state.go(stateName, params);
  }

  $scope.selectChild = function(id) {

  }

  $timeout(function() {
    //TODO: avoid animated menu when changing route
  	routeIdx.value === null ? mapService.zoomOnObject(object) : mapService.zoomOnRoute(object,routeIdx.value);
  	
  	$mdSidenav('left').open();

	$mdSidenav('left').onClose(function () {
	  $timeout(function() {
	  	$state.go('app.map')
	  }, 200)
	});
  })

  $scope.selectContains = function(object) {
      if (object.children == null) return [];
      return object.children.filter( function (c) {
	  return c in $scope.objects && ($scope.objects[c].parents == null || $scope.objects[c].parents.length <= 1)
      } )
  }

  $scope.selectContainsPartOf = function(object) {
      if (object.children == null) return [];
      return object.children.filter( function (c) {
	  return c in $scope.objects && ($scope.objects[c].parents != null && $scope.objects[c].parents.length > 1)
      } )
  }

  $scope.selectContainedIn = function(object) {
      if (object.parents == null) return [];
      return object.parents.filter( function (p) {
	  return p in $scope.objects && $scope.objects[p].type == 'building'
      } )
  }

  $scope.selectPartOf = function(object) {
      if (object.parents == null) return [];
      return object.parents.filter( function (p) {
	  return p in $scope.objects && $scope.objects[p].type != 'building'
      } )
  }

  $scope.getURL = function(object) {
    return $scope.get_lang(object, 'url');
  }

  $scope.highlightStage = function(activeStage){
    mapService.drawRoute($scope.object,$scope.routeIdx,activeStage);
  }

  $scope.selectedStage=0;

})
