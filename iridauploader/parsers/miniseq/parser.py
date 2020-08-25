import logging
import os

import iridauploader.model as model
import iridauploader.progress as progress

from iridauploader.parsers import BaseParser
from iridauploader.parsers import exceptions
from iridauploader.parsers import common
from iridauploader.parsers.miniseq import sample_parser, validation


class Parser(BaseParser):

    SAMPLE_SHEET_FILE_NAME = 'SampleSheet.csv'
    UPLOAD_COMPLETE_FILE_NAME = 'CompletedJobInfo.xml'

    def __init__(self, parser_type_name='miniseq'):
        """
        Initialize the Parser
        :param parser_type_name: string to be included in metadata of sequencing run for type identification in IRIDA
        """
        super().__init__(
            parser_type_name=parser_type_name,
            required_file_list=[
                Parser.SAMPLE_SHEET_FILE_NAME,
                Parser.UPLOAD_COMPLETE_FILE_NAME
            ])

    @staticmethod
    def get_relative_data_directory():
        """
        Returns path to the sequence file directory, relative to the Sample Sheet

        This is not used in the application but is useful for scripting and cloud deployment

        This includes a '*' character to be interpreted as a wildcard symbol,
        as this sequencer does not make consitant names for data directories, and the * must be gotten from the filesystem

        :return: a string which represents the concatenated path components, as per os.path.join
        """
        data_dir = os.path.join("Alignment_1", "*", "Fastq")
        return data_dir

    @staticmethod
    def get_full_data_directory(sample_sheet):
        """
        Returns the path to where the sequence data files can be found, including the sample_sheet directory

        Note, this hits the os, and as such is not to be used with cloud solutions.
        For cloud solutions, use get_relative_data_directory() and solve the actual path for your cloud environment

        :param sample_sheet: Sample sheet acts as the starting point for the data directory
        :return: a string which represents the concatenated path components, as per os.path.join
        """
        sample_sheet_dir = os.path.dirname(sample_sheet)
        partial_data_dir = os.path.join(sample_sheet_dir, "Alignment_1")
        # Verify the partial path exits, path could not exist if there was a sequencing error
        # Also, if someone runs the miniseq parser on a miseq directory, this is the failure point
        if not os.path.exists(partial_data_dir):
            raise exceptions.DirectoryError(
                ("The uploader was unable to find the data directory, Verify that the run directory is "
                 "undamaged, and that it is a MiniSeq sequencing run."), partial_data_dir)

        # get the directories [1] get the first directory [0]
        data_dir = os.path.join(partial_data_dir, next(os.walk(partial_data_dir))[1][0], "Fastq")
        return data_dir

    def find_runs(self, directory):
        """
        find a list of run directories in the directory given

        :param directory:
        :return: list of DirectoryStatus objects
        """
        logging.info("looking for runs in {}".format(directory))

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
                                            "can not parse samples from this directory {}".format(directory), directory)

        sample_sheet_file_name = Parser.SAMPLE_SHEET_FILE_NAME
        file_list = common.get_file_list(directory)  # Gets the list of files in the directory
        if sample_sheet_file_name not in file_list:
            logging.error("No sample sheet file in the MiniSeq format found")
            raise exceptions.DirectoryError("The directory {} has no sample sheet file in the MiniSeq format"
                                            " with the name {}"
                                            .format(directory, sample_sheet_file_name), directory)
        else:
            logging.debug("Sample sheet found")
            return os.path.join(directory, sample_sheet_file_name)

    def get_sequencing_run(self, sample_sheet, run_data_directory=None, run_data_directory_file_list=None):
        """
        Does local validation on the integrity of the run directory / sample sheet

        Throws a ValidationError with a validation result attached if it cannot make a sequencing run

        :param sample_sheet: Sample Sheet File
        :param run_data_directory: Optional: Directory (including run directory) to data files.
                                   Can be provided for bypassing os calls when developing on cloud systems
        :param run_data_directory_file_list: Optional: List of files in data directory.
                                             Can be provided for bypassing os calls when developing on cloud systems
        :return: SequencingRun
        """

        # get data directory and file list
        validation_result = model.ValidationResult()

        try:
            if run_data_directory is None:
                run_data_directory = Parser.get_full_data_directory(sample_sheet)
            if run_data_directory_file_list is None:
                run_data_directory_file_list = common.get_file_list(run_data_directory)
        except exceptions.DirectoryError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while parsing files")
            raise exceptions.ValidationError("Errors occurred while parsing files", validation_result)

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
            sample_list = sample_parser.parse_sample_list(sample_sheet,
                                                          run_data_directory,
                                                          run_data_directory_file_list)
            sequencing_run = common.build_sequencing_run_from_samples(sample_list,
                                                                      run_metadata,
                                                                      self.get_parser_type_name())
        except exceptions.SequenceFileError as error:
            validation_result.add_error(error)
            logging.error("Errors occurred while building sequence run from sample sheet")
            raise exceptions.ValidationError("Errors occurred while building sequence run from sample sheet",
                                             validation_result)

        return sequencing_run
