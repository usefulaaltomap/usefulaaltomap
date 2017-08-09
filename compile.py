import fnmatch
import json
import os
import re
import sys

import requests
import yaml

data = yaml.load(open('otaniemi.yml'))
use_cache = True
re_nametoid = re.compile('[^a-zA-Z0-9_]+')

# Getting ways by ID:
# wget -o /dev/null -O- 'http://overpass-api.de/api/interpreter?data=[out:json];(way(91227662);way(555));out;'

# utility
def update_maybe(dct, key, new_dct, new_key=None):
    if new_key is None: new_key = key
    if key in dct:
        new_dct[new_key] = dct[key]
def update_matching(dct, key_pattern, new_dct):
    for key in dct:
        if fnmatch.fnmatchcase(key, key_pattern):
            new_dct[key] = dct[key]

# Main class

class Location():
    """This class will handle most logic of locations"""
    def __init__(self, yamldata, type=None, parent=None):
        self.data = yamldata.copy()
        if type: self.data['type'] = type
        if parent: self.data['parents'] = [parent]
        self.data['children'] = [ ]
        # self-tests
        assert 'type' in self.data, 'Missing type: %s'%self.id
    def __repr__(self):
        return '%s(id=%s)'%(self.__class__.__name__, self.id)
    @property
    def id(self):
        if 'id'   in self.data: return self.data['id']
        if 'name' in self.data: return re_nametoid.sub('', self.data['name'].lower())
        return str(id(self))
    def json(self):
        data= dict(
            id=self.id,
            type=self.data.get('type'),
            )
        if self.latlon: data['latlon']   = self.latlon
        if self.outline: data['outline'] = self.outline
        # aliases: loc_name from OSM and then Aalto-specific
        data['aliases'] = [ ]
        if self.osm_metadata and 'loc_name' in self.osm_metadata['tags']:
            data['aliases'].append(self.osm_metadata['tags']['loc_name'])
        if self.osm_metadata and 'opening_hours' in self.osm_metadata['tags']:
            data['opening_hours'] = self.osm_metadata['tags']['opening_hours']
        if 'aliases' in self.data:
            aliases = self.data['aliases']
            if not isinstance(aliases, (list, tuple)):
                aliases = [aliases]
            data['aliases'].extend(aliases)
        data.update(self.names)
        update_maybe(self.data, 'parents', data)
        update_maybe(self.data, 'children', data)
        update_maybe(self.data, 'lore', data)
        update_maybe(self.data, 'note', data)
        update_maybe(self.data, 'opening_hours', data)
        data['osm_id'] = [ ]
        if 'osm' in self.data:  data['osm_id'].append(self.data['osm'])
        if 'osm_meta' in self.data:  data['osm_id'].append(self.data['osm_meta'])
        if self.osm_elements():
            data['osm_elements'] = [(t.replace('rel', 'relation'), v)
                                    for t,v in self.osm_elements()]
        if self.entrances(): data['entrances'] = self.entrances()
        data.update(self.labels)
        return data
    @property
    def children(self):
        if self.data['children']:
            return self.data['children']

    # Getter methods
    def osm_elements(self):
        """Used when downloading OSM data"""
        osm_elements = [ ]
        if 'osm' in self.data:
            if isinstance(self.data['osm'], str) and '=' in self.data['osm']:
                osm_elements.append(self.data['osm'].split('='))
            else:
                osm_elements.append(('way', self.data['osm']))
        if 'osm_meta' in self.data:
            if isinstance(self.data['osm_meta'], str) and '=' in self.data['osm_meta']:
                osm_elements.append(self.data['osm_meta'].split('='))
            else:
                osm_elements.append(('way', self.data['osm_meta']))
        if osm_elements:
            return osm_elements
        return None
        #if 'osm' not in self.data: return None
        #if isinstance(self.data['osm'], dict):
        #    data = [ ]
        #    data.append(('way', self.data['osm']['outline']))
        #    data.append((self.data['osm']['metadata'].split('=')))
        #    return data
        #if isinstance(self.data['osm'], str) and '=' in self.data['osm']:
        #    return [self.data['osm'].split('=')]
        #return [('way', self.data['osm'])]
    @property
    def osm_data_location(self):
        """OSM element that has the location data (path or latlon)"""
        if 'osm' not in self.data or not self.data['osm']: return None
        if isinstance(self.data['osm'], str) and '=' in self.data['osm']:
            return osm_data[int(self.data['osm'].split('=')[1])]
        #if isinstance(self.data['osm'], dict):
        #    if isinstance(self.data['osm']['outline'], str):
        #        return osm_data[int(self.data['osm']['outline'].split('=')[1])]
        #    return osm_data[self.data['osm']['outline']]
        return osm_data[self.data['osm']]
    @property
    def osm_metadata(self):
        """OSM element that has the metadata (names, address, etc)"""
        if 'osm_meta' in self.data:
            if isinstance(self.data['osm_meta'], str) and '=' in self.data['osm_meta']:
                return osm_data[int(self.data['osm_meta'].split('=')[1])]
            return osm_data[self.data['osm_meta']]
        if 'osm' in self.data:
            if isinstance(self.data['osm'], str) and '=' in self.data['osm']:
                return osm_data[int(self.data['osm'].split('=')[1])]
            return osm_data[self.data['osm']]
        return None
        #if isinstance(self.data['osm'], str) and '=' in self.data['osm']:
        #    return self.data['osm'].split('=')[1]
        #if isinstance(self.data['osm'], dict):
        #    if isinstance(self.data['osm']['metadata'], str):
        #        return osm_data[int(self.data['osm']['metadata'].split('=')[1])]
        #    return osm_data[self.data['osm']['metadata']]
        #return osm_data[self.data['osm']]
    @property
    def latlon(self):
        if 'latlon' in self.data: return self.data['latlon']
        if 'osm' not in self.data: return None
        if isinstance(self.data['osm'], str) and self.data['osm'].startswith('node'):
            n = int(self.data['osm'].split('=')[1])
            return (round(osm_data[n]['lat'], 5), round(osm_data[n]['lon'], 5))
        latlon_path = self.outline
        if not latlon_path: return none
        return ( round(sum(x[0] for x in latlon_path)/len(latlon_path), 5),
                 round(sum(x[1] for x in latlon_path)/len(latlon_path), 5))
    @property
    def outline(self):
        if 'outline' in self.data: return self.data['outline']
        if 'osm' not in self.data: return None
        locdat = self.osm_data_location
        if locdat['type'] != 'way':
            return None
        if 'nodes' in locdat:
            nodes = [ (round(osm_data[n]['lat'], 5), round(osm_data[n]['lon'], 5))
                     for n in locdat['nodes'] ]
            return nodes
            # Convex halls reduce data size a bit (currently to 70% but looks much worse)
            #print(len(nodes))
            #from scipy.spatial import ConvexHull
            #cv = ConvexHull(nodes)
            #print(len(cv.vertices))
            #return [nodes[i] for i in cv.vertices ]
    @property
    def names(self):
        osm = self.osm_metadata
        names = { }
        if osm and 'tags' in osm:
            if 'name' in osm['tags']:     names['name']    = osm['tags']['name'].replace('Aalto ', '')
            if 'int_name' in osm['tags']: names['name_en'] = osm['tags']['int_name'].replace('Aalto ', '')
            if 'name:en' in osm['tags']:  names['name_en'] = osm['tags']['name:en'].replace('Aalto ', '')
            if 'name:sv' in osm['tags']:  names['name_sv'] = osm['tags']['name:sv'].replace('Aalto ', '')
            if 'addr:street' in osm['tags']:
                names['address'] = " ".join((osm['tags']['addr:street'], osm['tags']['addr:housenumber']))
        update_matching(self.data, 'name*', names)
        update_matching(self.data, 'address*', names)
        return names
    def entrances(self):
        """Make list of entrances of this building.

        Returns: [ {'lat'=XX, 'lon'=XX, 'name'=XX, 'main'=True}, ... ]
                 'name' and 'main' are both optional.
        """
        way = self.osm_data_location
        if not way: return
        if way['type'] != 'way': return
        entrances = [ ]
        for n in way['nodes']:
            if 'tags' not in osm_data[n]:
                continue
            if osm_data[n]['tags'].get('entrance', None) not in {'yes', 'main', 'staircase'}:
                continue
            is_main = osm_data[n]['tags']['entrance'] == 'main'
            is_wheelchair = osm_data[n]['tags'].get('wheelchair') == 'yes'
            if osm_data[n]['tags'].get('access', 'yes') not in {'yes', 'permissive'}:
                continue
            name = osm_data[n]['tags'].get('name', osm_data[n]['tags'].get('ref'))
            if name and len(name) > 3: name = None
            lat, lon = round(osm_data[n]['lat'], 5), round(osm_data[n]['lon'], 5)
            # Create data
            e = dict(lat=lat, lon=lon)
            if name: e['name'] = name
            if is_main: e['main'] = is_main
            entrances.append(e)
            #print(n, e, osm_data[n])
        return entrances
    @property
    def labels(self):
        if self.data['type'] != 'building':
            return { }
        labels_dict = { }
        # find buliding number
        re_rnumber = re.compile(r'R(\d{2,3})', re.I)
        Rnumber = None
        if 'aliases' in self.data:
            Rnumber = next(map(re_rnumber.search, self.data['aliases']), None)
            if Rnumber:
                Rnumber = str(int(Rnumber.group(1)))
        update_matching(self.data, 'label*', labels_dict)
        # If we have R-number, update labels to include it
        if Rnumber:
            for key in labels_dict:
                labels_dict[key] = labels_dict[key] + '\n' + Rnumber
            if 'label' not in labels_dict:
                labels_dict['label'] = str(Rnumber)
        return labels_dict
    @property
    def priority(self):
        """Priority for sorting.  higher=sooner"""
        if self.data['type'] == 'building':    return 400
        if self.data['type'] == 'department':  return 300
        if self.data['type'] == 'unit':        return 200
        if self.data['type'] == 'service':     return 100
        return 0


