Changes
=======

Beta 0.6.0
----------
Added functionality:
* Added `--delay=[Integer]` argument/config option to allow runs to be delayed when they are found.
  * When `delay` is set, a new run will be set to Delayed, and will only be available to upload once `delay` minutes have passed
    * Default is 0 minutes, s.t. no delay will occur unless the `delay` argument or config argument is > 0
  * This should be used when automating uploads from a network location where file transfer may be done over a period of time
    * Please see the MiSeq Analysis issue for more details on when to use this https://github.com/phac-nml/irida-uploader/issues/76
  * The delay can be bypassed with `--force`
* Improved the Directory Status file
  * Includes a list of all samples to be uploaded and progress for them.
    * If a run stops mid upload, you can now clearly see which files where uploaded from the directory status file.
  * Added an IRIDA Instance field to the directory status file so where the files have been sent is recorded.
* Added support for Python 3.8 and 3.9
* Added NextSeq2000 support with a new parser `nextseq2k_nml`
  * Because the NextSeq2000 software does not generate a sample sheet that includes a project column, it needs to be created manually.
  * Please see the documentation for the `nextseq2k_nml` for details
* Added a warning if the base_url does not end in /api/

Developer changes:
* Refactored `core/cli_entry.py`
  * Renamed file to `core/upload.py` as to better fit its functionality (also handles gui uploads)
  * Created helper function file `core/upload_helpers.py` to improve code flow
  * Code flow for all routines has been simplified and new unit tests and documentation has been added
* The `DirectoryStatus` and `upload_status.py` files have been overhauled to support the new delay/upload_status functionality
* GUI upload now always executes with force_upload=True to simplify internal logic
* Windows build will no longer include test files in executable (slightly reduced file size)
* Added documentation for how to draft a new release (for internal use)

Beta 0.5.1
----------
Changes
* Added notes about version compatibility to README
* Added more error logging to api_calls.py
* Fixed integration tests compatibility with IRIDA Version 20.05

Beta 0.5.0
----------
Added functionality:
* Added `nanopore_assemblies` as an alias for directory uploads
* Added support for uploading `fast5` files
* Added `--upload_mode=<mode>` as an argument, replacing the `--assemblies` argument
  * Supports the following upload modes, which each upload files to different IRIDA REST endpoints
    * `default`: Sends to `sequencingRuns`, this is the default behaviour
    * `assemblies`: Sends to `assemblies`, this replaces `--assemblies`
    * `fast5`: Sends to `fast5`, this is a new feature
  * GUI now has a dropdown box to select upload mode
* Added mode `readonly`, controlled with config option `readonly` and cli argument `--readonly` / `-r`
  * This mode uploads without writing status and log files to the sequencing run directory.
  * `readonly` checkbox has been added to the GUI config page.

Developer changes:
* Changed `api` to post to `<base_url>/sequencingrun/<sequencing_run_type>` instead of `<base_url>/sequencingrun/miseqrun`
  * Added `sequencing_run_type` to the `parser -> model -> api` chain
* Switched to new build sequence to be more pythonic
  * Restructured Makefile to use `pip -e` instead of manual installation with requirements files when installing from source
  * Consolidated `run_upload.py` and `upload_gui.py` into `core/cli.py` and `gui/gui.py` (new file, not old gui.py)
  * Moved `gui/gui.py` to `gui/main_dialog.py`
  * GUI code can now be installed from `setup.py`/`pip` by using the extra `[GUI]` when installing
  * Makefile now uses extra `[GUI]` when installing gui with command `make gui`
* Dropped support for command line only windows build
  * As before, command line can still be used with the windows gui build
* Moved all example files to a new folder `examples`
* Bash scripts for running uploader have been simplified, renamed, and moved
  * Bash scripts now use the `setup.py` defined entry points for parity with `pip`
  * `irida-uploader.sh` -> `scripts/upload.sh`
  * `gui-uploader.sh` -> `scripts/gui.sh`
* Changed integration tests build/startup to follow the `setup.py` flow
  * Moved `start_integration_tests.py` to `iridauploader/tests_integration`
  * added `[TEST]` as an `extra` to `setup.py` for build simplicity
  * added `integration-test` as an entry point when building with `[Test]`, which `Makefile` now uses
  * Makefile command for integration tests has changed from:
    * `make integrationtests` ----> `make integrationtests branch=master`
    * `make integrationtestsdev` -> `make integrationtests branch=development`
    * any IRIDA github branch can be specified with the `branch` argument
* Makefile has been simplified for easier readability

Beta 0.4.3
----------
Added functionality:
* `directory` parsers now support full file paths for upload.

