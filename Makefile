SHELL=/bin/bash
IRIDA_VERSION?=master

all: clean requirements
gui: clean requirementsgui

clean:
	rm -rf iridauploader/.cache
	rm -rf .virtualenv
	rm -rf build
	rm -rf dist
	rm -rf iridauploader.egg-info/
	find -name "*pyc" -delete
	rm -rf iridauploader/tests_integration/repos/
	rm -rf iridauploader/tests_integration/tmp

requirements:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip3 install --upgrade wheel
	pip3 install -e .

requirementsgui:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip3 install --upgrade wheel
	pip3 install -e .[GUI]

windows: clean requirements
	source .virtualenv/bin/activate
	python -m nsist windows-installer.cfg

wheel: clean
	python3 setup.py sdist bdist_wheel

unittests: clean requirements
	source .virtualenv/bin/activate
	export IRIDA_UPLOADER_TEST='True'
	python3 -m unittest discover -s tests -t iridauploader

preintegration:
	mkdir iridauploader/tests_integration/tmp
	mkdir iridauploader/tests_integration/tmp/output-files
	mkdir iridauploader/tests_integration/tmp/reference-files
	mkdir iridauploader/tests_integration/tmp/sequence-files

integrationtests: clean requirements preintegration
	source .virtualenv/bin/activate
	export IRIDA_UPLOADER_TEST='True'
	xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests.py master

integrationtestsdev: clean requirements preintegration
	source .virtualenv/bin/activate
	export IRIDA_UPLOADER_TEST='True'
	xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests.py development

pep8: clean requirements
	source .virtualenv/bin/activate
	pycodestyle --show-source --exclude=".git","bin",".idea","docs",".github","site",".virtualenv","iridauploader/build" --ignore="E501" .

docs: requirements
	source .virtualenv/bin/activate
	mkdocs build

.ONESHELL:
