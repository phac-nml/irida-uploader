# IRIDA Uploader


##Features
* Command Line interface for Linux and Windows
* Single Directory Upload
* MiSeq/MiniSeq/NextSeq Sequencing Run Parser
* Directory Parsing
* Batch Uploads
* Assemblies Uploads
* Fast5 Uploads
* Can be used with cron/windows task scheduler for automated uploads
* GUI
* Resume Uploads

## Upcoming Features
* File upload checksum validation
* Post-processing tasks

## Version Compatibility

**IRIDA Uploader Version 0.5.0** and later require IRIDA to be at least **IRIDA Version 20.05**

If you are using an older version of IRIDA, you can use **IRIDA Uploader Version 0.4.3**, but we recommend that you speak with your IRIDA administrator to upgrade to the latest version.

# Getting Started

## GUI Tutorial

You can find a tutorial and walkthrough on the phac-nml github https://github.com/phac-nml/irida-uploader-tutorial

## Install / Setup

### Installation

#### Windows

You can download pre-built packages for Windows from our [GitHub releases page](https://github.com/phac-nml/irida-uploader/releases).

Run an installer (links above) and follow along with the install wizard.

You will need to configure your uploader before running. See [Configuration](configuration.md) for details

If you prefer to build a windows installer from source code, please see the README on [GitHub](https://github.com/phac-nml/irida-uploader)

#### Linux

If you prefer to build the uploader from source code, please see the README on [GitHub](https://github.com/phac-nml/irida-uploader)

##### Command Line

The IRIDA Uploader requires Python version 3.6 or newer

    $ python3 --version

Ensure that `pip`, and `setuptools` are up to date

    $ pip install pip -U
    $ pip install setuptools -U

Install the latest release with `pip`

    $ pip3 install iridauploader

Run the uploader

    $ irida-uploader

##### GUI

You can also install the GUI by specifying the `GUI` extra in your pip install command

    $ pip3 install 'iridauploader[GUI]'
    $ irida-uploader-gui

*Please Note: You will need to configure your uploader to connect to IRIDA before running. See Configuration section below.*

### Upload Modes

By default, the IRIDA Uploader will upload fastq sequence files, but it can also upload Assemblies (fasta), and Fast5 data

When uploading from the command line, use the `--upload_mode=<mode>`, with `assemblies` or `fast5` to upload those file types.

See the `--help` command for more details.

You can also select an upload mode when using the GUI via a drop down menu on the main screen.

### Configuration

You will need to configure IRIDA and the uploader to upload files.

[How to configure](configuration.md)

If you do not create a configuration file, IRIDA uploader will create one for you with default values the first time it try's to upload.

You will need to edit this file with your IRIDA credentials, and the parser that matches your data.

#### Choose a Parser

The config file has a `parser` field that you can use to parse different directory structures

We currently support the following:

`directory` : [Generic Directory](parsers/directory.md)

`miseq` / `miseq_v26` : [Miseq (Control Software Version 2.6)](parsers/miseq_v26.md)

`miseq_v31` : [Miseq (Control Software Version 3.1)](parsers/miseq_v31.md)

`miniseq` : [MiniSeq](parsers/miniseq.md)

`iseq` : [iSeq](parsers/miniseq.md)


`nextseq` : [NextSeq](parsers/nextseq.md)

## Starting an upload

You can upload with the following commands

### Windows:

Open a Command Prompt terminal and use the `iridauploader` command to upload

`C:\Users\username> iridauploader -d \path\to\my\samples\`

### Linux:

Use the `irida-uploader.sh` script included with the source code to upload.

`./irida-uploader.sh -d /path/to/the/sequencing/run/`


#### Note:
After uploading, an `irida_uploader_status.info` file will be created which indicates if a run is complete, or has failed

You can delete this file to make it ready for reupload, or use the `--force` option when running the uploader to ignore the status of a run directory.


## Batch Uploading

You can upload a directory containing run directories by using the `--batch` option when running the uploader.

Example batch upload directory:

`./irida-uploader.sh --batch /path/to/BatchDirectoryToUpload/`

```
.
└── BatchDirectoryToUpload
    ├── Run_1
    │   ├── SampleSheet.csv
    │   └── <other run files>
    ├── Run_2
    │   ├── SampleSheet.csv
    │   └── <other run files>
    └── Run_3
        ├── SampleSheet.csv
        └── <other run files>
```

The `--force` option can be used with the `--batch` option

##### WARNING! When uploading `nextseq` data and using `--batch` upload with an auto-upload script, incomplete fastq files could be uploaded if `bcl2fastq` has not finished when the upload begins.

## Logging

Logs about individual runs are written to the sequencing run directory that they are uploaded from.

Full debug logs are written to your system default logging directory

#### Linux

`/home/<user>/.cache/irida-uploader/log/`

#### Windows

`C:\Users\<username>\AppData\Local\irida-uploader\irida-uploader\Logs`

## Read Only Mode

You can upload in read-only mode with the config option, the `--readonly` / `-r` command line option, or the checkbox on the GUI.

In this mode, the status file and the logging file will not be created in the sequencing run directory during upload.

## Continue Partial/Failed Uploads

If an upload fails to complete upload for any reason, the upload can be continued from either the GUI (by selecting continue upload) or with the command line by using the `--confingue_partial` argument.

You can see details about which files have been uploaded by viewing the status file generated in your sequencing run directory.

**Note:** `--continue_partial` and `--force` are mutually exclusive, as `--force` indicates that a run should be restarted

# Problems?

### Problems uploading?
Check the [Errors Page](errors.md) for help with common errors.

### Found a bug or have an idea for a feature?
Create an issue on our [GitHub Issues Board](https://github.com/phac-nml/irida-uploader/issues)

# Developers

The modules of the IRIDA Uploader can be used through pip/pypi

`pip install iridauploader`

Example to get you started:

```python
import iridauploader.api as api
import iridauploader.parsers as parsers

api_instance = api.ApiCalls(client_id, client_secret, base_url, username, password, timeout_multiplier)
parser_instance = parsers.parser_factory("miseq")
```

Want to create a parser for a sequencer that we don't yet support or have an idea for an IRIDA related project?

[Requirements for new parsers](developers/parsers.md)

[Information on the IRIDA python API](developers/api.md)

[Object Model Reference](developers/objects.md)

[Cloud Deployment](developers/cloud.md)
