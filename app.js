/* Config constants TODO: NON-GLOBAL?*/
var BUILDING_DEFAULT_OUTLINE_WEIGHT = 1;
var BUILDING_DEFAULT_FILL_OPACITY = 0.1;
var BUILDING_HIGHLIGHT_OUTLINE_WEIGHT_WEAK = 2;
var BUILDING_HIGHLIGHT_FILL_OPACITY_WEAK = 0.15;
var BUILDING_HIGHLIGHT_OUTLINE_WEIGHT_STRONG = 3;
var BUILDING_HIGHLIGHT_FILL_OPACITY_STRONG = 0.25;

var OBJECT_HIGHLIGHT_OUTLINE_WEIGHT_STRONG = 3;
var OBJECT_HIGHLIGHT_FILL_OPACITY_STRONG = .25;

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
                   message += "\n<br> <span class=aliases>(" + d.aliases.join(", ") + ")</span>";
                mapService.map.paths[d.id] = {
                  id: d.id,
                  data: d,
                  type: "polygon",
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
                  mouseoverMessage: message
                }
                mapService.resetColors(mapService.map.paths[d.id]);
              }
            }


            return $http.get('data.json')
            .then(function(res) {
              // All data: id -> {data}
              mapService.data = { };
              // Object IDs which should be displayed by default: id -> true
               mapService.defaultObjects = { };
              angular.forEach(res.data.locations, function(d) {
                mapService.data[d.id] = d;
              })
              // Redirections
              mapService.redirects = res.data.redirects;
              // Add objects to map
              angular.forEach(mapService.data, function(d) {
                switch (d.type) {
                  case 'building':
                  case 'auxbuilding':
                  case 'studenthousing':
                  case 'otherbuilding':
                    addBuilding(d);
		    mapService.defaultObjects[d.id] = true;
                    break;
                  default:
                    // do nothing
                }
              })
              mapService.clearHighlights();
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
    url: '/',
    resolve: {
      clearHighlights: function(mapService) {
        // Following line resets view when you leave sidenav.
        //mapService.clearHighlights();
      }
    }
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
          // Use the "redirects" data to see if our ID has been changed.
          if (mapService.redirects && objId in mapService.redirects) {
            var obj = mapService.data[mapService.redirects[objId]];
            if (obj) {
              $state.go("app.selectedObject", { objectId: mapService.redirects[objId] });
              return $q.resolve(obj); // unreachable, hopefully (but backup display)
            } else {
              console.log("Tried to remap object, but failed: " + objId)
            }
          }
          console.log("No object found with id " + objId)
          $state.go('app.map')
        })
        .catch(console.log)
      }
    }
  })
})
