"""
This file holds helper functions that assist upload.py

Each function handles it's own try/except block, and updates the directory status
as they progress through their respective tasks
"""

import logging
import os

from pprint import pformat

from iridauploader import api
import iridauploader.config as config
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

def directory_has_readonly_conflict(directory):
    """
    Returns True if directory is not writable and readonly is not True
    Else returns False
    :param directory:
    :return: boolean
    """
    if (config.read_config_option("readonly", bool, False) is False and not os.access(directory, os.W_OK)):
        return True
    else:
        return False


def set_run_delayed(directory_status):
    """
    Set the directory_status's status to be DELAYED
    :param directory_status:
    :return:
    """
    _set_and_write_directory_status(directory_status, DirectoryStatus.DELAYED)


# *************************************
# _validate_and_upload helper functions
# *************************************


def parse_and_validate(directory_status, parse_as_partial):
    """
    Do the parsing, and offline validation
    :param directory_status: DirectoryStatus object
    :param parse_as_partial: sequencing_run will not include any samples that have already been uploaded
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
    # When continuing a partial run, filter out already uploaded samples
    if parse_as_partial:
        sequencing_run = set_uploaded_samples_to_skip(sequencing_run, directory_status.get_sample_status_list())

    return sequencing_run


def set_uploaded_samples_to_skip(sequencing_run, sample_status_list):
    """
    Given a complete sequencing run, remove all samples that have been marked as uploaded in the sample status list
    :param sequencing_run: sequencing run to filter
    :param sample_status_list: full sample list to check against
    :return: sequencing_run
    """
    # This block looks worse than it is, worst case is O(n^2)
    # There are "cleaner" but less readable ways to do this in the same runtime, but readability > reduced line count
    for project in sequencing_run.project_list:
        for sample in project.sample_list:
            for sample_status in sample_status_list:
                if (sample_status.uploaded is True
                        and sample_status.sample_name == sample.sample_name
                        and str(sample_status.project_id) == str(project.id)):
                    # If a sample has already been uploaded, skip it
                    sample.skip = True

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


def upload_sequencing_run(sequencing_run, directory_status, upload_mode, upload_from_partial=False):
    """
    Starts the actual upload of the sequencing run
    :param sequencing_run:
    :param directory_status:
    :param upload_mode:
    :param upload_from_partial: Default False, when continuing from a partial run, we can reuse the the run_id
    :return: None
    """
    logging.info("*** Starting Upload ***")
    try:
        # If continuing a partial run, use the existing run_id
        if upload_from_partial:
            run_id = directory_status.run_id
        else:
            run_id = None
        # Upload
        api_handler.upload_sequencing_run(
            sequencing_run=sequencing_run,
            directory_status=directory_status,
            upload_mode=upload_mode,
            run_id=run_id
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
