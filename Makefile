.PHONY: run install url

run:
	source .venv/Scripts/activate || source .venv/bin/activate; \
	python ./src/test.py

install:
	rm -rf .venv; \
	python -m venv .venv; \
	[ -d ".venv/bin/activate" ] source ".venv/bin/activate" || source .venv/Scripts/activate; \
	pip install -r requirements.txt;

url:
	python src/index_v2.py
