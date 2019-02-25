import json
import time
import os

from model.directory_status import DirectoryStatus

from . import exceptions


# Module level Constants
# These define the status files valid fields and variables

# File name
STATUS_FILE_NAME = "irida_uploader_status.info"

# Status field for a sequencing run
STATUS_FIELD = "Upload Status"
DATE_TIME_FIELD = "Date Time"

# States that are valid for the status field
DIRECTORY_STATUS_NEW = 'new'
DIRECTORY_STATUS_INVALID = 'invalid'
DIRECTORY_STATUS_PARTIAL = 'partial'
DIRECTORY_STATUS_ERROR = 'error'
DIRECTORY_STATUS_COMPLETE = 'complete'

# list for convenience
DIRECTORY_STATUS_LIST = [
    DIRECTORY_STATUS_NEW,
    DIRECTORY_STATUS_INVALID,
    DIRECTORY_STATUS_PARTIAL,
    DIRECTORY_STATUS_ERROR,
    DIRECTORY_STATUS_COMPLETE
]


def get_directory_status(directory, sample_sheet):
    """
    Gets the directory status based off using '.miseqUploaderInfo' files to track progress

    :param directory: the directory to search for a run
    :param sample_sheet: optional param: if a sample sheet is required for a run,
        the file name for the sample sheet can be added here to validate that it exists
    :return: directory and status dictionary
    """
    result = DirectoryStatus(directory)

    if not os.access(directory, os.W_OK):
        result.status = DIRECTORY_STATUS_INVALID
        result.message = 'Directory cannot be accessed. Please check permissions'
        return result

    file_list = next(os.walk(directory))[2]  # Gets the list of files in the directory
    if sample_sheet not in file_list:
        result.status = DIRECTORY_STATUS_INVALID
        result.message = 'Directory has no valid sample sheet file with the name {}'.format(sample_sheet)
        return result

    if STATUS_FILE_NAME not in file_list:  # no irida_uploader_status.info file yet, has not been uploaded
        result.status = DIRECTORY_STATUS_NEW
        return result

    # Must check status of upload to determine if upload is completed
    uploader_info_file = os.path.join(directory, STATUS_FILE_NAME)
    with open(uploader_info_file, "rb") as reader:
        info_file = json.load(reader)
        status = info_file[STATUS_FIELD]
        if status in DIRECTORY_STATUS_LIST:
            result.status = status
        else:  # the status found in the file is not in the defined list
            raise exceptions.DirectoryError("Cannot access directory", directory)

    return result


def write_directory_status(directory, status):
    """
    Writes a status to the status file:
    Overwrites anything that is in the file

    Writes a timestamp to the time of last written

    :param directory: directory status file is in (or will be created in)
    :param status: status to set the run to
        Should be one of defined module level status constants
    :return: None
    """

    if not os.access(directory, os.W_OK):  # Cannot access upload directory
        raise exceptions.DirectoryError("Cannot access directory", directory)

    uploader_info_file = os.path.join(directory, STATUS_FILE_NAME)

    json_data = {STATUS_FIELD: status,
                 DATE_TIME_FIELD: _get_date_time_field()}

    with open(uploader_info_file, "w") as json_file:
        json.dump(json_data, json_file)


def _get_date_time_field():
    """
    Returns the current date and time as a string
    :return:
    """
    return time.strftime("%Y-%m-%d %H:%M")
