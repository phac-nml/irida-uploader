SHELL=/bin/bash
IRIDA_VERSION?=master

all: clean requirements

clean:
	rm -rf .cache
	rm -rf .virtualenv
	rm -rf build
	find -name "*pyc" -delete
	rm -rf tests_integration/repos/
	rm -rf tests_integration/tmp

requirements:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip install --upgrade pip wheel
	pip install -r requirements.txt

windows: clean requirements
	source .virtualenv/bin/activate
	python -m nsist windows-installer.cfg

unittests: clean requirements
	source .virtualenv/bin/activate
	python3 -m unittest discover -s tests -t .

integrationtests: clean requirements
	rm -rf tests_integration/repos/
	mkdir tests_integration/tmp
	mkdir tests_integration/tmp/output-files
	mkdir tests_integration/tmp/reference-files
	mkdir tests_integration/tmp/sequence-files
	source .virtualenv/bin/activate
	xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests.py

integrationtestsdev: clean requirements
	rm -rf tests_integration/repos/
	mkdir tests_integration/tmp
	mkdir tests_integration/tmp/output-files
	mkdir tests_integration/tmp/reference-files
	mkdir tests_integration/tmp/sequence-files
	source .virtualenv/bin/activate
	xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests_dev.py

docs: requirements
	source .virtualenv/bin/activate
	mkdocs build

.ONESHELL:
