import logging

from pprint import pformat

import api
import parsers
import global_settings
import progress
from model import DirectoryStatus

from . import api_handler, parsing_handler, logger

EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0


def upload_run_single_entry(directory, force_upload=False):
    """
    This function acts as a single point of entry for uploading a directory
    todo: rewrite

    Handles getting a directories run status, and running if conditions are met (valid run, new run or forced upload).

    :param directory:
    :param force_upload:
    :return:
    """
    directory_status = parsing_handler.get_run_status(directory)
    # Check if a run is invalid, an invalid run cannot be uploaded.
    if directory_status.status_equals(DirectoryStatus.INVALID):
        logging.error("ERROR! Run in directory {} is invalid. Returned with message: '{}'"
                      "".format(directory_status.directory, directory_status.message))
        return exit_error()

    # Only upload if run is new, or force_upload is True
    if not force_upload:
        if not directory_status.status_equals(DirectoryStatus.NEW):
            logging.error("ERROR! Run in directory {} is not new. It has either been uploaded, "
                          "or an upload was attempted with error. "
                          "Please check the status file 'irida_uploader_status.info' "
                          "in the run directory for more details. "
                          "You can bypass this error by uploading with the --force argument.".format(directory))
            return exit_error()

    return _validate_and_upload(directory_status)


def _validate_and_upload(directory_status):
    """
    This function attempts to upload a single run directory

    todo: rewrite
    Handles parsing and validating the directory for samples
    Sets up the api layer based on config file
    Verifies samples is able to be uploaded (verifies projects exist)
    Initializes objects/routes on IRIDA to accept Samples (creates samples if they don't exist)
    Starts the upload

    :param directory: Directory of the sequencing run to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :return:
    """
    logging_start_block(directory_status.directory)
    logging.debug("upload_run_single_entry:Starting {}".format(directory_status.directory))

    # Add progress file to directory
    try:
        directory_status.status = DirectoryStatus.PARTIAL
        progress.write_directory_status(directory_status)
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
        logging.error("ERROR! An error occurred with directory '{}', with message: {}".format(e.directory, e.message))
        logging.info("Samples not uploaded!")
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()
    except parsers.exceptions.ValidationError as e:
        # Sequencing Run / SampleSheet was not valid for some reason
        logging.error("ERROR! Errors occurred during validation with message: {}".format(e.message))
        logging.error("Error list: " + pformat(e.validation_result.error_list))
        logging.info("Samples not uploaded!")
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()

    # Initialize the api for first use
    logging.info("*** Connecting to IRIDA ***")
    try:
        api_handler.initialize_api_from_config()
    except api.exceptions.IridaConnectionError as e:
        logging.error("ERROR! Could not initialize irida api.")
        logging.error("Errors: " + pformat(e.args))
        logging.info("Samples not uploaded!")
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()
    logging.info("*** Connected ***")

    logging.info("*** Verifying run (online validation) ***")
    try:
        validation_result = api_handler.prepare_and_validate_for_upload(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()

    if not validation_result.is_valid():
        logging.error("Sequencing run can not be uploaded")
        logging.error("Sequencing run can not be uploaded. Encountered {} errors"
                      "".format(validation_result.error_count()))
        logging.error("Errors: " + pformat(validation_result.error_list))
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()
    logging.info("*** Run Verified ***")

    # Start upload
    logging.info("*** Starting Upload ***")
    try:
        run_id = api_handler.upload_sequencing_run(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        return exit_error()
    logging.info("*** Upload Complete ***")

    # Set progress file to complete
    try:
        directory_status.status = DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status, run_id=run_id)
    except progress.exceptions.DirectoryError as e:
        # this is an exceptionally rare case (successful upload, but fails to write progress)
        logging.ERROR("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        logging.info("Samples were uploaded, but progress file may be incorrect!")

    logging.info("Samples in directory '{}' have finished uploading!".format(directory_status.directory))

    logging_end_block()

    return exit_success()


def batch_upload_single_entry(batch_directory, force_upload=False):
    """
    This function acts as a single point of entry for batch uploading run directories

    It uses upload_run_single_entry as it function for uploading the individual runs

    A list of runs to be uploaded is generated at start up, and all found runs will be attempted to be uploaded.

    :param batch_directory: Directory containing sequencing run directories to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :return:
    """
    logging.debug("batch_upload_single_entry:Starting {} with force={}".format(batch_directory, force_upload))

    directory_status_list = parsing_handler.get_run_status_list(batch_directory)

    logging.info("Found {} potential run directories".format(len(directory_status_list)))
    for directory_status in directory_status_list:
        if directory_status.status_equals(DirectoryStatus.INVALID):
            logging.info("DIRECTORY: %s\n"
                         "%30sSTATUS:  %s\n"
                         "%30sDETAILS: %s"
                         % (directory_status.directory, "", directory_status.status, "", directory_status.message))
        else:
            logging.info("DIRECTORY: %s\n"
                         "%30sSTATUS:  %s"
                         % (directory_status.directory, "", directory_status.status))

    if force_upload:
        upload_list = [x for x in directory_status_list if not x.status_equals(DirectoryStatus.INVALID)]
        logging.info("Starting upload for all non invalid runs. {} runs found. "
                     "(Running with --force)".format(len(upload_list)))
    else:
        upload_list = [x for x in directory_status_list if x.status_equals(DirectoryStatus.NEW)]
        logging.info("Starting upload for all new runs. {} runs found.".format(len(upload_list)))

    for directory_status in upload_list:
        logging.info("Starting upload for {}".format(directory_status.directory))
        result = _validate_and_upload(directory_status)
        print("THING ASDF: {}".format(result))#todo

    logging.info("Finished, Exiting!")
    return exit_success()


def exit_error():
    """
    Returns an failed run exit code which ends the process when returned
    :return: 1
    """
    logging_end_block()
    return EXIT_CODE_ERROR


def exit_success():
    """
    Returns an success run exit code which ends the process when returned
    :return: 0
    """
    return EXIT_CODE_SUCCESS


def logging_start_block(directory):
    """
    Logs an information block to the console and file which indicates the start of an upload run.
    Includes the uploader version number set in the global_settings module
    :return:
    """
    logger.add_log_to_directory(directory)
    logging.info("==================================================")
    logging.info("---------------STARTING UPLOAD RUN----------------")
    logging.info("Uploader Version {}".format(global_settings.UPLOADER_VERSION))
    logging.info("Logging to file in: " + global_settings.log_file)
    logging.info("==================================================")


def logging_end_block():
    """
    Logs an block to the console and file that indicates the end of an upload run.
    :return:
    """
    logging.info("==================================================")
    logging.info("----------------ENDING UPLOAD RUN-----------------")
    logging.info("==================================================")
    logger.remove_directory_logger()

