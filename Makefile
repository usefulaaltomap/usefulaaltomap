RAW=osm_raw_data.json
WEBFILES=index.html data.json main sidenav/ *.js



default: data.json

# Downloads from OSM, generates data.json
data.json: otaniemi.yml compile.py
	python3 compile.py data.json

# Re-download the OSM data (making a backup)
refresh:
	mv $(RAW) $(RAW)-`date +%Y-%m-%d_%H:%M`
	python3 compile.py data.json

deploy: data.json
	test ! -z "$(HOST)" && echo "specify host:   make ... HOST=hostname"
	rsync -aivP $(WEBFILES) $(HOST):/srv/usefulaaltomap/www/
