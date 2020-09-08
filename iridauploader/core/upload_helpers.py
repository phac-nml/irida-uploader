"""
This file holds helper functions that assist upload.py

Each function handles it's own try/except block, and updates the directory status
as they progress through their respective tasks
"""

import logging
import time

from pprint import pformat

from iridauploader import api
import iridauploader.parsers as parsers
import iridauploader.progress as progress
from iridauploader.model import DirectoryStatus

from . import api_handler, parsing_handler


def _set_and_write_directory_status(directory_status, status, message=None):
    """
    Given a DirectoryStatus object, sets the status and message, and then writes to the directory status directory

    :param directory_status: DirectoryStatus object
    :param status: a valid DirectoryStatus status
    :param message: string
    :return:
    """
    try:
        directory_status.status = status
        directory_status.message = message
        progress.write_directory_status(directory_status)
    except progress.exceptions.DirectoryError as e:
        logging.error("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        raise e


# ****************************************************************
# upload_single_entry / batch_upload_single_entry helper functions
# ****************************************************************


def set_run_delayed(directory_status):
    """
    Set the directory_status's status to be DELAYED
    :param directory_status:
    :return:
    """
    _set_and_write_directory_status(directory_status, DirectoryStatus.DELAYED)


def delayed_time_has_passed(directory_status, delay_minutes):
    """
    Checks if delay_minutes time has passed since directory_status.time

    See time docs for details on time modules functionality
    https://docs.python.org/3/library/time.html
    :param directory_status: time.struct_time
    :param delay_minutes: Integer
    :return: Boolean
    """
    run_found_time = directory_status.time

    if run_found_time is None or delay_minutes == 0:  # No delay, return True
        return True

    # float representing the time run was found (in seconds)
    run_found_time_float = time.mktime(run_found_time)
    # add delay time to found time
    time_plus_delay_float = run_found_time_float + (delay_minutes * 60)
    # get current time
    current_time_float = time.time()
    # compare current time to time when run is ready
    return current_time_float > time_plus_delay_float


# *************************************
# _validate_and_upload helper functions
# *************************************


def parse_and_validate(directory_status):
    """
    Do the parsing, and offline validation
    :param directory_status: DirectoryStatus object
    :return:
    """
    # Set directory status to partial before starting
    _set_and_write_directory_status(directory_status, DirectoryStatus.PARTIAL)

    try:
        sequencing_run = parsing_handler.parse_and_validate(directory_status.directory)
    except parsers.exceptions.DirectoryError as e:
        # Directory was not valid for some reason
        full_error = "ERROR! An error occurred with directory '{}', with message: {}".format(e.directory, e.message)
        logging.error(full_error)
        logging.info("Samples not uploaded!")
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e
    except parsers.exceptions.ValidationError as e:
        # Sequencing Run / SampleSheet was not valid for some reason
        error_msg = "ERROR! Errors occurred during validation with message: {}".format(e.message)
        logging.error(error_msg)
        error_list_msg = "Error list: " + pformat(e.validation_result.error_list)
        logging.error(error_list_msg)
        logging.info("Samples not uploaded!")
        full_error = error_msg + ", " + error_list_msg
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e

    return sequencing_run


def verify_upload_mode(upload_mode):
    """
    Verifies upload mode string given is a valid upload mode
    :param upload_mode: String
    :return: None, throws Exception if invalid
    """
    valid_upload_mode_list = api_handler.get_upload_modes()
    if upload_mode not in valid_upload_mode_list:
        e = Exception("Upload mode '{}' is not valid, upload mode must be one of {}".format(
            upload_mode,
            valid_upload_mode_list
        ))
        logging.error(e)
        raise e


def init_file_status_list_from_sequencing_run(sequencing_run, directory_status):
    """
    Update status file with sample list and write
    :param sequencing_run:
    :param directory_status:
    :return: None
    """
    directory_status.init_file_status_list_from_sequencing_run(sequencing_run)
    _set_and_write_directory_status(directory_status, DirectoryStatus.PARTIAL)


def initialize_api(directory_status):
    """
    Setup api handler for first use
    :param directory_status
    :return: None
    """
    try:
        api_handler.initialize_api_from_config()
    except api.exceptions.IridaConnectionError as e:
        logging.error("ERROR! Could not initialize irida api.")
        logging.error("Errors: " + pformat(e.args))
        logging.info("Samples not uploaded!")
        full_error = "ERROR! Could not initialize irida api. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e
    logging.info("*** Connected ***")


def irida_prep_and_validation(sequencing_run, directory_status):
    """
    Prepare sequencing run for upload to IRIDA and run validation on against the sequencing_run
    :param sequencing_run:
    :param directory_status
    :return: ValidationResult object
    """
    logging.info("*** Verifying run (online validation) ***")
    try:
        validation_result = api_handler.prepare_and_validate_for_upload(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Lost connection to Irida. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e

    if not validation_result.is_valid():
        logging.error("Sequencing run can not be uploaded")
        logging.error("Sequencing run can not be uploaded. Encountered {} errors"
                      "".format(validation_result.error_count()))
        logging.error("Errors: " + pformat(validation_result.error_list))
        full_error = "Sequencing run can not be uploaded, Errors: " + pformat(validation_result.error_list)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise Exception(full_error)
    logging.info("*** Run Verified ***")


def upload_sequencing_run(sequencing_run, directory_status, upload_mode):
    """
    Starts the actual upload of the sequencing run
    :param sequencing_run:
    :param directory_status:
    :param upload_mode:
    :return: None
    """
    logging.info("*** Starting Upload ***")
    try:
        api_handler.upload_sequencing_run(
            sequencing_run=sequencing_run,
            directory_status=directory_status,
            upload_mode=upload_mode
        )
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Lost connection to Irida. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e
    except api.exceptions.IridaResourceError as e:
        logging.error("Could not access IRIDA resource")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Could not access IRIDA resource Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e
    except api.exceptions.FileError as e:
        logging.error("Could not upload file to IRIDA")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Could not upload file to IRIDA. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        raise e

    _set_and_write_directory_status(directory_status, DirectoryStatus.COMPLETE)
    logging.info("*** Upload Complete ***")
