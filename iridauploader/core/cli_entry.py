import logging

from pprint import pformat

import iridauploader.api as api
import iridauploader.config as config
import iridauploader.parsers as parsers
import iridauploader.progress as progress
from iridauploader.model import DirectoryStatus

from . import api_handler, parsing_handler, logger, exit_return

VERSION_NUMBER = "0.5.1"


def upload_run_single_entry(directory, force_upload=False, upload_mode=None):
    """
    This function acts as a single point of entry for uploading a directory

    Handles getting a directories run status, and running if conditions are met (valid run, new run or forced upload).

    :param directory: Directory of the sequencing run to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :param upload_mode: String with upload mode to use. When None, default is used.
    :return: ExitReturn
    """
    directory_status = parsing_handler.get_run_status(directory)
    # Check if a run is invalid, an invalid run cannot be uploaded.
    if directory_status.status_equals(DirectoryStatus.INVALID):
        error_msg = "ERROR! Run in directory {} is invalid. Returned with message: '{}'".format(
            directory_status.directory, directory_status.message)
        logging.error(error_msg)
        return exit_error(error_msg)

    # Only upload if run is new, or force_upload is True
    if not force_upload:
        if not directory_status.status_equals(DirectoryStatus.NEW):
            error_msg = "ERROR! Run in directory {} is not new. It has either been uploaded, " \
                        "or an upload was attempted with error. " \
                        "Please check the status file 'irida_uploader_status.info' " \
                        "in the run directory for more details. " \
                        "You can bypass this error by uploading with the --force argument.".format(directory)
            logging.error(error_msg)
            return exit_error(error_msg)

    # get default upload mode if None
    if upload_mode is None:
        upload_mode = api_handler.get_default_upload_mode()

    return _validate_and_upload(directory_status, upload_mode)


def batch_upload_single_entry(batch_directory, force_upload=False, upload_mode=None):
    """
    This function acts as a single point of entry for batch uploading run directories

    It uses _validate_and_upload as it function for uploading the individual runs

    A list of runs to be uploaded is generated at start up, and all found runs will be attempted to be uploaded.

    :param batch_directory: Directory containing sequencing run directories to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :param upload_mode: String with upload mode to use. When None, default is used.
    :return: ExitReturn
    """
    logging.debug("batch_upload_single_entry:Starting {} with force={}".format(batch_directory, force_upload))
    # get all potential directories to upload
    directory_status_list = parsing_handler.get_run_status_list(batch_directory)
    # list info about directories found
    logging.info("Found {} potential run directories".format(len(directory_status_list)))
    for directory_status in directory_status_list:
        logging.info("DIRECTORY: %s\n"
                     "%30sSTATUS:  %s\n"
                     "%30sDETAILS: %s"
                     % (directory_status.directory, "", directory_status.status, "", directory_status.message))

    # if `force` is on, only don't upload invalid runs
    if force_upload:
        upload_list = [x for x in directory_status_list if not x.status_equals(DirectoryStatus.INVALID)]
        logging.info("Starting upload for all non invalid runs. {} run(s) found. "
                     "(Running with --force)".format(len(upload_list)))
    # without `force` only upload new runs
    else:
        upload_list = [x for x in directory_status_list if x.status_equals(DirectoryStatus.NEW)]
        logging.info("Starting upload for all new runs. {} run(s) found.".format(len(upload_list)))

    # get default upload mode if None
    if upload_mode is None:
        upload_mode = api_handler.get_default_upload_mode()

    # run upload, keep track of which directories did not upload
    error_list = []
    for directory_status in upload_list:
        logging.info("Starting upload for {}".format(directory_status.directory))
        result = _validate_and_upload(directory_status, upload_mode)
        if result.exit_code == exit_return.EXIT_CODE_ERROR:
            error_list.append(directory_status.directory)

    logging.info("Uploads completed with {} error(s)".format(len(error_list)))
    for directory in error_list:
        logging.warning("Directory '{}' upload exited with ERROR, check log and status file for details"
                        "".format(directory))

    logging.info("Batch upload complete, Exiting!")
    return exit_success()


