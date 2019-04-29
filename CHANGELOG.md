Changes
=======

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

Beta 0.1
---------
* The start of time

