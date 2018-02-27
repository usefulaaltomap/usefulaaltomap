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

    // This function tests for building or building-like objects.
    function isBuilding(obj) {
	//return $scope.objects[obj].type == 'building' || $scope.objects[obj].type == 'wing';
	//return ['building', 'wing', 'studenthousing'].index($scope.objects[obj].type);
	return $scope.objects[obj].type in {'building':1, 'wing':1, 'studenthousing':1};
    }
    // Remove all non-buildings from a list.
    function filterNonBuildings(lst) {
	return lst.filter(function(x) { return !isBuilding(x) })
    }

  $scope.selectContains = function(object) {
      if (object.children == null) return [];
      return object.children.filter( function (c) {
	  return c in $scope.objects && ($scope.objects[c].parents == null || filterNonBuildings($scope.objects[c].parents).length <= 1)
      } )
  }

  $scope.selectContainsPartOf = function(object) {
      if (object.children == null) return [];
      return object.children.filter( function (c) {
	  return c in $scope.objects && ($scope.objects[c].parents != null && filterNonBuildings($scope.objects[c].parents).length > 1)
      } )
  }

  $scope.selectContainedIn = function(object) {
      if (object.parents == null) return [];
      return object.parents.filter( function (p) {
	  return p in $scope.objects && isBuilding(p)
      } )
  }

  $scope.selectPartOf = function(object) {
      if (object.parents == null) return [];
      return object.parents.filter( function (p) {
	  return p in $scope.objects && ! isBuilding(p)
      } )
  }

  $scope.getURL = function(object) {
    return $scope.get_lang(object, 'url');
  }


})
