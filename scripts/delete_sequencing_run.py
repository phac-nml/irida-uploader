#!/usr/bin/env python3
"""
This file is a script to delete a sequencing run from irida based on the contents of a run directory
"""

import argparse
import os
import textwrap

from iridauploader import VERSION_NUMBER
import iridauploader.config as config
import iridauploader.core.api_handler as api_handler
import iridauploader.progress.upload_status as upload_status


DESCRIPTION = textwrap.dedent('''
This script deletes a sequencing run from IRIDA based on the contents of a run directory

required arguments:
  -c CONFIG, --config CONFIG
                        Path to configuration file.
  -d DIRECTORY, --directory DIRECTORY
                        Location of sequencing run previously uploaded to delete.
''')
SCRIPT_VERSION = "0.1"


def init_argparser():
    # Set up an argument parser. We are using defaults to stay consistent with other software.
    # description gets added to the usage statements
    argument_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        prog="./delete_sequencing_run.sh -c CONFIG -d DIRECTORY",
    )
    # Our main arguments. They required or else an error will be thrown when the program is run
    argument_parser.add_argument('-c', '--config',
                                 action='store',
                                 required=True,
                                 help=argparse.SUPPRESS)
    argument_parser.add_argument('-d', '--directory',
                                 action='store',
                                 required=True,
                                 help=argparse.SUPPRESS)
    argument_parser.add_argument('--version',
                                 action='version',
                                 version='Script version {} Using IRIDA Uploader {}'
                                         ''.format(SCRIPT_VERSION, VERSION_NUMBER))
    return argument_parser


def main():
    """
    Parse args and validate directory
    """
    argument_parser = init_argparser()
    args = argument_parser.parse_args()
    # set config to be used by api module
    init_conf(args.config)

    # Verify directory is readable before upload
    if not os.access(args.directory, os.R_OK):  # Cannot access upload directory
        print("ERROR! Specified directory is not readable: {}".format(args.directory))
        return 1

    print('Script version {} Using IRIDA Uploader {}'.format(SCRIPT_VERSION, VERSION_NUMBER))
    api = get_api()
    run_id = run_parse(args.directory)
    prompt_user(run_id)
    run_deletion(api, run_id)


def run_parse(directory):
    """
    parse directory for status and display info
    """
    status = get_directory_status(directory)
    print_sample_dict(status)
    return status.run_id


def prompt_user(run_id):
    print("\nVerify that you want this Sequencing Run deleted from IRIDA")
    print("Enter the Run ID of this Sequencing Run to continue.")
    user_input = input()
    if user_input != run_id:
        print("RUN ID DOES NOT MATCH! EXITING!")
        exit(1)


def run_deletion(api, run_id):
    """
    delete sequencing run from IRIDA
    """
    api.delete_seq_run(run_id)
    print("Sequencing Run {} has been deleted.".format(run_id))
    return 0


def init_conf(config_file_path):
    config.set_config_file(config_file_path)
    config.setup()


def get_api():
    api_i = api_handler.initialize_api_from_config()
    print("Connected to IRIDA version: {}".format(api_i.get_irida_version()))
    return api_i


def get_directory_status(directory):
    status = upload_status.read_directory_status_from_file(directory)
    print("\nReading status of directory: {}".format(status.directory))
    print("Run directories status: {}".format(status.status))
    print("Run id: {}".format(status.run_id))
    if status.status != upload_status.DirectoryStatus.COMPLETE:
        print("THIS RUN DIRECTORY IS NOT COMPLETE! EXITING!")
        exit(1)
    return status


def print_sample_dict(status):
    sample_dict = status.sample_status_to_dict()
    print("\nFiles uploaded to the following samples will be deleted!")
    for sample_entry in sample_dict:
        print("Project ID: {}, Sample Name: {}".format(sample_entry['Project ID'], sample_entry['Sample Name']))
    return sample_dict


# This is called when the program is run for the first time
if __name__ == "__main__":
    main()
