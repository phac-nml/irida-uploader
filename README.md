IRIDA Uploader
==============


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