# assemble locations
locations = [ ]
for building in data.get('buildings', []):
    L = Location(building, type='building')
    print(L.id, L.data)
    locations.append(L)
    for child in building.get('children', []):
        locations.append(Location(child, parent=L.id))
        print(locations[-1].id, locations[-1].data)
for building in data.get('other', []):
    L = Location(building)
    print(L.id, L.data)
    locations.append(L)
    for child in building.get('children', []):
        locations.append(Location(child, parent=L.id))
        print(locations[-1].id, locations[-1].data)
locations.sort(key=lambda x: x.priority, reverse=True)
# Crosslink children
locations_lookup = { }
for L in locations:
    locations_lookup[L.id] = L
for L in locations:
    for L_parent_id in L.data.get('parents', []):
        locations_lookup[L_parent_id].data['children'].append(L.id)
for L in locations:
    L.data.get('children', []).sort(key=lambda x: locations_lookup[x].priority, reverse=True)
    L.data.get('parents', []).sort(key=lambda x: locations_lookup[x].priority, reverse=True)


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
    rcommand = "[out:json];(%s);out;"%(
                 ";".join('%s(%s)%s'%(t,osmid, ';>' if t=='way' else '') for t, osmid in osm_ways))
    r = requests.get('http://overpass-api.de/api/interpreter',
                params=dict(data=rcommand))
    if r.status_code != 200:
        print(rcommand)
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
    open(sys.argv[1]+'-readable', 'w').write(json.dumps(newdata, indent=2))
else:
    print(json.dumps(newdata, indent=4))
