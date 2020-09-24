"""
This file contains the single entry functions to upload data that are called via the command line and the gui
These functions return exit codes that get passed up the chain to whatever function calls the uploader (i.e. bash)

It also contains the functions for starting/stopping logging to a directory
"""

import logging

import iridauploader.api as api
import iridauploader.config as config
import iridauploader.parsers as parsers
import iridauploader.progress as progress
from iridauploader.model import DirectoryStatus

from . import api_handler, parsing_handler, logger, exit_return, upload_helpers, VERSION_NUMBER


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
    delay_minutes = config.read_config_option("delay", expected_type=int)

    # Check if a run is invalid, an invalid run cannot be uploaded.
    if directory_status.status_equals(DirectoryStatus.INVALID):
        error_msg = "ERROR! Run in directory {} is invalid. Returned with message: '{}'".format(
            directory_status.directory, directory_status.message)
        logging.error(error_msg)
        return exit_error(error_msg)
    # Check if run is new, if delay config is > 0, delay the run, exit with success
    elif directory_status.status_equals(DirectoryStatus.NEW):
        if delay_minutes > 0:
            upload_helpers.set_run_delayed(directory_status)
            logging.info("Run has been delayed for {} minutes.".format(delay_minutes))
            return exit_success()
    # If run was delayed, check if run can now be uploaded, if not, exit with success
    elif directory_status.status_equals(DirectoryStatus.DELAYED):
        if upload_helpers.delayed_time_has_passed(directory_status, delay_minutes):
            logging.info("Delayed run is ready for upload. Continuing...")
        else:
            logging.info("Delayed run is still not ready for upload.")
            return exit_success()
    # other statuses are error, partial, and complete runs, force upload allows theses
    elif not force_upload:
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

    # upload
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

    # get delay
    delay_minutes = config.read_config_option("delay", expected_type=int)
    logging.debug("delay_minutes is set to: " + str(delay_minutes))

    # get all potential directories to upload
    directory_status_list = parsing_handler.get_run_status_list(batch_directory)
    # list info about directories found
    logging.info("Found {} potential run directories".format(len(directory_status_list)))
    for directory_status in directory_status_list:
        logging.info("DIRECTORY: %s\n"
                     "%30sSTATUS:  %s\n"
                     "%30sDETAILS: %s"
                     % (directory_status.directory, "", directory_status.status, "", directory_status.message))

    upload_list = []
    delayed_list = []
    for directory_status in directory_status_list:
        logging.info("Analysing directory: {}".format(directory_status.directory))
        # ignore invalid directories
        if directory_status.status_equals(DirectoryStatus.INVALID):
            continue
        # Check if run is new, if delay config is > 0, delay the run, else add to upload list
        elif directory_status.status_equals(DirectoryStatus.NEW):
            if delay_minutes > 0:
                upload_helpers.set_run_delayed(directory_status)
                logging.info("Run has been delayed for {} minutes.".format(delay_minutes))
                delayed_list.append(directory_status)
            else:
                upload_list.append(directory_status)
        # If run was delayed, check if run can now be uploaded, else it's still delayed
        elif directory_status.status_equals(DirectoryStatus.DELAYED):
            if upload_helpers.delayed_time_has_passed(directory_status, delay_minutes):
                logging.info("Delayed run is ready for upload. Continuing...")
                upload_list.append(directory_status)
            else:
                logging.info("Delayed run is still not ready for upload.")
                delayed_list.append(directory_status)
        # other statuses are error, partial, and complete runs, force upload allows theses
        elif force_upload:
            upload_list.append(directory_status)

    # Display delayed run count to the user
    if len(delayed_list) > 0:
        logging.info("{} run(s) have been delayed.".format(len(delayed_list)))

    # Display runs to upload count to the user
    if force_upload:
        logging.info("Starting upload for all non invalid and non delayed runs. {} run(s) found. "
                     "(Running with --force)".format(len(upload_list)))
    else:
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
            error_list.append(directory_status)

    logging.info("Uploads completed with {} error(s)".format(len(error_list)))
    for directory_status in error_list:
        logging.warning("Directory '{}' upload exited with ERROR, check log and status file for details"
                        "".format(directory_status.directory))

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

    try:
        # Starting upload process: Parse and do offline verification
        sequencing_run = upload_helpers.parse_and_validate(directory_status)
        upload_helpers.verify_upload_mode(upload_mode)
        upload_helpers.init_file_status_list_from_sequencing_run(sequencing_run, directory_status)

        # Initialize api, run pre upload preparation and validation
        upload_helpers.initialize_api(directory_status)
        upload_helpers.irida_prep_and_validation(sequencing_run, directory_status)

        # Upload run
        upload_helpers.upload_sequencing_run(sequencing_run, directory_status, upload_mode)

    except (progress.exceptions.DirectoryError,
            parsers.exceptions.ValidationError,
            parsers.exceptions.DirectoryError,
            api.exceptions.IridaConnectionError,
            api.exceptions.IridaResourceError,
            api.exceptions.FileError,
            Exception
            ) as e:
        return exit_error(e)

    logging.info("Samples in directory '{}' have finished uploading!".format(directory_status.directory))

    logging_end_block()

    return exit_success()


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
