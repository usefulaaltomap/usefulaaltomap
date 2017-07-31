angular.module('usefulAaltoMap')
.controller('main', function($http, $scope, $state, leafletData, $mdSidenav, mapService, utils) {

$scope.zoomOnObject = mapService.zoomOnObject;
$scope.openSideNav = mapService.openSideNav;
$scope.searchQuerySelected = mapService.searchQuerySelected;


/* Utility methods */

$scope.get_lang = utils.get_lang;

function set_lang(lang) {
  // Set language.  This doesnt' work right now.
  LANG = lang;
}
$scope.set_lang = set_lang;

/* Core visualization methods */

  /*if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(args) {
      $scope.map.center.lat = args.coords.latitude;
      $scope.map.center.lng = args.coords.longitude;
    })
  }*/

  $scope.map = mapService.map;

  // When an object is selected.
  
  $scope.goToState = function(stateName, params) {
    console.log(params)
    $state.go(stateName, params);
  }

  $scope.zoomOnObjectById = function(id) {
    //if (! ('outline' in mapService.data[id] || 'latlon' in mapService.data[id]))
    //  openSidenav(mapService.data[id]);
    $scope.zoomOnObject(mapService.data[id]);
    openSidenav(id);
  }

  $scope.getItemText = function(selectedItem) {
    return $scope.get_lang(selectedItem, 'name') || selectedItem.id;
  }

  $scope.getItems = function(searchQuery) {
    searchQuery = searchQuery.toLowerCase();  // What user enters

    // Helper function for filtering search results
    function match(str, minmatch) {
      if (!str) return false;
      if (minmatch && searchQuery.length < minmatch) return false;
      // Searching for just a digit
      if (searchQuery.match('/^[0-9]{1,2}$/')) {
        return str.endsWith(searchQuery)
      }
      // Searching for a single letter - building letters
      else if (searchQuery.length == 1) {
        return str.toLowerCase() == searchQuery
      }
      // Searching for only two letters - match at start of each word only
      else if (searchQuery.length == 2) {
        return RegExp("\\b"+searchQuery, 'i').test(str)
      }
      // Generic search
      else {
        return str.toLowerCase().indexOf(searchQuery) > -1
      }
    }

    // Check if the query matches an alias
    function matchAliases(d) {
      var matched = false;
      angular.forEach(d.aliases, function(a) {
        if (match(a)) { matched = true };
      })
      return matched;
    }

    return _.filter(mapService.data, function(d) {
      return match(d.name) || match(d.name_fi) || match(d.name_en) || match(d.name_sv) || match(d.id) || matchAliases(d) || match(d.address, 7);
    })
  }

  function openSidenav(objId) {
    $state.go('app.selectedObject', {objectId: objId})
    /*.then(function() {
      return;
    })*/
  }

  $scope.$on('leafletDirectivePath.click', function(event, args) {
    event.preventDefault();
    openSidenav(args.modelName)
  })

  $scope.$on('leafletDirectivePath.mouseover', function(event, args) {
    var data = mapService.data[args.modelName]
    mapService.highlightObject(mapService.data[args.modelName]);
    var pxBounds = args.leafletObject._pxBounds;
    var popup = L.popup({autoPan: false, offset: {x: 0, y: -(pxBounds.max.y - pxBounds.min.y) / 2}})
      .setLatLng(data.latlon)
      .setContent(args.leafletObject.options.mouseoverMessage)
      .openOn(mapService.leafletMap)
  })

  $scope.$on('leafletDirectivePath.mouseout', function(event, args) {
    var path = $scope.map.paths[args.modelName];

    path.weight = BUILDING_DEFAULT_OUTLINE_WEIGHT;
    path.fillOpacity = BUILDING_DEFAULT_FILL_OPACITY;
  })
})