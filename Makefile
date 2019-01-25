SHELL=/bin/bash
IRIDA_VERSION?=master

all: clean requirements

clean:
	rm -rf .cache
	rm -rf .virtualenv
	rm -rf build
	find -name "*pyc" -delete
	rm -rf Tests/integrationTests/repos/

requirements:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip install --upgrade pip wheel
	pip install -r requirements.txt
	deactivate

windows: clean requirements
	source .virtualenv/bin/activate
	python -m nsist windows-installer.cfg
	deactivate

test: clean requirements 
	source .virtualenv/bin/activate
	xvfb-run --auto-servernum --server-num=1 py.test --integration --irida-version=$(IRIDA_VERSION)

docs: requirements
	source .virtualenv/bin/activate
	mkdocs build
	deactivate

.ONESHELL:
