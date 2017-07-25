default: data.json

data.json: otaniemi.yml compile.py
	python3 compile.py data.json