Developer changes:
* Added method `get_metadata(self, sample_name, project_id)` to allow other metadata to be fetched from the `api` module
* Added method `send_metadata(self, metadata, project_id, sample_name)` to allow other metadata to be sent using the `api` module
* Added model `Metadata` to support `send_metadata` method

Beta 0.4.2
----------
Added functionality:
* Added support for uploading assemblies. Use `-a` / `--assemblies` or the checkbox on the GUI

Developer changes:
* Added support for cloud deployment by using the `iridauploader` available on `pip`
* Added version updater script to the `scripts` directory
* Added argument `assemblies=False` to `send_sequence_files(...)` to allow for assemblies upload from the `api` module
* Added method `get_assemblies_files(self, project_id, sample_name)` to allow for fetching assemblies from the `api` module

Beta 0.4.1
----------
Developer changes:
* Files structure changed
  * Moved all application code into a `iridauploader` directory.
  * Changed all import statements from using relative imports to use absolute imports with the root of `iridauploader`
* Added PyPi support via `setup.py`
  * the IRIDA Uploaders modules can now be imported via `pip`
* Swapped multipart file encoder to now use `requests-toolkit` to enable file streaming, leading to faster / more consitant uploads
* Changed byte send size of httplib to 1024\*1024, raising max upload speed from ~40Mbps to >200Mbps (upper bound not found yet)
* Gui file progress widget no longer knows about single vs paired end sequence files, only progress per sample

Bug Fixes:
* Gui progress widget no longer turns green(complete) at 50% upload with paired end reads in rare cases

Beta 0.3.3
----------
Added functionality:
* Added support for Miseq Control Software Version 3.1
  * Use parser `miseq_v31`, behaves the same as miniseq and iseq parser.
  * Also added `miseq_v26` to specify parsing for the older miseq control software.
  * The `miseq` parser still specifies the Miseq Control Software Version 2.6

Beta 0.3.2
----------
Added functionality:
* Default config file can now be overridden across a system by adding a config.conf file to the source directory. Specifying config file from command line trumps the override file.

Changes:
* Logging directory has been changed from `irida_uploader` to `irida-uploader` to match config directory naming.

Beta 0.3.1
----------
Added functionality:
* Added support for iSeq, use parser `iseq` to use.
* Added message box to confirm if user wants to exit gui while data is being uploaded.
* Added crash log file `crash.log` to the log directory in cases where an error causes an unrecoverable error 

Bug Fixes:
* Fixed python script not being called from `irida-uploader.sh` when called from outside of the install directory
* Integration Development tests now test java 11 instead of java 8
* Fixed bug that caused `miniseq` parser to fail when parsing `iseq` runs
* Fixed hard crash in some cases when IRIDA failed to respond to the HTTP request
* Uploader no longer exits after creating a new config file (fixes issue where GUI would exit without explanation)
* Fixed very rare hard crash in case where IRIDA stops replying mid url existence verification
* Fix issue were some parsing errors were not properly handled by GUI causing crashes

Beta 0.3
--------
Added functionality:
* Added config option overrides for the command line
    * Can define in command line `--option parameter` or without a parameter `--option` for a user prompt
    * Use the `--help` option for more details on these options
* The `directory` parser can now handle full (absolute) file paths in the sample list file

Bug Fixes:
* Fixed hard crash that sometimes occurred when valid url's were given as the base_url
* Fixed hard crash when running the miniseq parser on a miseq run directory

API Changes:
* Added 400, 401, 403, and 500 to http errors we explicitly have exceptions for. (Other errors still generate generic exceptions that are handled the same way.)

Developer changes:
* Added pep8 testing with `make pep8`

Beta 0.2.1
----------
Bug Fixes:
* Fixed bug where 2 description fields would be sent with some miniseq runs, causing upload to fail.

Beta 0.2
--------
Added functionality:
* When uploading, a `irida_uploader_status.info` status file will be created in the run directory
* If a status file exists, trying to upload will fail and give a message saying an upload has already been attempted
* using `--force` or `-f` when uploading bypasses this check
* Added support for python versions 3.5 to 3.7 (previously was locked to 3.6 only)
* Now uploader writes logs to run folder, for that specific upload
* When uploading, a progress percentage will be printed to the command line (Linux + Windows)
* Miseq uploader now requires `CompletedJobInfo.xml` file to upload
* Added support for MiniSeq, use parser `miniseq` to use.
* Added support for NextSeq, use parser `nextseq` to use.
* Added shebang to top of upload_run.py to support conda environments
* Added batch uploading, use `--batch` or `-b` with a directory containing multiple runs to upload.

Beta 0.1
---------
* The start of time

