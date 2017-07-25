default: data.json

data.json: otaniemi.yml compile.py osm_raw_data.json
	python3 compile.py data.json
