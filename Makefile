SRC_YAML=otaniemi.yml
PYTHON='python3'
RAW=raw/osm_raw_data.json
WEBFILES=index.html data.json data.json-readable $(SRC_YAML) main sidenav *.js
SITE_DIR=www/


# data.json is the processed data for the web site, so just make that
# by default.
default: data.json

# raw/osm_raw_data.json is a raw file downloaded from an OSM API, but
# is only downloaded if it is not there already.  Thus, it downloads
# the first time, but after that have to run "make refresh" to get
# newer data.  Don't forget to do this or you end up
# confused!
raw/osm_raw_data.json: $(SRC_YAML)
	mkdir -p raw
	$(PYTHON) compile.py data.json
# Generate the data.json file.  Note that the actual command is the
# same as the above, there's really no reason to have two separate
# rules here... other than making dependencies explicit.
data.json: $(SRC_YAML) compile.py raw/osm_raw_data.json
	$(PYTHON) compile.py data.json

# The downloaded data cached saved in raw/osm_raw_data.json.  This rule moves hte
refresh:
	mkdir -p raw
	test -f $(RAW)-`date +%Y-%m-%d` || mv $(RAW) $(RAW)-`date +%Y-%m-%d` || true
	rm $(RAW) || true
	$(PYTHON) compile.py data.json

# Make a file $(SITE_DIR) and copy al the static files that we need
# into there.  This sets it up for Github Pages, but can be used on
# any static server.
deploy-prepare:
	mkdir -p $(SITE_DIR)/
	rsync -a $(WEBFILES) $(SITE_DIR)/
	touch $(SITE_DIR)/.nojekyll
	echo usefulaaltomap.fi >> $(SITE_DIR)/CNAME
# Deploy using rsync and the HOST variable.
deploy-rsync: deploy-prepare data.json
	@test ! -z "$(HOST)" || ( echo "ERROR: specify host:   make ... HOST=hostname" ; false )
	rsync -aivP $(SITE_DIR) $(HOST):/srv/usefulaaltomap/www/ --exclude=.git
# Deploy to github-pages.  This is just for local use, not on
# travis-ci (there's another module for that), but this clones the
# existing gh-pages repo, does some file movement to put it in the
# $(SITE_DIR), commit, and push.
deploy-github: deploy-prepare data.json
	{ cd $(SITE_DIR) && test ! -d .git && git clone git@github.com:usefulaaltomap/usefulaaltomap.fi tmp-git && mv tmp-git/.git . && rm -rf tmp-git ; } || true
	cd $(SITE_DIR) && git add .
	cd $(SITE_DIR) && git commit -a -m "deployment"
	cd $(SITE_DIR) && git push origin master

deploy: deploy-github
