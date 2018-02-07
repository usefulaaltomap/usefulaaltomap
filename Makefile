PYTHON='python3'
RAW=raw/osm_raw_data.json
WEBFILES=index.html data.json data.json-readable otaniemi.yml main sidenav *.js



default: data.json

# Downloads from OSM, generates data.json (identical rules)
raw/osm_raw_data.json: otaniemi.yml
	mkdir -p raw
	$(PYTHON) compile.py data.json
data.json: otaniemi.yml compile.py raw/osm_raw_data.json
	$(PYTHON) compile.py data.json

# Re-download the OSM data (making a backup)
refresh:
	mkdir -p raw
	test -f $(RAW)-`date +%Y-%m-%d` || mv $(RAW) $(RAW)-`date +%Y-%m-%d` || true
	rm $(RAW) || true
	$(PYTHON) compile.py data.json

deploy: data.json
	@test ! -z "$(HOST)" || ( echo "ERROR: specify host:   make ... HOST=hostname" ; false )
	rsync -aivP $(WEBFILES) $(HOST):/srv/usefulaaltomap/www/
