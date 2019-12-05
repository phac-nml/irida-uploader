Changes
=======

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

