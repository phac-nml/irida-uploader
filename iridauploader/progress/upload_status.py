import json
import os

import iridauploader.config as config
from iridauploader.model.directory_status import DirectoryStatus

from . import exceptions


# Module level Constants
# These define the status files valid fields and variables

# File name
STATUS_FILE_NAME = "irida_uploader_status.info"


def get_directory_status(directory, required_file_list):
    """
    Gets the directory status based off using 'irida_uploader_status.info' files to track progress

    Returns as soon as it finds the case that applies

    :param directory: the directory to search for a run
    :param required_file_list: optional param: a list of required files that
        are required for that run to be considered valid. Example: ['SampleSheet.csv']
    :return: directory and status dictionary
    """
    # Verify directory is readable
    if not os.access(directory, os.R_OK):
        directory_status = DirectoryStatus(directory)
        directory_status.status = DirectoryStatus.INVALID
        directory_status.message = 'Directory cannot be read. Please check permissions'
        return directory_status

    # If readonly is not set, verify directory is writable
    if config.read_config_option("readonly", bool, False) is False:
        if not os.access(directory, os.W_OK):
            directory_status = DirectoryStatus(directory)
            directory_status.status = DirectoryStatus.INVALID
            directory_status.message = 'Directory cannot be written to. Please check permissions or use readonly mode'
            return directory_status

    # Gets the list of files in the directory
    file_list = next(os.walk(directory))[2]

    # Legacy upload catch
    # When the irida-miseq-uploader (old uploader) ran it generated a .miseqUploaderInfo file
    # To prevent uploading runs that used this old system, we assume runs with this file are COMPLETE
    # By default they will not be picked up automatically with --batch because they are set to COMPLETE,
    # but they can still be uploaded using the --force option
    if '.miseqUploaderInfo' in file_list:
        directory_status = DirectoryStatus(directory)
        directory_status.status = DirectoryStatus.COMPLETE
        directory_status.message = "Legacy uploader run. Set to complete to avoid uploading duplicate data."
        return directory_status

    for file_name in required_file_list:
        if file_name not in file_list:
            directory_status = DirectoryStatus(directory)
            directory_status.status = DirectoryStatus.INVALID
            directory_status.message = 'Directory is missing required file with filename {}'.format(file_name)
            return directory_status

    # All pre-validation passed
    # Determine if status file already exists, or if the run is brand new
    if STATUS_FILE_NAME in file_list:  # Status file already exists, use it.
        directory_status = read_directory_status_from_file(directory)
        return directory_status
    else:  # no irida_uploader_status.info file yet, has not been uploaded
        directory_status = DirectoryStatus(directory)
        directory_status.status = DirectoryStatus.NEW
        return directory_status


def read_directory_status_from_file(directory):
    uploader_info_file = os.path.join(directory, STATUS_FILE_NAME)
    with open(uploader_info_file, "rb") as reader:
        data = reader.read().decode()
    json_dict = json.loads(data)

    try:
        directory_status = DirectoryStatus.init_from_json_dict(json_dict)
        if directory_status.status not in DirectoryStatus.VALID_STATUS_LIST:
            raise KeyError("Invalid directory status: {}".format(directory_status.status))
    except KeyError as e:
        # If status file is invalid, create a new directory status with invalid and error message to return instead
        directory_status = DirectoryStatus(directory)
        directory_status.status = DirectoryStatus.INVALID
        directory_status.message = str(e)

    return directory_status


def write_directory_status(directory_status):
    """
    Writes a status to the status file:
    Overwrites anything that is in the file

    Writes a timestamp to the time of last written

    :param directory_status: DirectoryStatus object containing status to write to directory
    :return: None
    """
    if config.read_config_option("readonly", bool, False) is False:
        if not os.access(directory_status.directory, os.W_OK):  # Cannot access upload directory
            raise exceptions.DirectoryError("Cannot access directory", directory_status.directory)

        json_data = directory_status.to_json_dict()

        uploader_info_file = os.path.join(directory_status.directory, STATUS_FILE_NAME)
        with open(uploader_info_file, "w") as json_file:
            json.dump(json_data, json_file, indent=4, sort_keys=True)
            json_file.write("\n")
