#!/usr/bin/env python3
"""
This file is the entry point for the command line interface for both bash and windows

It uses argparse, getpass, as well as os to keep the interface operating system agnostic
"""

import argparse
import getpass
import os
import textwrap

from iridauploader import VERSION_NUMBER
import iridauploader.config as config
import iridauploader.core as core
from iridauploader.api import UPLOAD_MODES
from iridauploader.parsers import supported_parsers

DESCRIPTION = textwrap.dedent('''
This program parses sequencing runs and uploads them to IRIDA.

required arguments:
  --d DIRECTORY, --directory DIRECTORY
                        Location of sequencing run to upload.
                        Directory must be writable.
''')


def init_argparser():
    # Set up an argument parser. We are using defaults to stay consistent with other software.
    # description gets added to the usage statements
    argument_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=DESCRIPTION,
        prog="irida-uploader -d DIRECTORY",
        epilog='-c* options can be used without a parameter to prompt for input.')
    # Our main argument. It is required or else an error will be thrown when the program is run
    # Normally we would use a positional argument, but because of our 1 or None config overrides it makes sense to use
    # a optional argument, with the required set to True. We have to suppress the help on the argument, and add it's
    # help information to the formatted description text of the parser for the argument to be shown as required when
    # --help is used.
    argument_parser.add_argument('-d', '--directory',
                                 action='store',
                                 required=True,
                                 help=argparse.SUPPRESS)
    # help='Location of sequencing run to upload. Directory must be writable.')
    # Add the version argument
    argument_parser.add_argument('--version',
                                 action='version', version='IRIDA Uploader {}'.format(VERSION_NUMBER))
    # Optional argument, for using an alternative config file.
    argument_parser.add_argument('-c', '--config',
                                 action='store',
                                 help='Path to an alternative configuration file. '
                                      'This overrides the default config file in the config directory')
    # Optional argument, Force uploading a run even if a non new status file exists
    argument_parser.add_argument('-f', '--force',
                                 action='store_true',  # This line makes it not parse a variable
                                 help='Uploader will ignore the status file, '
                                      'and try to upload even when a run is in non new status.')
    # Optional argument, Force uploading a run even if a non new status file exists
    argument_parser.add_argument('-p', '--continue_partial',
                                 action='store_true',  # This line makes it not parse a variable
                                 help='Uploader will continue an existing upload run when upload status is partial.')
    # Optional argument, Upload all sequencing runs in a directory of runs
    argument_parser.add_argument('-b', '--batch',
                                 action='store_true',  # This line makes it not parse a variable
                                 help='Uploader will expect a directory containing a sequencing run directories, '
                                      'and upload in batch. '
                                      'The list of runs is generated at start time '
                                      '(Runs added to directory mid upload will not be uploaded).')
    # Optional argument, Upload mode
    argument_parser.add_argument('-u', '--upload_mode',
                                 action='store',
                                 help='Choose which upload mode to use. '
                                      'Supported modes: ' + str(UPLOAD_MODES))

    # Optional arguments for overriding config file settings
    # Explanation:
    #   nargs='?', const=True, default=False,
    #   Allows zero or one parameters
    #   If the argument is not given:                      the value will be False           (indicates load from file)
    #   If the argument is given, and no parameter given:  the value will be True            (prompt user for input)
    #   If the argument is given, and parameter is given:  the value will be the parameter   (used to override config)
    argument_parser.add_argument('-ci', '--config_client_id', action='store', nargs='?', const=True, default=False,
                                 help='Override the "client_id" field in config file. '
                                      'This is for the uploader client created in IRIDA, '
                                      'used to handle the data upload')
    argument_parser.add_argument('-cs', '--config_client_secret', action='store', nargs='?', const=True, default=False,
                                 help='Override "client_secret" in config file. '
                                      'This is for the uploader client created in IRIDA, '
                                      'used to handle the data upload')
    argument_parser.add_argument('-cu', '--config_username', action='store', nargs='?', const=True, default=False,
                                 help='Override "username" in config file. This is your IRIDA account username.')
    argument_parser.add_argument('-cp', '--config_password', action='store', nargs='?', const=True, default=False,
                                 help='Override "password" in config file. This corresponds to your IRIDA account.')
    argument_parser.add_argument('-cb', '--config_base_url', action='store', nargs='?', const=True, default=False,
                                 help='Override "base_url" in config file. The api url for your irida instance '
                                      '(example: https://my.irida.server/api/)')
    argument_parser.add_argument('-cr', '--config_parser', action='store', nargs='?', const=True, default=False,
                                 help='Override "parser" in config file. '
                                      'Choose the type of sequencer data that is being uploaded. '
                                      'Supported parsers: ' + str(supported_parsers))
    argument_parser.add_argument('-r', '--readonly',
                                 action='store_true',  # This line makes it not parse a variable
                                 help='Upload in Read Only mode, does not write status or log file to run directory.')
    argument_parser.add_argument('-cd', '--delay', action='store', nargs='?', const=True, default=False,
                                 help='Accepts an Integer for minutes to delay. When set, new runs will have their  '
                                      'status set to delayed. When uploading a run with the delayed status, the run '
                                      'will only upload if the given amount of minutes has passes since it was set to '
                                      'delayed. Default = 0: When set to 0, runs will not be given delayed status.')
    argument_parser.add_argument('-ct', '--config_timeout', action='store', nargs='?', const=True, default=False,
                                 help='Accepts an Integer for the expected transfer time in seconds per MB. '
                                      'Default is 10 second for every MB of data to transfer (100kb/s). Increasing this'
                                      ' number can reduce timeout errors when your transfer speed is very slow.')
    return argument_parser


