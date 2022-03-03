IRIDA Uploader
==============

[![Integration Tests](https://github.com/phac-nml/irida-uploader/workflows/Integration%20Tests/badge.svg?branch=development&event=schedule)](https://github.com/phac-nml/irida-uploader/actions?query=branch%3Adevelopment)
[![Documentation Status](https://readthedocs.org/projects/irida-uploader/badge/?version=stable)](https://irida-uploader.readthedocs.io/en/stable/?badge=stable)
[![install with bioconda](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat)](http://bioconda.github.io/recipes/irida-uploader/README.html)

**Please Note: The latest version of the IRIDA Uploader requires IRIDA Version 20.05 or later.**

If you are using an older version of IRIDA, please update your IRIDA, or use Uploader Release Version 0.4.3

Download / Installation
--------------------

The IRIDA Uploader is available via `pip` and `bioconda`

Installation instructions can be found in our documentation.

[ReadTheDocs](https://irida-uploader.readthedocs.io/en/stable/)

Tutorial
--------

You can find a walkthrough and tutorial on the phac-nml github

https://github.com/phac-nml/irida-uploader-tutorial

Running the project from source code
--------------------------
You can build an environment and run the uploader from source code with the following commands:

    $ make
    $ source .virtualenv/bin/activate
    $ irida-uploader --help

You can also build and run the GUI with:

    $ make gui
    $ source .virtualenv/bin/activate
    $ irida-uploader-gui

Creating the Windows installer from source code
------------------------------

A new windows installer can be built on linux, so first see the installation instructions for installing on linux in our documentation.

You will also need `nsis` installed to create the windows installer.

    $ sudo apt install nsis

Then run the command:

    $ make windows
    
This will create a new installer in the folder `build/nsis/` with a name similar to `IRIDA_Uploader_GUI_0.X.X.exe`

Running Tests
-------------

#### Unit tests

Running the unittests can be done with the command:

    $ make unittests

#### Integration tests

To run integration tests You will need to download and install chromedriver http://chromedriver.chromium.org/downloads

You will need to grant the IRIDA instance access to the mysql database needed for the tests

    $ mysql -e "CREATE USER 'test'@'localhost' IDENTIFIED BY 'test'; GRANT ALL ON irida_uploader_test.* to 'test'@'localhost';"

Running the IRIDA integration tests can be done with the command:

    $ make integrationtests branch=<IRIDA github branch to test against>

Example:

    $ make integrationtests branch=development

Tests will be logged to `~/.cache/irida_uploader_test/log/irida-uploader.log`

#### PEP8 tests

You can run pep8 tests with:

    $ make pep8

Documentation
------------------------------
You can [ReadTheDocs](https://irida-uploader.readthedocs.io/en/stable/) here.

Alternatively, documentation is built locally using `mkdocs`. 

It can be built with the command:

    $ make docs

Or you can install mkdocs to your system:

    $ sudo apt install mkdocs
    $ mkdocs build

HTML docs will be generated to `site/` for local browsing
