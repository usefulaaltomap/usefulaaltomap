/* Config constants TODO: NON-GLOBAL?*/
var BUILDING_DEFAULT_OUTLINE_WEIGHT = 1;
var BUILDING_DEFAULT_FILL_OPACITY = 0.1;
var BUILDING_HIGHLIGHT_OUTLINE_WEIGHT = 2;
var BUILDING_HIGHLIGHT_FILL_OPACITY = 0.2;
var LANG = "en";

angular.module('usefulAaltoMap', ['ui-leaflet', 'ui.router', 'ngMaterial'])
.config(function($stateProvider, $urlRouterProvider) {
  $urlRouterProvider.otherwise('/')

  $stateProvider
  .state('app', {
    abstract: true,
    views: {
      'main': {
        templateUrl: 'main/main.html',
        controller: 'main',
        resolve: {
          initApp: function($http, mapService, utils) {

            function addBuilding(d) {
              if (d.outline) {
                message = utils.get_lang(d, "name")
                if (d.aliases && d.aliases.length > 0)
                   message += "\n<br> (" + d.aliases.join(", ") + ")";
                mapService.map.paths[d.id] = {
                  clickable: true,
                  weight: BUILDING_DEFAULT_OUTLINE_WEIGHT,
                  fill: true,
                  fillColor: 'red',
                  fillOpacity: BUILDING_DEFAULT_FILL_OPACITY,
                  latlngs: d.outline.map(function(coords) {
                    return {
                      lat: coords[0],
                      lng: coords[1]
                    }
                  }),
                  data: d,
                  mouseoverMessage: message
                }
              }
            }


            return $http.get('data.json')
            .then(function(res) {
              mapService.data = { };
              angular.forEach(res.data.locations, function(d) {
                mapService.data[d.id] = d;
              })
              // Add objects to map
              angular.forEach(mapService.data, function(d) {
                switch (d.type) {
                  case 'building':
                    addBuilding(d)
                    break;
                  default:
                    // do nothing
                }
              })
            })
            .catch(console.log)
          }
        }
      },
      '': {
        template: '<div ui-view></div>'
      }
    }
  })
  .state('app.map', {
    template: '',
    url: '/'
  })
  .state('app.selectedObject', {
    templateUrl: '/sidenav/sidenav.html',
    controller: 'sidenavController',
    url: '/select/:objectId',
    resolve: {
      object: function($stateParams, mapService, $q, $state, $timeout) {

        var objId = $stateParams.objectId;

        function waitForInit() {
          var deferred = $q.defer();
          if (mapService.data) { return $q.resolve(mapService.data) }
          else {
            return $timeout(waitForInit, 100);
          }
        }

        return waitForInit()
        .then(function(data) {
          var obj = mapService.data[objId];
          if (obj) {
            return $q.resolve(obj);
          }
          else {
            console.log("No object found with id " + objId)
            $state.go('app.map')
          }
        })
        .catch(console.log)
      }
    }
  })
})