"""
This file contains the single entry functions to upload data that are called via the command line and the gui
These functions return exit codes that get passed up the chain to whatever function calls the uploader (i.e. bash)

It also contains the functions for starting/stopping logging to a directory
"""

import logging

from iridauploader import VERSION_NUMBER
import iridauploader.api as api
import iridauploader.config as config
import iridauploader.parsers as parsers
import iridauploader.progress as progress
from iridauploader.model import DirectoryStatus

from . import api_handler, parsing_handler, logger, exit_return, upload_helpers


def upload_run_single_entry(directory, force_upload=False, upload_mode=None, continue_upload=False):
    """
    This function acts as a single point of entry for uploading a directory

    Handles getting a directories run status, and running if conditions are met (valid run, new run or forced upload).

    :param directory: Directory of the sequencing run to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :param upload_mode: String with upload mode to use. When None, default is used.
    :param continue_upload: When set, a PARTIAL status run will be continued from where it left off.
    :return: ExitReturn
    """

    directory_status = parsing_handler.get_run_status(directory)
    parse_as_partial = False

    # Check that directory is writeable, or readonly mode is enabled
    if upload_helpers.directory_has_readonly_conflict(directory_status.directory):
        error_msg = 'Directory cannot be written to. Please check permissions or use readonly mode'
        logging.error(error_msg)
        return exit_error(error_msg)
    # Check if run is New or Delayed, and then do delay logic
    elif (directory_status.status_equals(DirectoryStatus.NEW)
          or directory_status.status_equals(DirectoryStatus.DELAYED)):
        if force_upload:
            logging.debug("Run is skipping delay check via force")
        elif progress.run_is_ready_with_delay(directory_status):
            # Note: This is the "happy path" where upload continues
            logging.debug("Run is ready to upload, continuing")
        else:
            logging.debug("Run is delayed, exiting")
            return exit_success()
    # Check if run is partial, if we are continuing partial runs this block will enable parsing as partial
    # NOTE: its assumed that at most only one of `continue_upload` and `force_upload` are set
    elif directory_status.status_equals(DirectoryStatus.PARTIAL):
        if continue_upload:
            # Happy path for continuing an upload
            logging.info("Continuing upload on a partial run.")
            parse_as_partial = True
        elif force_upload:
            # Note: This is "happy path" 2, where upload starts from beginning with force
            logging.info("Run with status {} is being force uploaded".format(directory_status.status))
        else:
            error_msg = "ERROR! Directory status is PARTIAL. This run can be continued with the --continue_partial" \
                        " argument, or restarted from the beginning with the --force argument."
            logging.error(error_msg)
            return exit_error(error_msg)
    # Check if a run is invalid, an invalid run cannot be uploaded.
    elif directory_status.status_equals(DirectoryStatus.INVALID):
        error_msg = "ERROR! Run in directory {} is invalid. Returned with message: '{}'".format(
            directory_status.directory, directory_status.message)
        logging.error(error_msg)
        return exit_error(error_msg)
    # Check if run is any other status, if force upload is set, continue, otherwise exit
    elif (directory_status.status_equals(DirectoryStatus.ERROR)
          or directory_status.status_equals(DirectoryStatus.COMPLETE)):
        if force_upload:
            # Note: This is "happy path" 2, where upload continues with force
            logging.info("Run with status {} is being force uploaded".format(directory_status.status))
        else:
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
    return _validate_and_upload(directory_status, upload_mode, parse_as_partial)


