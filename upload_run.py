#!/usr/bin/env python3

import argparse
import getpass
import os

import config
import core
import global_settings


# Set up an argument parser. We are using defaults to stay consistent with other software.
# description gets added to the usage statements
argument_parser = argparse.ArgumentParser(description='This program parses sequencing runs and uploads them to IRIDA.')
# Add the version argument
argument_parser.add_argument('-v', '--version',
                             action='version', version='IRIDA Uploader {}'.format(global_settings.UPLOADER_VERSION))
# Our main argument. It is required or else an error will be thrown when the program is run
argument_parser.add_argument('directory',
                             help='Location of sequencing run to upload. Directory must be writable.')
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
# Optional argument, Upload all sequencing runs in a directory of runs
argument_parser.add_argument('-b', '--batch',
                             action='store_true',  # This line makes it not parse a variable
                             help='Uploader will expect a directory containing a sequencing run directories, '
                                  'and upload in batch. '
                                  'The list of runs is generated at start time '
                                  '(Runs added to directory mid upload will not be uploaded).')

# Optional arguments for overriding config file settings
# Explanation:
#   nargs='?', const=True, default=False,
#       Allows zero or one parameters
#       If the argument is not given:                      the value will be False           (indicates load from file)
#       If the argument is given, and no parameter given:  the value will be True            (prompt user for input)
#       If the argument is given, and parameter is given:  the value will be the parameter   (used to override config)
argument_parser.add_argument('-ci', '--config_client_id', action='store', nargs='?', const=True, default=False,
                             help='Override "client_id" in config file. '
                                  'Can be used without a parameter to prompt for input.')
argument_parser.add_argument('-cs', '--config_client_secret', action='store', nargs='?', const=True, default=False,
                             help='Override "client_secret" in config file. '
                                  'Can be used without a parameter to prompt for input.')
argument_parser.add_argument('-cu', '--config_username', action='store', nargs='?', const=True, default=False,
                             help='Override "username" in config file. '
                                  'Can be used without a parameter to prompt for input.')
argument_parser.add_argument('-cp', '--config_password', action='store', nargs='?', const=True, default=False,
                             help='Override "password" in config file. '
                                  'Can be used without a parameter to prompt for input.')
argument_parser.add_argument('-cb', '--config_base_url', action='store', nargs='?', const=True, default=False,
                             help='Override "base_url" in config file. '
                                  'Can be used without a parameter to prompt for input.')
argument_parser.add_argument('-cr', '--config_parser', action='store', nargs='?', const=True, default=False,
                             help='Override "parser" in config file. '
                                  'Can be used without a parameter to prompt for input.')


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

    if args.config_client_id is True:
        print("Enter Client ID:")
        client_id = input()
    elif args.config_client_id is not False:
        client_id = args.config_client_id

    if args.config_client_secret is True:
        print("Enter Client Secret:")
        client_secret = input()
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

    config.set_config_options(client_id=client_id,
                              client_secret=client_secret,
                              username=username,
                              password=password,
                              base_url=base_url,
                              parser=parser)


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
    args = argument_parser.parse_args()
    # Setup config options
    _config_uploader(args)

    # Verify directory is writable before upload
    if not os.access(args.directory, os.W_OK):  # Cannot access upload directory
        print("ERROR! Specified directory is not writable: {}".format(args.directory))
        return 1

    # Start Upload
    if args.batch:
        return upload_batch(args.directory, args.force)
    else:
        return upload(args.directory, args.force)


def upload(run_directory, force_upload):
    """
    start upload on a single run directory
    :param run_directory:
    :param force_upload:
    :return:
    """
    return core.cli_entry.upload_run_single_entry(run_directory, force_upload)


def upload_batch(batch_directory, force_upload):
    """
    Start uploading runs in the batch directory
    :param batch_directory:
    :param force_upload:
    :return:
    """
    return core.cli_entry.batch_upload_single_entry(batch_directory, force_upload)


# This is called when the program is run for the first time
if __name__ == "__main__":
    main()