def _set_config_override(args):
    """
    Check the config override arguments and override
    :param args: list of args from parseargs
    :return:
    """
    client_id = None
    client_secret = None
    username = None
    password = None
    base_url = None
    parser = None
    readonly = None
    delay = None
    timeout = None

    if args.config_client_id is True:
        print("Enter Client ID:")
        client_id = input()
    elif args.config_client_id is not False:
        client_id = args.config_client_id

    if args.config_client_secret is True:
        print("Enter Client Secret:")
        # getpass blanks out the secret entry
        client_secret = getpass.getpass()
    elif args.config_client_secret is not False:
        client_secret = args.config_client_secret

    if args.config_username is True:
        print("Enter Username:")
        username = input()
    elif args.config_username is not False:
        username = args.config_username

    if args.config_password is True:
        print("Enter Password:")
        # getpass blanks out password entry
        password = getpass.getpass()
    elif args.config_password is not False:
        password = args.config_password

    if args.config_base_url is True:
        print("Enter Base IRIDA URL (format: http://my.irida.server/api/):")
        base_url = input()
    elif args.config_base_url is not False:
        base_url = args.config_base_url

    if args.config_parser is True:
        print("Enter Parser to use:")
        parser = input()
    elif args.config_parser is not False:
        parser = args.config_parser

    if args.readonly is True:
        readonly = args.readonly

    if args.delay is True:
        print("Enter delay in minutes (Integer):")
        delay = int(input())
    elif args.delay is not False:
        delay = int(args.delay)

    if args.config_timeout is True:
        print("Enter timeout per MB in seconds (Integer):")
        delay = int(input())
    elif args.config_timeout is not False:
        timeout = int(args.config_timeout)

    config.set_config_options(client_id=client_id,
                              client_secret=client_secret,
                              username=username,
                              password=password,
                              base_url=base_url,
                              parser=parser,
                              readonly=readonly,
                              delay=delay,
                              timeout=timeout)


def _config_uploader(args):
    """
    Sets up config settings for command line uploading
    :param args:
    :return:
    """
    # If a config file is passed in, set it before starting upload
    if args.config:
        config.set_config_file(args.config)
        # config.user_config_file = args.config
    # Init config
    config.setup()
    # Override with any passed in options
    _set_config_override(args)


def main():
    # Parse the arguments passed from the command line and start the upload
    argument_parser = init_argparser()
    args = argument_parser.parse_args()
    # Setup config options
    _config_uploader(args)

    # Verify directory is readable before upload
    if not os.access(args.directory, os.R_OK):  # Cannot access upload directory
        print("ERROR! Specified directory is not readable: {}".format(args.directory))
        return 1

    # Verify force and continue are not both active
    if args.force and args.continue_partial:
        print("ERROR! --force and --continue_partial are mutually exclusive. "
              "To continue a partial upload use --continue_partial. "
              "To upload all samples from the beginning use --force")
        return 1

    # Start Upload
    if args.batch:
        return upload_batch(args.directory, args.force, args.upload_mode, args.continue_partial)
    else:
        return upload(args.directory, args.force, args.upload_mode, args.continue_partial)


def upload(run_directory, force_upload, upload_mode, continue_partial):
    """
    start upload on a single run directory
    :param run_directory:
    :param force_upload:
    :param upload_mode
    :param continue_partial
    :return: exit code 0 or 1
    """
    return core.upload.upload_run_single_entry(run_directory, force_upload, upload_mode, continue_partial).exit_code


def upload_batch(batch_directory, force_upload, upload_mode, continue_partial):
    """
    Start uploading runs in the batch directory
    :param batch_directory:
    :param force_upload:
    :param upload_mode:
    :param continue_partial:
    :return: exit code 0 or 1
    """
    return core.upload.batch_upload_single_entry(batch_directory, force_upload, upload_mode, continue_partial).exit_code


# This is called when the program is run for the first time
if __name__ == "__main__":
    main()
