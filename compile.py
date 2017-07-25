import json
import os
import sys

import requests
import yaml

data = yaml.load(open('otaniemi.yml'))

use_cache = True

# Getting ways by ID:
# wget -o /dev/null -O- 'http://overpass-api.de/api/interpreter?data=[out:json];(way(91227662);way(555));out;'

class Location():
    """This class will handle most logic of locations"""
    def __init__(self, yamldata, parent=None):
        self.data = yamldata.copy()
        self.data.setdefault('type', 'building')
        if parent: self.data['parent'] = parent
    @property
    def id(self):
        if 'id'   in self.data: return self.data['id']
        if 'name' in self.data: return self.data['name']
        return str(id(self))
    def json(self):
        data= dict(
            id=self.id,
            type=self.data['type'],
            )
        if 'osm' in self.data:
            data['latlon'] = self.latlon
            data['outline'] = self.outline
        data.update(self.names)
        return data

    # Getter methods
    def osm_elements(self):
        """Used when downloading OSM data"""
        if 'osm' in self.data:
            return ('way', self.data['osm'])
    @property
    def osm_data_location(self):
        """OSM element that has the location data (path, latlon)"""
        if 'osm' not in self.data: return None
        return osm_data[self.data['osm']]
    @property
    def osm_metadata(self):
        """OSM element that has the metadata (names, address, etc)"""
        if 'osm' not in self.data: return None
        return osm_data[self.data['osm']]
    @property
    def latlon(self):
        if 'osm' not in self.data: return None
        latlon_path = self.outline
        return ( sum(x[0] for x in latlon_path)/len(latlon_path),
                 sum(x[1] for x in latlon_path)/len(latlon_path))
    @property
    def outline(self):
        if 'osm' not in self.data: return None
        return [ (osm_data[n]['lat'], osm_data[n]['lon'])
                 for n in self.osm_data_location['nodes'] ]
    @property
    def names(self):
        osm = self.osm_metadata
        names = { }
        if osm and 'tags' in osm:
            if 'name' in osm['tags']:     names['name']    = osm['tags']['name']
            if 'int_name' in osm['tags']: names['name_en'] = osm['tags']['int_name']
            if 'name:en' in osm['tags']:  names['name_en'] = osm['tags']['name:en']
            if 'name:sv' in osm['tags']:  names['name_sv'] = osm['tags']['name:sv']
            if 'addr:street' in osm['tags']:
                names['address'] = " ".join((osm['tags']['addr:street'], osm['tags']['addr:housenumber']))
        if 'name' not in names: names['name'] = building['id']
        return names


# assemble locations
locations = [ ]
for building in data.get('buildings', []):
    L = Location(building)
    locations.append(L)
    for child in L.data.get('children', []):
        locations.append(Location(child, parent=L.id))

# Find the OSM data that needs downloading
osm_ways = []
for L in locations:
    osm_data = L.osm_elements()
    if osm_data is not None:
        osm_ways.append(osm_data)
# Download and cache it
if use_cache and os.path.exists('osm_raw_data.json'):
    r = json.loads(open('osm_raw_data.json').read())
else:
    rcommand = "[out:json];(%s);out;"%";".join('%s(%d);>'%x for x in osm_ways)
    r = requests.get('http://overpass-api.de/api/interpreter',
                params=dict(data=rcommand))
    print(r.status)
    open('osm_raw_data.json', 'w').write(r.text)
    try:
        r = r.json()
    except:
        print(r.text)
# Assemble actual data
osm_data = { }
for elem in r['elements']:
    osm_data[elem['id']] = elem


def process_building(building):
    # Find initial data based on OSM
    building.setdefault('type', 'building')
    print('%s id=%s'%(building['type'], building['id']))

    from_osm = {'tags': { } }
    if 'osm' in building and building['osm'] in osm_data:
        building_osm = osm_data[building['osm']]
        print('  osm id=%s'%building['osm'])
        #print(building_osm)
        # find OSM outline
        # TODO: assumes it's a way
        latlon_path = [ (osm_data[n]['lat'], osm_data[n]['lon']) for n in building_osm['nodes'] ]
        building['outline'] = latlon_path
        # Find average location (TODO: make correct)
        building['latlon'] = (sum(x[0] for x in latlon_path)/len(latlon_path),
                              sum(x[1] for x in latlon_path)/len(latlon_path))

        # Other metadata
        if 'tags' in building_osm:
            if 'name' in building_osm['tags']:     from_osm['name']    = building_osm['tags']['name']
            if 'int_name' in building_osm['tags']: from_osm['name_en'] = building_osm['tags']['int_name']
            if 'name:en' in building_osm['tags']:  from_osm['name_en'] = building_osm['tags']['name:en']
            if 'name:sv' in building_osm['tags']:  from_osm['name_sv'] = building_osm['tags']['name:sv']
            if 'addr:street' in building_osm['tags']:
                from_osm['tags']['address'] = " ".join((building_osm['tags']['addr:street'], building_osm['tags']['addr:housenumber']))


    # Now update based on yaml data
    if 'name' not in building: building['name'] = building['id']

    # Create final object.  We want to return yaml data, if it exists,
    # and otherwise update from OSM data.  Eventually convert this to
    # a proper dict-merge algorithm.
    new_tags = { }
    new_building = { }
    new_building.update(from_osm)
    new_building.update(building)
    new_tags.update(from_osm.get('tags', {}))
    new_tags.update(building.get('tags', {}))
    new_building['tags'] = new_tags
    return new_building



# Create the JSON data
newdata = [ ]
for L in locations:
    print(L.id)
    newdata.append(L.json())

newdata = dict(
    locations=newdata,
    search=[],
    )

if len(sys.argv) > 1:
    open(sys.argv[1], 'w').write(json.dumps(newdata))
else:
    print(json.dumps(newdata, indent=4))
