import logging

from pprint import pformat

import api
import parsers
import global_settings

from . import api_handler, parsing_handler


def validate_and_upload_single_entry(directory):
    """
    This function acts as a single point of entry for uploading a directory

    Handles parsing and validating the directory for samples
    Sets up the api layer based on config file
    Verifies samples is able to be uploaded (verifies projects exist)
    Initializes objects/routes on IRIDA to accept Samples (creates samples if they don't exist)
    Starts the upload

    :param directory: Directory of the sequencing run to upload
    :return:
    """
    logging_start_block()
    logging.debug("validate_and_upload_single_entry:Starting {}".format(directory))

    # Do parsing (Also offline validation)
    try:
        sequencing_run = parsing_handler.parse_and_validate(directory)
    except parsers.exceptions.DirectoryError as e:
        # Directory was not valid for some reason
        logging.error("ERROR! An error occurred with directory '{}', with message: {}".format(e.directory, e.message))
        logging.info("Samples not uploaded!")
        return exit_error()
    except parsers.exceptions.ValidationError as e:
        # Sequencing Run / SampleSheet was not valid for some reason
        logging.error("ERROR! Errors occurred during validation with message: {}".format(e.message))
        logging.error("Error list: " + pformat(e.validation_result.error_list))
        logging.info("Samples not uploaded!")
        return exit_error()

    # Initialize the api for first use
    logging.info("*** Connecting to IRIDA ***")
    try:
        api_handler.initialize_api_from_config()
    except api.exceptions.IridaConnectionError as e:
        logging.error("ERROR! Could not initialize irida api.")
        logging.error("Errors: " + pformat(e.args))
        logging.info("Samples not uploaded!")
        return exit_error()
    logging.info("*** Connected ***")

    logging.info("*** Verifying run (online validation) ***")
    try:
        validation_result = api_handler.prepare_and_validate_for_upload(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        return exit_error()

    if not validation_result.is_valid():
        logging.error("Sequencing run can not be uploaded")
        logging.error("Sequencing run can not be uploaded. Encountered {} errors"
                      "".format(validation_result.error_count()))
        logging.error("Errors: " + pformat(validation_result.error_list))
        return exit_error()
    logging.info("*** Run Verified ***")

    # Start upload
    logging.info("*** Starting Upload ***")
    try:
        api_handler.upload_sequencing_run(sequencing_run)
    except api.exceptions.IridaConnectionError as e:
        logging.error("Lost connection to Irida")
        logging.error("Errors: " + pformat(e.args))
        return 1
    logging.info("*** Upload Complete ***")

    logging.info("Samples in directory '{}' have finished uploading!".format(directory))

    return exit_success()


def upload_first_new_run(run_directory_list):
    logging.debug("upload_first_new_run:Starting {}".format(run_directory_list))
    logging.info("Finding first new run in directory: {}".format(run_directory_list))

    try:
        first_run = parsing_handler.get_first_new_run(run_directory_list)
    except Exception as e:  # TODO
        raise e  # Todo

    if first_run is None:
        logging.info("Could not find a new run in directory: {}".format(run_directory_list))
        return exit_success()  # TODO, should this be a success, or maybe a different error code (2) so that we can catch it when scripting with upload_first_new_run uploads

    logging.info("New run found. Starting upload on directory: {}". format(first_run))
    return validate_and_upload_single_entry(first_run)


def exit_error():
    """
    Returns an failed run exit code which ends the process when returned
    :return: 1
    """
    logging_end_block()
    return 1


def exit_success():
    """
    Returns an success run exit code which ends the process when returned
    :return: 0
    """
    logging_end_block()
    return 0


def logging_start_block():
    """
    Logs an information block to the console and file which indicates the start of an upload run.
    Includes the uploader version number set in the global_settings module
    :return:
    """
    logging.info("==================================================")
    logging.info("---------------STARTING UPLOAD RUN----------------")
    logging.info("Uploader Version {}".format(global_settings.UPLOADER_VERSION))
    logging.info("==================================================")


def logging_end_block():
    """
    Logs an block to the console and file that indicates the end of an upload run.
    :return:
    """
    logging.info("==================================================")
    logging.info("----------------ENDING UPLOAD RUN-----------------")
    logging.info("==================================================")
