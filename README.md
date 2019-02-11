IRIDA Uploader
==============

[![Build Status](https://travis-ci.org/phac-nml/irida-uploader.svg?branch=development)](https://travis-ci.org/phac-nml/irida-uploader)

[![Documentation Status](https://readthedocs.org/projects/irida-uploader/badge/?version=latest)](https://irida-uploader.readthedocs.io/en/latest/?badge=latest)

Download / Installation
--------------------

Installation instructions can be found in our documentation.

[ReadTheDocs](https://irida-uploader.readthedocs.io/en/latest/)

Creating the Windows installer from source code
------------------------------

A new windows installer can be built on linux, so first see the installation instructions for installing on linux in our documentation.

You will also need `nsis` installed to create the windows installer.

    $ sudo apt install nsis

Then run the command:

    $ make windows
    
This will create a new installer in the folder `build/nsis/` with a name similar to `IRIDA_Uploader_1.0.exe`

Running Tests
-------------

#### Unit tests

Running the unittests can be done with the command:

    $ make unittest

#### IRIDA Integration

To run integration tests your will need some additional software.

    $ sudo apt install xvfb

You will also need to download and install chromedriver http://chromedriver.chromium.org/downloads

You will need to allow the IRIDA instance to the mysql database needed for the tests

    $ mysql -e "CREATE USER 'test'@'localhost' IDENTIFIED BY 'test'; GRANT ALL ON irida_uploader_test.* to 'test'@'localhost';"

Running the IRIDA integration tests can be done with the command:

    $ make integrationtests

Tests will be logged to `~/.cache/irida_uploader_test/log/irida-uploader.log`

You can verify PEP8 conformity by running:

    $ ./scripts/verifyPEP8.sh

Note: No output is produced (other than `pip`-related output) if the PEP8 verification succeeds.

Documentation
------------------------------
You can [ReadTheDocs](https://irida-uploader.readthedocs.io/en/latest/) here.

Alternatively, documentation is built locally using `mkdocs`. 

It can be built with the command:

    $ make docs

Or you can install mkdocs to your system:

    $ sudo apt install mkdocs
    $ mkdocs build

HTML docs will be generated to `site/` for local browsing
