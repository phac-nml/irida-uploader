import json
import logging
import os
import time

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
        return DirectoryStatus(directory=directory,
                               status=DirectoryStatus.INVALID,
                               message='Directory cannot be read. Please check permissions')

    # Gets the list of files in the directory
    file_list = next(os.walk(directory))[2]

    # Legacy upload catch
    # When the irida-miseq-uploader (old uploader) ran it generated a .miseqUploaderInfo file
    # To prevent uploading runs that used this old system, we assume runs with this file are COMPLETE
    # By default they will not be picked up automatically with --batch because they are set to COMPLETE,
    # but they can still be uploaded using the --force option
    if '.miseqUploaderInfo' in file_list:
        return DirectoryStatus(directory=directory,
                               status=DirectoryStatus.COMPLETE,
                               message="Legacy uploader run. Set to complete to avoid uploading duplicate data.")

    for file_name in required_file_list:
        if file_name not in file_list:
            return DirectoryStatus(directory=directory,
                                   status=DirectoryStatus.INVALID,
                                   message='Directory is missing required file with filename {}'.format(file_name))

    # All pre-validation passed
    # Determine if status file already exists, or if the run is brand new
    if STATUS_FILE_NAME in file_list:  # Status file already exists, use it.
        return read_directory_status_from_file(directory)
    else:  # no irida_uploader_status.info file yet, has not been uploaded
        return DirectoryStatus(directory=directory, status=DirectoryStatus.NEW)


def read_directory_status_from_file(directory):
    uploader_info_file = os.path.join(directory, STATUS_FILE_NAME)

    try:
        # Read file as json
        with open(uploader_info_file, "rb") as reader:
            data = reader.read().decode()
        json_dict = json.loads(data)
        # Generate DirectoryStatus from json
        directory_status = DirectoryStatus.init_from_json_dict(json_dict, directory)
        if directory_status.status not in DirectoryStatus.VALID_STATUS_LIST:
            raise KeyError("Invalid directory status: {}".format(directory_status.status))
        # When loading from an ERROR sheet, or an old sheet, we must manually add the directory to the object
        if directory_status.directory is None:
            directory_status.directory = directory
    except KeyError as e:
        # If status file is invalid, create a new directory status with invalid and error message to return instead
        directory_status = DirectoryStatus(directory=directory, status=DirectoryStatus.INVALID, message=str(e))
    except Exception:
        # If the file cannot be read (e.g. invalid json), return invalid
        message = "Status file '{}' is malformed. Please delete this file and try again.".format(uploader_info_file)
        return DirectoryStatus(directory=directory, status=DirectoryStatus.INVALID, message=message)

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


def run_is_ready_with_delay(directory_status):
    """
    Expects a NEW or DELAYED directory status

    If a NEW run is given, and the config is set to delay new runs, the run will be set to DELAYED, otherwise it's ready
    If a DELAYED run is given, the run is ready if enough time has passed, otherwise it is not ready yet.

    Writes to directory status file when set to DELAYED

    :param directory_status:
    :return: True when run is ready for upload, otherwise False
    """
    delay_minutes = config.read_config_option("delay", expected_type=int)
    logging.debug("delay_minutes is set to: " + str(delay_minutes))

    # Check if run is new, check if there's a delay
    if directory_status.status_equals(DirectoryStatus.NEW):
        if delay_minutes > 0:
            _set_run_delayed(directory_status)
            logging.info("Run has been delayed for {} minutes.".format(delay_minutes))
            run_is_ready = False
        else:
            logging.info("No delay time given for NEW run. Continuing...")
            run_is_ready = True
    # If run was delayed, check if run can now be uploaded
    elif directory_status.status_equals(DirectoryStatus.DELAYED):
        if _delayed_time_has_passed(directory_status, delay_minutes):
            logging.info("Delayed run is now ready for upload. Continuing...")
            run_is_ready = True
        else:
            logging.info("Delayed run is still not ready for upload.")
            run_is_ready = False
    # This case should be imposable
    else:
        raise Exception("Function called with invalid directory status, This should never happen.")

    return run_is_ready


def _set_run_delayed(directory_status):
    """
    Helper function to set and write directory status as delayed.

    :param directory_status:
    :return:
    """
    directory_status.status = DirectoryStatus.DELAYED
    write_directory_status(directory_status)


def _delayed_time_has_passed(directory_status, delay_minutes):
    """
    Checks if delay_minutes time has passed since directory_status.time

    See time docs for details on time modules functionality
    https://docs.python.org/3/library/time.html
    :param directory_status: time.struct_time
    :param delay_minutes: Integer
    :return: Boolean
    """
    # Delay Time is not set, run is ready for upload
    if delay_minutes == 0 or directory_status.time is None:
        return True

    # float representing the time run was found (in seconds)
    run_found_time_float = time.mktime(directory_status.time)
    # add delay time to found time
    time_plus_delay_float = run_found_time_float + (delay_minutes * 60)
    # get current time
    current_time_float = time.time()
    # compare current time to time when run is ready
    return current_time_float > time_plus_delay_float
