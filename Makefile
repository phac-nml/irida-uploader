SHELL=/bin/bash
IRIDA_VERSION?=master

requirements: clean env
	source .virtualenv/bin/activate
	pip3 install -e .

clean:
	rm -rf iridauploader/.cache
	rm -rf .virtualenv
	rm -rf build
	rm -rf dist
	rm -rf iridauploader.egg-info/
	find -name "*pyc" -delete
	rm -rf iridauploader/tests_integration/repos/
	rm -rf iridauploader/tests_integration/tmp

env:
	python3 -m venv .virtualenv
	source .virtualenv/bin/activate
	pip3 install --upgrade wheel pip setuptools

gui: clean env
	source .virtualenv/bin/activate
	pip3 install -e .[GUI]

windows: clean env
	source .virtualenv/bin/activate
	pip3 install -e .[WINDOWS]
	python3 -m nsist windows-installer.cfg

wheel: clean
	python3 setup.py sdist bdist_wheel

unittests: clean env
	source .virtualenv/bin/activate
	pip3 install -e .[TEST]
	export IRIDA_UPLOADER_TEST='True'
	python3 -m unittest discover -s tests -t iridauploader

preintegration:
	mkdir iridauploader/tests_integration/tmp
	mkdir iridauploader/tests_integration/tmp/output-files
	mkdir iridauploader/tests_integration/tmp/reference-files
	mkdir iridauploader/tests_integration/tmp/sequence-files
	mkdir iridauploader/tests_integration/tmp/assembly-files
	chmod -R 555 iridauploader/tests_integration/fake_ngs_data_read_only

integrationtests: clean env preintegration
	source .virtualenv/bin/activate
	pip3 install -e .[TEST]
	export IRIDA_UPLOADER_TEST='True'
	xvfb-run --auto-servernum --server-num=1 integration-test $(branch) $(db_host) $(db_port)

pep8: clean env
	source .virtualenv/bin/activate
	pip3 install pycodestyle
	pycodestyle --show-source --exclude=".git","bin",".idea","docs",".github","site",".virtualenv","iridauploader/build" --ignore="E501,W503" .

docs: requirements
	source .virtualenv/bin/activate
	mkdocs build

.ONESHELL:
