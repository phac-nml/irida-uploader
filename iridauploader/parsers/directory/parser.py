import logging
import os

import iridauploader.progress as progress

from iridauploader.parsers import exceptions
from iridauploader.parsers import common
from iridauploader.parsers import BaseParser
from iridauploader.parsers.directory import sample_parser, validation


class Parser(BaseParser):

    SAMPLE_SHEET_FILE_NAME = 'SampleList.csv'

    def __init__(self, parser_type_name='directory'):
        """
        Initialize the Parser
        :param parser_type_name: string to be included in metadata of sequencing run for type identification in IRIDA
        """
        super().__init__(parser_type_name=parser_type_name, required_file_list=[Parser.SAMPLE_SHEET_FILE_NAME])

    def find_runs(self, directory):
        """
        find a list of run directories in the directory given

        :param directory:
        :return: list of DirectoryStatus objects
        """
        logging.info("Looking for runs in {}".format(directory))

        runs = []
        directory_list = common.find_directory_list(directory)
        for d in directory_list:
            runs.append(progress.get_directory_status(d, self.get_required_file_list()))

        return runs

    def find_single_run(self, directory):
        """
        Find a run in the base directory given

        :param directory:
        :return: DirectoryStatus object
        """
        logging.info("looking for run in {}".format(directory))

        return progress.get_directory_status(directory, self.get_required_file_list())

    @staticmethod
    def get_sample_sheet(directory):
        """
        gets the sample sheet file path from a given run directory

        :param directory:
        :return:
        """
        logging.info("Looking for sample sheet in {}".format(directory))

        # Checks if we can access to the given directory, return empty and log a warning if we cannot.
        if common.cannot_read_directory(directory):
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

    def get_sequencing_run(self, sample_sheet, run_data_directory_file_list=None):
        """
        Does local validation on the integrity of the run directory / sample sheet

        Throws a ValidationError with a validation result attached if it cannot make a sequencing run

        :param sample_sheet:
        :param run_data_directory_file_list: Optional: List of files in the data directory to verify against the
        SampleList.csv file. This is used when deploying the parsers on a cloud environment.
        :return: SequencingRun
        """

        # Try to get the sample sheet, validate that the sample sheet is valid
        validation_result = validation.validate_sample_sheet(sample_sheet)
        if not validation_result.is_valid():
            logging.error("Errors occurred while getting sample sheet")
            raise exceptions.ValidationError("Errors occurred while getting sample sheet", validation_result)

        # When running with a premade file list, verify files on sample_sheet are in file list
        try:
            if run_data_directory_file_list is not None:
                sample_parser.verify_sample_sheet_file_names_in_file_list(sample_sheet, run_data_directory_file_list)
        except exceptions.SequenceFileError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while building sequence run from sample sheet")
            raise exceptions.ValidationError("Errors occurred while building sequence run from sample sheet",
                                             validation_result)

        # Build a list of sample objects from sample sheet
        try:
            if run_data_directory_file_list is not None:
                sample_list = sample_parser.build_sample_list_from_sample_sheet_no_verify(sample_sheet)
            else:
                sample_list = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(sample_sheet)
        except exceptions.DirectoryError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while parsing files")
            raise exceptions.ValidationError("Errors occurred while parsing files", validation_result)

        # verify samples in sample_list are all of one type, either single or paired end
        if not sample_parser.only_single_or_paired_in_sample_list(sample_list):
            e = exceptions.SampleSheetError(
                ("Your sample sheet is malformed. "
                 "SampleSheet cannot have both paired end and single end runs. "
                 "Make sure all samples are either paired or single."),
                sample_sheet
            )
            validation_result.add_error(e)
            logging.error("Error occurred while building file list: Sample sheet has both paired and single end reads")
            raise exceptions.ValidationError("Errors occurred while building file list.", validation_result)

        # Try to build sequencing run from sample sheet & meta data, raise validation error if errors occur
        try:
            run_metadata = sample_parser.parse_metadata(sample_list)
            sequencing_run = common.build_sequencing_run_from_samples(sample_list,
                                                                      run_metadata,
                                                                      self.get_parser_type_name())
        except exceptions.SequenceFileError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while building sequence run from sample sheet")
            raise exceptions.ValidationError("Errors occurred while building sequence run from sample sheet",
                                             validation_result)

        return sequencing_run
