"""
This file handles selecting a parser, and parsing/validation with it
"""
import logging

import config
import parsers
from progress import upload_status

from . import model_validator


def get_parser_from_config():
    """
    Uses the 'parser' field in the config file to find and return the parser
    :return:
    """
    parser_instance = config.read_config_option("parser")
    return parsers.Parser.factory(parser_instance)


def parse_and_validate(directory):
    """
    Parses and validates a run from a directory
    Throws DirectoryError or ValidationError if invalid

    :param directory:
    :return: a valid sequencing run
    """
    logging.info("*** Beginning Parsing ***")
    parser_instance = get_parser_from_config()

    try:
        sample_sheet = parser_instance.get_sample_sheet(directory)
    except parsers.exceptions.DirectoryError as e:
        logging.debug("parsing_handler:Exception while getting sample sheet from directory")
        raise e

    try:
        sequencing_run = parser_instance.get_sequencing_run(sample_sheet)
    except parsers.exceptions.ValidationError as e:
        logging.debug("parsing_handler:Exception while getting sequencing run with sample_sheet")
        raise e

    logging.info("Validating sequencing run")
    validation_result = model_validator.validate_sequencing_run(sequencing_run)
    if not validation_result.is_valid():
        logging.info("parsing_handler:Exception while validating Sequencing Run")
        raise parsers.exceptions.ValidationError("Sequencing Run is not valid", validation_result)

    logging.info("*** Parsing Done ***")

    return sequencing_run


def run_is_new(directory):
    """
    Given a run directory, returns True or False if run is new
    :param directory:
    :return:
    """
    parser_instance = get_parser_from_config()
    status = parser_instance.find_single_run(directory)
    return _run_is_new_via_directory_status(status)


def _run_is_new_via_directory_status(directory_status):
    """
    Checks if a run directory is new or not

    :param directory_status: a DirectoryStatus object created by the progress module
    :return: True or False
    """
    parser_instance = get_parser_from_config()
    result = upload_status.get_directory_status(
        directory_status.directory,
        parser_instance.get_sample_sheet_file_name()
    )

    return result.status == upload_status.DIRECTORY_STATUS_NEW
