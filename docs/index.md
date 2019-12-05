# IRIDA Uploader


##Features
* Command Line interface for Linux and Windows
* Single Directory Upload
* MiSeq/MiniSeq/NextSeq Sequencing Run Parser
* Directory Parsing
* Batch Uploads
* Can be used with cron/windows task scheduler for automated uploads
* GUI

## Upcoming Features
* File upload checksum validation
* Post-processing tasks
* Pause and resume uploads

# Getting Started

## GUI Tutorial

You can find a tutorial and walkthrough on the phac-nml github https://github.com/phac-nml/irida-uploader-tutorial

## Download / Install / Setup

### Download

The IRIDA Uploader can be run on any operating system that supports Python.

You can download the source code on [GitHub](https://github.com/phac-nml/irida-uploader).

You can download pre-built packages for Windows from our [GitHub releases page](https://github.com/phac-nml/irida-uploader/releases).

### Installation

#### Windows

Run an installer (links above) and follow along with the install wizard.

You will need to configure your uploader before running. See [Configuration](configuration.md) for details

#### Linux

Make sure Python 3.5 or newer is installed

    $ python3 --version

If python3 is not installed, install with

    $ sudo apt-get install python3

Install pip:

    $ sudo apt-get install python3-pip

### virtualenv usage  

Install virtualenv and setuptools

    $ pip install virtualenv
    $ pip install setuptools

If you already have these packages installed, ensure they are up to date

    $ pip install virtualenv -U
    $ pip install setuptools -U

Download the source code

    $ git clone https://github.com/phac-nml/irida-uploader
    $ cd irida-uploader

Build a virtualenv and install the dependencies automatically with `make`:

    $ make
    
You will need to configure your uploader before running.

### Configuration

You will need to configure IRIDA and the uploader to upload files.

[How to configure](configuration.md)

If you do not create a configuration file, IRIDA uploader will create one for you with default values the first time it try's to upload.

You will need to edit this file with your IRIDA credentials, and the parser that matches your data.

#### Choose a Parser

The config file has a `parser` field that you can use to parse different directory structures

We currently support the following:

`directory` : [Generic Directory](parsers/directory.md)

`miseq` : [Miseq](parsers/miseq.md)

`miniseq` / `iseq` : [MiniSeq / iSeq](parsers/miniseq.md)

`nextseq` : [NextSeq](parsers/nextseq.md)

## Starting an upload

You can upload with the following commands

### Windows:

Open a Command Prompt terminal and use the `iridauploader` command to upload

`C:\Users\username> iridauploader \path\to\my\samples\`

### Linux:

Use the `irida-uploader.sh` script included with the source code to upload.

`./irida-uploader.sh /path/to/the/sequencing/run/`


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

`/home/<user>/.cache/irida_uploader/log/`

#### Windows

`C:\Users\<username>\AppData\Local\irida_uploader\irida_uploader\Logs`

# Problems?

### Problems uploading?
Check the [Errors Page](errors.md) for help with common errors.

### Found a bug or have an idea for a feature?
Create an issue on our [GitHub Issues Board](https://github.com/phac-nml/irida-uploader/issues)

# Developers

Want to create a parser for a sequencer that we don't yet support or have an idea for an IRIDA related project?

[Requirements for new parsers](developers/parsers.md)

[Information on the IRIDA python API](developers/api.md)

[Object Model Reference](developers/objects.md)
