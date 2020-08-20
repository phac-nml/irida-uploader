import json
import time
import os

import iridauploader.config as config
from iridauploader.model.directory_status import DirectoryStatus

from . import exceptions


# Module level Constants
# These define the status files valid fields and variables

# File name
STATUS_FILE_NAME = "irida_uploader_status.info"

# Status field for a sequencing run
STATUS_FIELD = "Upload Status"
DATE_TIME_FIELD = "Date Time"
RUN_ID_FIELD = "Run ID"
IRIDA_INSTANCE_FIELD = "IRIDA Instance"
MESSAGE_FIELD = "Message"


def get_directory_status(directory, required_file_list):
    """
    Gets the directory status based off using 'irida_uploader_status.info' files to track progress

    :param directory: the directory to search for a run
    :param required_file_list: optional param: a list of required files that
        are required for that run to be considered valid. Example: ['SampleSheet.csv']
    :return: directory and status dictionary
    """
    result = DirectoryStatus(directory)

    # Verify directory is readable
    if not os.access(directory, os.R_OK):
        result.status = DirectoryStatus.INVALID
        result.message = 'Directory cannot be read. Please check permissions'
        return result

    # If readonly is not set, verify directory is writable
    if config.read_config_option("readonly", bool, False) is False:
        if not os.access(directory, os.W_OK):
            result.status = DirectoryStatus.INVALID
            result.message = 'Directory cannot be written to. Please check permissions or use readonly mode'
            return result

    file_list = next(os.walk(directory))[2]  # Gets the list of files in the directory

    # Legacy upload catch
    # When the irida-miseq-uploader (old uploader) ran it generated a .miseqUploaderInfo file
    # To prevent uploading runs that used this old system, we assume runs with this file are COMPLETE
    # By default they will not be picked up automatically with --batch because they are set to COMPLETE,
    # but they can still be uploaded using the --force option
    if '.miseqUploaderInfo' in file_list:
        result.status = DirectoryStatus.COMPLETE
        result.message = "Legacy uploader run. Set to complete to avoid uploading duplicate data."
        return result

    for file_name in required_file_list:
        if file_name not in file_list:
            result.status = DirectoryStatus.INVALID
            result.message = 'Directory is missing required file with filename {}'.format(file_name)
            return result

    if STATUS_FILE_NAME not in file_list:  # no irida_uploader_status.info file yet, has not been uploaded
        result.status = DirectoryStatus.NEW
        return result

    # Must check status of upload to determine if upload is completed
    uploader_info_file = os.path.join(directory, STATUS_FILE_NAME)
    with open(uploader_info_file, "rb") as reader:
        data = reader.read().decode()
    info_file = json.loads(data)
    status = info_file[STATUS_FIELD]
    if status in DirectoryStatus.VALID_STATUS_LIST:
        result.status = status
        if MESSAGE_FIELD in info_file:
            result.message = info_file[MESSAGE_FIELD]
        else:
            result.message = None
    else:  # the status found in the file is not in the defined list
        raise exceptions.DirectoryError("Invalid Status in status file", directory)

    return result


def write_directory_status(directory_status, run_id=None):
    """
    Writes a status to the status file:
    Overwrites anything that is in the file

    Writes a timestamp to the time of last written

    :param directory_status: DirectoryStatus object containing status to write to directory
    :param run_id: optional, when used, the run id will be included in the status file,
        along with the irida instance the run is uploaded to.
    :return: None
    """

    if not os.access(directory_status.directory, os.W_OK):  # Cannot access upload directory
        raise exceptions.DirectoryError("Cannot access directory", directory_status.directory)

    uploader_info_file = os.path.join(directory_status.directory, STATUS_FILE_NAME)
    if run_id:
        json_data = {STATUS_FIELD: directory_status.status,
                     MESSAGE_FIELD: directory_status.message,
                     DATE_TIME_FIELD: _get_date_time_field(),
                     RUN_ID_FIELD: run_id,
                     IRIDA_INSTANCE_FIELD: config.read_config_option('base_url')}
    else:
        json_data = {STATUS_FIELD: directory_status.status,
                     MESSAGE_FIELD: directory_status.message,
                     DATE_TIME_FIELD: _get_date_time_field()}

    with open(uploader_info_file, "w") as json_file:
        json.dump(json_data, json_file, indent=4, sort_keys=True)
        json_file.write("\n")


def _get_date_time_field():
    """
    Returns the current date and time as a string
    :return:
    """
    return time.strftime("%Y-%m-%d %H:%M")
