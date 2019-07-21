PYTHON='python3'
RAW=raw/osm_raw_data.json
WEBFILES=index.html data.json data.json-readable otaniemi.yml main sidenav *.js
SITE_DIR=www/


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

deploy-prepare:
	mkdir -p $(SITE_DIR)/
	rsync -a $(WEBFILES) $(SITE_DIR)/
	touch $(SITE_DIR)/.nojekyll
deploy: deploy-prepare data.json
	@test ! -z "$(HOST)" || ( echo "ERROR: specify host:   make ... HOST=hostname" ; false )
	rsync -aivP $(SITE_DIR) $(HOST):/srv/usefulaaltomap/www/ --exclude=.git

deploy-github:
	cd $(SITE_DIR) && git add .
	cd $(SITE_DIR) && git commit -a -m "deployment"
	cd $(SITE_DIR) && git push origin master

github: deploy-prepare deploy-github
