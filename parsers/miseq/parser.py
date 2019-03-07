import logging
import os

import model
import progress

from .. import exceptions
from . import sample_parser, validation


class Parser:

    @staticmethod
    def get_sample_sheet_file_name():
        return 'SampleSheet.csv'

    @staticmethod
    def _find_directory_list(directory):
        """Find and return all directories in the specified directory.

        Arguments:
        directory -- the directory to find directories in

        Returns: a list of directories including current directory
        """

        # Checks if we can access to the given directory, return empty and log a warning if we cannot.
        if not os.access(directory, os.W_OK):
            raise exceptions.DirectoryError("The directory is not writeable, "
                                            "can not upload samples from this directory {}".format(directory),
                                            directory)

        dir_list = next(os.walk(directory))[1]  # Gets the list of directories in the directory
        full_dir_list = []
        for d in dir_list:
            full_dir_list.append(os.path.join(directory, d))
        return full_dir_list

    @staticmethod
    def find_runs(directory):
        """
        find a list of run directories in the directory given

        :param directory:
        :return: list of DirectoryStatus objects
        """
        logging.info("looking for runs in {}".format(directory))

        runs = []
        directory_list = Parser._find_directory_list(directory)
        for d in directory_list:
            runs.append(progress.get_directory_status(d, Parser.get_sample_sheet_file_name()))

        return runs

    @staticmethod
    def find_single_run(directory):
        """
        Find a run in the base directory given

        :param directory:
        :return: DirectoryStatus object
        """
        logging.info("looking for run in {}".format(directory))

        return progress.get_directory_status(directory, Parser.get_sample_sheet_file_name())

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
                                            "can not parse samples from this directory {}".format(directory), directory)

        sample_sheet_file_name = Parser.get_sample_sheet_file_name()
        file_list = next(os.walk(directory))[2]  # Gets the list of files in the directory
        if sample_sheet_file_name not in file_list:
            logging.error("No sample sheet file in the MiSeq format found")
            raise exceptions.DirectoryError("The directory {} has no sample sheet file in the MiSeq format"
                                            " with the name {}"
                                            .format(directory, sample_sheet_file_name), directory)
        else:
            logging.debug("Sample sheet found")
            return os.path.join(directory, sample_sheet_file_name)

    @staticmethod
    def get_sequencing_run(sample_sheet):
        """
        Does local validation on the integrety of the run directory / sample sheet

        Throws a ValidationError with a valadation result attached if it cannot make a sequencing run

        :param sample_sheet:
        :return: SequencingRun
        """

        # Try to get the sample sheet, validate that the sample sheet is valid
        validation_result = validation.validate_sample_sheet(sample_sheet)
        if not validation_result.is_valid():
            logging.error("Errors occurred while getting sample sheet")
            raise exceptions.ValidationError("Errors occurred while getting sample sheet", validation_result)

        # Try to parse the meta data from the sample sheet, throw validation error if errors occur
        validation_result = model.ValidationResult()
        try:
            run_metadata = sample_parser.parse_metadata(sample_sheet)
        except exceptions.SampleSheetError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while parsing metadata")
            raise exceptions.ValidationError("Errors occurred while parsing metadata", validation_result)

        # Try to build sequencing run from sample sheet & meta data, raise validation error if errors occur
        try:
            sequencing_run = sample_parser.build_sequencing_run_from_samples(sample_sheet, run_metadata)
        except exceptions.SequenceFileError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while building sequence run from sample sheet")
            raise exceptions.ValidationError("Errors occurred while building sequence run from sample sheet",
                                             validation_result)

        return sequencing_run
