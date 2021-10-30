.PHONY: source run install

run:
	python ./src/test.py

install:
	pip install -r requirements.txt

source:
	source env/vc/bin/activate

url:
	python src/index_v2.py
