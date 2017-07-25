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
        if 'aliases' in self.data:
            aliases = self.data['aliases']
            if not isinstance(aliases, (list, tuple)):
                aliases = [aliases]
            data['aliases'] = aliases
        data.update(self.names)
        return data

    # Getter methods
    def osm_elements(self):
        """Used when downloading OSM data"""
        if 'osm' not in self.data: return None
        if not isinstance(self.data['osm'], dict):
            return [('way', self.data['osm'])]
        data = [ ]
        data.append(('way', self.data['osm']['outline']))
        data.append((self.data['osm']['metadata'].split('=')))
        return data
    @property
    def osm_data_location(self):
        """OSM element that has the location data (path, latlon)"""
        if 'osm' not in self.data: return None
        if isinstance(self.data['osm'], dict):
            if isinstance(self.data['osm']['outline'], str):
                return osm_data[int(self.data['osm']['outline'].split('=')[1])]
            return osm_data[self.data['osm']['outline']]
        return osm_data[self.data['osm']]
    @property
    def osm_metadata(self):
        """OSM element that has the metadata (names, address, etc)"""
        if 'osm' not in self.data: return None
        if isinstance(self.data['osm'], dict):
            if isinstance(self.data['osm']['metadata'], str):
                return osm_data[int(self.data['osm']['metadata'].split('=')[1])]
            return osm_data[self.data['osm']['metadata']]
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
        return [ (round(osm_data[n]['lat'], 5), round(osm_data[n]['lon'], 5))
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
        if self.data.get('name')   : names['name'] = self.data['name']
        if self.data.get('name_fi'): names['name_fi'] = self.data['name_fi']
        if self.data.get('name_en'): names['name_en'] = self.data['name_en']
        if self.data.get('name_sv'): names['name_sv'] = self.data['name_sv']
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
        osm_ways.extend(osm_data)
# Download and cache it
if use_cache and os.path.exists('osm_raw_data.json'):
    r = json.loads(open('osm_raw_data.json').read())
else:
    rcommand = "[out:json];(%s);out;"%";".join('%s(%s);>'%tuple(x) for x in osm_ways)
    r = requests.get('http://overpass-api.de/api/interpreter',
                params=dict(data=rcommand))
    if r.status_code != 200:
        raise RuntimeError("HTTP failure: %s %s"%(r.status_code, r.reason))
    open('osm_raw_data.json', 'w').write(r.text)
    try:
        r = r.json()
    except:
        print(r.text)
        exit(1)
# Assemble actual data
osm_data = { }
for elem in r['elements']:
    osm_data[elem['id']] = elem





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
    open(sys.argv[1], 'w').write(json.dumps(newdata, separators=(',', ':')))
else:
    print(json.dumps(newdata, indent=4))