def _validate_and_upload(directory_status, upload_mode):
    """
    This function attempts to upload a single run directory

    Handles parsing and validating the directory for samples
    Sets up the api layer based on config file
    Verifies samples is able to be uploaded (verifies projects exist)
    Initializes objects/routes on IRIDA to accept Samples (creates samples if they don't exist)
    Starts the upload

    :param directory_status: DirectoryStatus object that has directory to try upload
    :param upload_mode: String, mode to use when uploading assemblies
    :return: ExitReturn
    """
    logging_start_block(directory_status.directory)
    logging.debug("upload_run_single_entry:Starting {}".format(directory_status.directory))

    # Add progress file to directory
    try:
        _set_and_write_directory_status(directory_status, DirectoryStatus.PARTIAL)
    except progress.exceptions.DirectoryError as e:
        logging.error("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        logging.info("Samples not uploaded!")
        return exit_error()

    # Do parsing (Also offline validation)
    try:
        sequencing_run = parsing_handler.parse_and_validate(directory_status.directory)
    except parsers.exceptions.DirectoryError as e:
        # Directory was not valid for some reason
        full_error = "ERROR! An error occurred with directory '{}', with message: {}".format(e.directory, e.message)
        logging.error(full_error)
        logging.info("Samples not uploaded!")
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)
    except parsers.exceptions.ValidationError as e:
        # Sequencing Run / SampleSheet was not valid for some reason
        error_msg = "ERROR! Errors occurred during validation with message: {}".format(e.message)
        logging.error(error_msg)
        error_list_msg = "Error list: " + pformat(e.validation_result.error_list)
        logging.error(error_list_msg)
        logging.info("Samples not uploaded!")
        full_error = error_msg + ", " + error_list_msg
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)

    # Check if upload_mode is valid
    # Todo: This should get split into another block when resume upload gets added
    # Keep this simple for now until the bigger refactor
    valid_upload_mode_list = api_handler.get_upload_modes()
    if upload_mode not in valid_upload_mode_list:
        e = "Upload mode '{}' is not valid, upload mode must be one of {}".format(
            upload_mode,
            valid_upload_mode_list
        )
        logging.error(e)
        return exit_error(e)

    # Initialize the api for first use
    logging.info("*** Connecting to IRIDA ***")
    try:
        api_handler.initialize_api_from_config()
    except api.exceptions.IridaConnectionError as e:
        logging.error("ERROR! Could not initialize irida api.")
        logging.error("Errors: " + pformat(e.args))
        logging.info("Samples not uploaded!")
        full_error = "ERROR! Could not initialize irida api. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)
    logging.info("*** Connected ***")

    logging.info("*** Verifying run (online validation) ***")
    try:
        validation_result = api_handler.prepare_and_validate_for_upload(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Lost connection to Irida. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)

    if not validation_result.is_valid():
        logging.error("Sequencing run can not be uploaded")
        logging.error("Sequencing run can not be uploaded. Encountered {} errors"
                      "".format(validation_result.error_count()))
        logging.error("Errors: " + pformat(validation_result.error_list))
        full_error = "Sequencing run can not be uploaded, Errors: " + pformat(validation_result.error_list)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(full_error)
    logging.info("*** Run Verified ***")

    # Start upload
    logging.info("*** Starting Upload ***")
    try:
        run_id = api_handler.upload_sequencing_run(sequencing_run=sequencing_run, upload_mode=upload_mode)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Lost connection to Irida. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)
    except api.exceptions.IridaResourceError as e:
        logging.error("Could not access IRIDA resource")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Could not access IRIDA resource Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)
    except api.exceptions.FileError as e:
        logging.error("Could not upload file to IRIDA")
        logging.error("Errors: " + pformat(e.args))
        full_error = "Could not upload file to IRIDA. Errors: " + pformat(e.args)
        _set_and_write_directory_status(directory_status, DirectoryStatus.ERROR, full_error)
        return exit_error(e)
    logging.info("*** Upload Complete ***")

    # Set progress file to complete
    try:
        _set_and_write_directory_status(directory_status, DirectoryStatus.COMPLETE, run_id=run_id)
    except progress.exceptions.DirectoryError as e:
        # this is an exceptionally rare case (successful upload, but fails to write progress)
        logging.ERROR("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        logging.info("Samples were uploaded, but progress file may be incorrect!")

    logging.info("Samples in directory '{}' have finished uploading!".format(directory_status.directory))

    logging_end_block()

    return exit_success()


def _set_and_write_directory_status(directory_status, status, message=None, run_id=None):
    """
    Given a DirectoryStatus object, sets the status and message, and then writes to the directory status directory

    :param directory_status: DirectoryStatus object
    :param status: a valid DirectoryStatus status
    :param message: string
    :param run_id: optional, if provided, the run id and irida instance will be included when written
    :return:
    """
    if config.read_config_option("readonly", bool, False) is False:
        directory_status.status = status
        directory_status.message = message
        progress.write_directory_status(directory_status, run_id)


def exit_error(error):
    """
    Returns an failed run exit code which ends the process when returned
    :return: ExitReturn with EXIT_CODE_ERROR
    """
    logging_end_block()
    return exit_return.ExitReturn(exit_return.EXIT_CODE_ERROR, error)


def exit_success():
    """
    Returns an success run exit code which ends the process when returned
    :return: ExitReturn with EXIT_CODE_SUCCESS
    """
    return exit_return.ExitReturn(exit_return.EXIT_CODE_SUCCESS)


def logging_start_block(directory):
    """
    Logs an information block to the console and file which indicates the start of an upload run.
    Includes the uploader version number set in this module
    :return:
    """
    if config.read_config_option("readonly", bool, False) is False:
        logger.add_log_to_directory(directory)
    logging.info("==================================================")
    logging.info("---------------STARTING UPLOAD RUN----------------")
    logging.info("Uploader Version {}".format(VERSION_NUMBER))
    logging.info("Logging to file in: " + logger.get_user_log_dir())
    logging.info("==================================================")


def logging_end_block():
    """
    Logs an block to the console and file that indicates the end of an upload run.
    :return:
    """
    logging.info("==================================================")
    logging.info("----------------ENDING UPLOAD RUN-----------------")
    logging.info("==================================================")
    if config.read_config_option("readonly", bool, False) is False:
        logger.remove_directory_logger()
