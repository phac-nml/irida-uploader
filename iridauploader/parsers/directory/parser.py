import logging
import os

import iridauploader.progress as progress
import iridauploader.model as model

from iridauploader.parsers import exceptions
from iridauploader.parsers import common
from iridauploader.parsers.directory import sample_parser, validation


class Parser:

    SAMPLE_SHEET_FILE_NAME = 'SampleList.csv'

    @staticmethod
    def get_required_file_list():
        """
        Returns a list of files that are required for a run directory to be considered valid
        :return: [files_names]
        """
        return [Parser.SAMPLE_SHEET_FILE_NAME]

    @staticmethod
    def find_runs(directory):
        """
        find a list of run directories in the directory given

        :param directory:
        :return: list of DirectoryStatus objects
        """
        logging.info("Looking for runs in {}".format(directory))

        runs = []
        directory_list = common.find_directory_list(directory)
        for d in directory_list:
            runs.append(progress.get_directory_status(d, Parser.get_required_file_list()))

        return runs

    @staticmethod
    def find_single_run(directory):
        """
        Find a run in the base directory given

        :param directory:
        :return: DirectoryStatus object
        """
        logging.info("looking for run in {}".format(directory))

        return progress.get_directory_status(directory, Parser.get_required_file_list())

    @staticmethod
    def get_sample_sheet(directory):
        """
        gets the sample sheet file path from a given run directory

        :param directory:
        :return:
        """
        logging.info("Looking for sample sheet in {}".format(directory))

        # Checks if we can access to the given directory, return empty and log a warning if we cannot.
        if not os.access(directory, os.W_OK):
            logging.error(("The directory is not accessible, can not parse samples from this directory {}"
                           "".format(directory), directory))
            raise exceptions.DirectoryError("The directory is not accessible, "
                                            "can not parse samples from this directory {}".format(directory),
                                            directory)

        sample_sheet_file_name = Parser.SAMPLE_SHEET_FILE_NAME
        file_list = common.get_file_list(directory)
        if sample_sheet_file_name not in file_list:
            logging.error("No sample sheet file in the Directory Upload format found")
            raise exceptions.DirectoryError("The directory {} has no sample sheet file in the Directory Upload format "
                                            "with the name {}"
                                            "".format(directory, sample_sheet_file_name), directory)
        else:
            logging.debug("Sample sheet found")
            return os.path.join(directory, sample_sheet_file_name)

    @staticmethod
    def get_sequencing_run(sample_sheet, run_data_directory_file_list=None):
        """
        Does local validation on the integrity of the run directory / sample sheet

        Throws a ValidationError with a validation result attached if it cannot make a sequencing run

        :param sample_sheet:
        :return: SequencingRun
        """

        # get file list
        validation_result = model.ValidationResult()

        try:
            if run_data_directory_file_list is None:
                data_dir = os.path.dirname(sample_sheet)
                run_data_directory_file_list = common.get_file_list(data_dir)
        except exceptions.DirectoryError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while parsing files")
            raise exceptions.ValidationError("Errors occurred while parsing files", validation_result)

        # Try to get the sample sheet, validate that the sample sheet is valid
        validation_result = validation.validate_sample_sheet(sample_sheet)
        if not validation_result.is_valid():
            logging.error("Errors occurred while getting sample sheet")
            raise exceptions.ValidationError("Errors occurred while getting sample sheet", validation_result)

        # Try to build sequencing run from sample sheet & meta data, raise validation error if errors occur
        try:
            sample_list = sample_parser.parse_sample_list(sample_sheet, run_data_directory_file_list)
            run_metadata = sample_parser.parse_metadata(sample_list)
            sequencing_run = common.build_sequencing_run_from_samples(sample_list, run_metadata)
        except exceptions.SequenceFileError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while building sequence run from sample sheet")
            raise exceptions.ValidationError("Errors occurred while building sequence run from sample sheet",
                                             validation_result)

        return sequencing_run
