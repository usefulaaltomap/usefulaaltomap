PYTHON='python3'
RAW=osm_raw_data.json
WEBFILES=index.html data.json data.json-readable otaniemi.yml main sidenav *.js



default: data.json

# Downloads from OSM, generates data.json (identical rules)
osm_raw_data.json: otaniemi.yml
	$(PYTHON) compile.py data.json
data.json: otaniemi.yml compile.py osm_raw_data.json
	$(PYTHON) compile.py data.json

# Re-download the OSM data (making a backup)
refresh:
	test -f $(RAW)-`date +%Y-%m-%d_%H:%M` || mv $(RAW) $(RAW)-`date +%Y-%m-%d_%H:%M` || true
	rm $(RAW) || true
	$(PYTHON) compile.py data.json

deploy: data.json
	@test ! -z "$(HOST)" || ( echo "ERROR: specify host:   make ... HOST=hostname" ; false )
	rsync -aivP $(WEBFILES) $(HOST):/srv/usefulaaltomap/www/
