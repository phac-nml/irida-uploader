import logging

from pprint import pformat

import api
import parsers
import global_settings
import progress

from . import api_handler, parsing_handler, logger

EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0


def validate_and_upload_single_entry(directory, force_upload=False):
    """
    This function acts as a single point of entry for uploading a directory

    Handles parsing and validating the directory for samples
    Sets up the api layer based on config file
    Verifies samples is able to be uploaded (verifies projects exist)
    Initializes objects/routes on IRIDA to accept Samples (creates samples if they don't exist)
    Starts the upload

    :param directory: Directory of the sequencing run to upload
    :param force_upload: When set to true, the upload status file will be ignored and file will attempt to be uploaded
    :return:
    """
    logging_start_block(directory)
    logging.debug("validate_and_upload_single_entry:Starting {}".format(directory))

    # Only upload if run is new, or force_upload is True
    if not force_upload:
        run_is_new = parsing_handler.run_is_new(directory)
        if not run_is_new:
            logging.error("ERROR! Run in directory {} is not new. It has either been uploaded, "
                          "or an upload was attempted with error. "
                          "Please check the status file 'irida_uploader_status.info' "
                          "in the run directory for more details. "
                          "You can bypass this error by uploading with the --force argument.".format(directory))
            return exit_error()

    # Add progress file to directory
    try:
        progress.write_directory_status(directory, progress.DIRECTORY_STATUS_PARTIAL)
    except progress.exceptions.DirectoryError as e:
        logging.error("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        logging.info("Samples not uploaded!")
        return exit_error()

    # Do parsing (Also offline validation)
    try:
        sequencing_run = parsing_handler.parse_and_validate(directory)
    except parsers.exceptions.DirectoryError as e:
        # Directory was not valid for some reason
        logging.error("ERROR! An error occurred with directory '{}', with message: {}".format(e.directory, e.message))
        logging.info("Samples not uploaded!")
        return exit_error(directory)
    except parsers.exceptions.ValidationError as e:
        # Sequencing Run / SampleSheet was not valid for some reason
        logging.error("ERROR! Errors occurred during validation with message: {}".format(e.message))
        logging.error("Error list: " + pformat(e.validation_result.error_list))
        logging.info("Samples not uploaded!")
        return exit_error(directory)

    # Initialize the api for first use
    logging.info("*** Connecting to IRIDA ***")
    try:
        api_handler.initialize_api_from_config()
    except api.exceptions.IridaConnectionError as e:
        logging.error("ERROR! Could not initialize irida api.")
        logging.error("Errors: " + pformat(e.args))
        logging.info("Samples not uploaded!")
        return exit_error(directory)
    logging.info("*** Connected ***")

    logging.info("*** Verifying run (online validation) ***")
    try:
        validation_result = api_handler.prepare_and_validate_for_upload(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        return exit_error(directory)

    if not validation_result.is_valid():
        logging.error("Sequencing run can not be uploaded")
        logging.error("Sequencing run can not be uploaded. Encountered {} errors"
                      "".format(validation_result.error_count()))
        logging.error("Errors: " + pformat(validation_result.error_list))
        return exit_error(directory)
    logging.info("*** Run Verified ***")

    # Start upload
    logging.info("*** Starting Upload ***")
    try:
        run_id = api_handler.upload_sequencing_run(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        return exit_error(directory)
    logging.info("*** Upload Complete ***")

    # Set progress file to complete
    try:
        progress.write_directory_status(directory, progress.DIRECTORY_STATUS_COMPLETE, run_id=run_id)
    except progress.exceptions.DirectoryError as e:
        # this is an exceptionally rare case (successful upload, but fails to write progress)
        logging.ERROR("ERROR! Error while trying to write status file to directory {} with error message: {}"
                      "".format(e.directory, e.message))
        logging.info("Samples were uploaded, but progress file may be incorrect!")

    logging.info("Samples in directory '{}' have finished uploading!".format(directory))

    logging_end_block()

    return exit_success()


def exit_error(run_directory=None):
    """
    Returns an failed run exit code which ends the process when returned
    :param run_directory: if this is given, the directory status will be set to error
    :return: 1
    """
    if run_directory:
        try:
            progress.write_directory_status(run_directory, progress.DIRECTORY_STATUS_ERROR)
        except progress.exceptions.DirectoryError as e:
            # this is an exceptionally rare case (wrote to directory at start, but fails to write on exit)
            logging.ERROR("ERROR! Error on exit while trying to write status file to directory {} "
                          "with error message: {}".format(e.directory, e.message))

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