def batch_upload_single_entry(batch_directory, force_upload=False, upload_mode=None, continue_upload=False):
    """
    This function acts as a single point of entry for batch uploading run directories

    It uses _validate_and_upload as it function for uploading the individual runs

    A list of runs to be uploaded is generated at start up, and all found runs will be attempted to be uploaded.

    :param batch_directory: Directory containing sequencing run directories to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :param upload_mode: String with upload mode to use. When None, default is used.
    :param continue_upload: When True, continues uploading existing partial runs from where they left off
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

    # upload_list contains dicts with the following format
    # {'status': DirectoryStatus, 'partial': boolean}
    upload_list = []
    # delayed_list contains DirectoryStatus objects
    delayed_list = []

    for directory_status in directory_status_list:
        logging.info("Analysing directory: {}".format(directory_status.directory))
        # ignore invalid directories
        if directory_status.status_equals(DirectoryStatus.INVALID):
            continue
        # Check if run is New or Delayed, and then do delay logic
        elif (directory_status.status_equals(DirectoryStatus.NEW)
              or directory_status.status_equals(DirectoryStatus.DELAYED)):
            if force_upload:
                logging.debug("BATCH: Run is being added with force")
                upload_list.append({"status": directory_status, "partial": False})
            elif progress.run_is_ready_with_delay(directory_status):
                # Note: This is the "happy path" where upload continues
                logging.debug("BATCH: Run is ready to upload")
                upload_list.append({"status": directory_status, "partial": False})
            else:
                logging.debug("BATCH: Run is delayed")
                delayed_list.append(directory_status)
        # Check if run is partial, if we are continuing partial runs this block will enable parsing as partial
        # NOTE: its assumed that at most only one of `continue_upload` and `force_upload` are set
        elif directory_status.status_equals(DirectoryStatus.PARTIAL):
            if continue_upload:
                # Happy path for continuing an upload
                logging.debug("BATCH: Run is ready to continue upload as partial")
                upload_list.append({"status": directory_status, "partial": True})
            elif force_upload:
                # Note: This is "happy path" 2, where upload continues with force
                logging.debug("BATCH: Partial Run is being added with force")
                upload_list.append({"status": directory_status, "partial": False})
            else:
                logging.debug("BATCH: Partial Run is skipped")
                continue
        # other statuses are error, partial, and complete runs, force upload allows theses
        elif (directory_status.status_equals(DirectoryStatus.ERROR)
              or directory_status.status_equals(DirectoryStatus.COMPLETE)):
            if force_upload:
                logging.debug("BATCH: Run is forced for upload")
                upload_list.append({"status": directory_status, "partial": False})
            else:
                logging.debug("BATCH: Run is skipped")
                continue

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

    # run uploads (including partial), keep track of which directories did not upload
    error_list = []
    for directory_status_dict in upload_list:
        result = _validate_and_upload(directory_status_dict['status'], upload_mode, directory_status_dict['partial'])
        if result.exit_code == exit_return.EXIT_CODE_ERROR:
            error_list.append(directory_status_dict['status'])

    logging.info("Uploads completed with {} error(s)".format(len(error_list)))
    for directory_status in error_list:
        logging.warning("Directory '{}' upload exited with ERROR, check log and status file for details"
                        "".format(directory_status.directory))

    logging.info("Batch upload complete, Exiting!")
    return exit_success()


def _validate_and_upload(directory_status, upload_mode, continue_from_partial):
    """
    This function attempts to upload a single run directory

    Handles parsing and validating the directory for samples
    Sets up the api layer based on config file
    Verifies samples is able to be uploaded (verifies projects exist)
    Initializes objects/routes on IRIDA to accept Samples (creates samples if they don't exist)
    Starts the upload

    :param directory_status: DirectoryStatus object that has directory to try upload
    :param upload_mode: String, mode to use when uploading assemblies
    :param continue_from_partial: when set, already uploaded samples will be skipped, and existing run_id will be used
    :return: ExitReturn
    """
    logging_start_block(directory_status.directory)
    logging.debug("upload_run_single_entry:Starting {}".format(directory_status.directory))
    logging.info("Starting upload for '{}' with continue partial upload = '{}'".format(
        directory_status.directory, str(continue_from_partial)))

    try:
        # Starting upload process: Parse and do offline verification
        sequencing_run = upload_helpers.parse_and_validate(directory_status, continue_from_partial)
        upload_helpers.verify_upload_mode(upload_mode)
        upload_helpers.init_file_status_list_from_sequencing_run(sequencing_run, directory_status)

        # Initialize api, run pre upload preparation and validation
        upload_helpers.initialize_api(directory_status)
        upload_helpers.irida_prep_and_validation(sequencing_run, directory_status)

        # Upload run
        upload_helpers.upload_sequencing_run(sequencing_run, directory_status, upload_mode, continue_from_partial)

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
