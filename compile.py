import json
import os
import sys

import requests
import yaml

data = yaml.load(open('otaniemi.yml'))
#print(data)
newdata = [ ]

use_cache = True

# Getting ways by ID:
# wget -o /dev/null -O- 'http://overpass-api.de/api/interpreter?data=[out:json];(way(91227662);way(555));out;'


# Data which needs downloading
osm_ways = []
for building in data.get('buildings', []):
    if 'osm' in building:
        osm_ways.append(building['osm'])

if use_cache and os.path.exists('osm_raw_data.json'):
    r = json.loads(open('osm_raw_data.json').read())
else:
    r = requests.get('http://overpass-api.de/api/interpreter',
                params=dict(data="[out:json];(%s);out;"%";".join('way(%d);>'%x for x in osm_ways)))
    open('osm_raw_data.json', 'w').write(r.text)
    try:
        r = r.json()
    except:
        print(r.text)
osm_data = { }
for elem in r['elements']:
    if elem['type'] == 'node':
        osm_data[elem['id']] = elem #(elem['lat'], elem['lon'])
    else:
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
    if 'name' not in building: building['name'] = 'id'

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




for building in data.get('buildings', []):

    children = building.pop('children', [])
    building = process_building(building)
    building['type'] = 'building'
    newdata.append(building)

    # If this building has children, add them
    if children:
        for child in children:
            child['parent'] = building['id']
            newdata.append(child)


if len(sys.argv) > 1:
    open(sys.argv[1], 'w').write(json.dumps(newdata, indent=4))
else:
    print(json.dumps(newdata, indent=4))
