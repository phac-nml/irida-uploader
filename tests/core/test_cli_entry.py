import unittest
from unittest.mock import patch, MagicMock, Mock
from os import path
import os

from core import cli_entry, logger
from model import DirectoryStatus
from parsers.exceptions import DirectoryError

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestValidateAndUploadSingleEntry(unittest.TestCase):
    """
    Tests the core.cli_entry.upload_run_single_entry function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def tearDown(self):
        print("Cleaning up status file")
        log_file_path = path.join(path_to_module, "fake_ngs_data", "irida-uploader.log")
        if path.exists(log_file_path):
            os.remove(log_file_path)
        status_file_path = path.join(path_to_module, "fake_ngs_data", "irida_uploader_status.info")
        if path.exists(status_file_path):
            os.remove(status_file_path)

        # Clean up the logger in the case where a test fails to complete
        print("Cleaning up directory logger")
        if logger.directory_logger:
            logger.remove_directory_logger()

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_valid_all_functions_called(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        :return:
        """
        my_directory = path.join(path_to_module, "fake_ngs_data")

        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            directory = my_directory
            status = DirectoryStatus.NEW

            @staticmethod
            def status_equals(status):
                return status == DirectoryStatus.NEW

        # add mock data to the function calls that are essential
        stub_directory_status = StubDirectoryStatus()
        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]
        mock_progress.write_directory_status.side_effect = [None, None]

        cli_entry.upload_run_single_entry(my_directory, force_upload=False)

        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, run_id=None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with("Fake Sequencing Run")

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_log_file_created(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        Mocks aren't used, the function fails almost right away,
            but we don't care because we are only ensuring the log file is created
        :return:
        """

        directory = path.join(path_to_module, "fake_ngs_data")
        directory_status = DirectoryStatus(directory)
        log_file = path.join(directory, "irida-uploader.log")
        # Check that log file does not exist before starting
        self.assertFalse(path.exists(log_file))

        cli_entry._validate_and_upload(directory_status)

        # Make sure log file is created
        self.assertTrue(path.exists(log_file))

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_invalid_at_api_sequencing_run(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a invalid directory in given
        Invalidity comes from api module,
        When parsing, it should be valid
        :return:
        """

        directory = path.join(path_to_module, "fake_ngs_data")

        class StubValidationResult:
            @staticmethod
            def is_valid():
                return False

            @staticmethod
            def error_count():
                return 0

            @property
            def error_list(self):
                return []

        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.NEW

            @staticmethod
            def status_equals(status):
                return status == DirectoryStatus.NEW

        # add mock data to the function calls that are essential
        stub_directory_status = StubDirectoryStatus()
        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        cli_entry.upload_run_single_entry(directory)

        # Make sure the validation is tried
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # make sure the upload is NOT done, as validation is invalid
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_invalid_before_parsing_sequencing_run(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a invalid directory in given
        Invalidity comes from checking if the run is valid, but before parsing
        :return:
        """
        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.INVALID
            message = ""

            @staticmethod
            def status_equals(status):
                return status == DirectoryStatus.INVALID

        # add mock data to the function calls that are essential
        mock_parsing_handler.get_run_status.side_effect = [StubDirectoryStatus]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [None]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.upload_run_single_entry(directory)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure the later functions are not called
        mock_parsing_handler.parse_and_validate.assert_not_called()
        mock_api_handler.initialize_api_from_config.assert_not_called()
        mock_api_handler.prepare_and_validate_for_upload.assert_not_called()
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_invalid_at_parsing_sequencing_run(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a invalid directory in given
        Invalidity comes from parsing module
        :return:
        """
        directory = path.join(path_to_module, "fake_ngs_data")

        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.NEW

            @staticmethod
            def status_equals(status):
                return status == DirectoryStatus.NEW

        # add mock data to the function calls that are essential
        mock_parsing_handler.get_run_status.side_effect = [StubDirectoryStatus]
        mock_parsing_handler.parse_and_validate.side_effect = [DirectoryError("", "")]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [None]
        mock_api_handler.upload_sequencing_run.side_effect = [None]


        cli_entry.upload_run_single_entry(directory)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure the error throwing function is called
        mock_parsing_handler.parse_and_validate.assert_called_with(directory)
        # Make sure the later functions are not called
        mock_api_handler.initialize_api_from_config.assert_not_called()
        mock_api_handler.prepare_and_validate_for_upload.assert_not_called()
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_valid_force_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        In this case, we are forcing an upload, so no run is new check should happen
        :return:
        """

        directory = path.join(path_to_module, "fake_ngs_data")

        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.NEW

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.status_equals = MagicMock(return_value=False)
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        # mock_parsing_handler.run_is_new.side_effect = [None]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        cli_entry.upload_run_single_entry(directory, True)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done (Only invalid check is done)
        mock_stub_directory_status.status_equals.assert_called_once_with(DirectoryStatus.INVALID)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with("Fake Sequencing Run")

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_valid_new_status_file_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        In this case, the run is new check should happen
        :return:
        """
        directory = path.join(path_to_module, "fake_ngs_data")

        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.NEW

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.status_equals = Mock()
        mock_stub_directory_status.status_equals.side_effect = [False, True]
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        cli_entry.upload_run_single_entry(directory, False)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is done
        mock_stub_directory_status.status_equals.assert_called_with(DirectoryStatus.NEW)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with("Fake Sequencing Run")

    @patch("core.cli_entry.progress")
    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_valid_already_uploaded(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        In this case, the run is new check should occur, and the run should not be uploaded, and not be parsed
        :return:
        """

        directory = path.join(path_to_module, "fake_ngs_data")

        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        # add mock data to the function calls that are essential
        class StubDirectoryStatus:
            directory = path.join(path_to_module, "fake_ngs_data")
            status = DirectoryStatus.COMPLETE

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.status_equals = Mock()
        mock_stub_directory_status.status_equals.side_effect = [False, False]
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        cli_entry.upload_run_single_entry(directory, False)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done
        mock_stub_directory_status.status_equals.assert_called_with(DirectoryStatus.NEW)
        # Make sure parsing and validation is NOT done
        mock_parsing_handler.parse_and_validate.assert_not_called()
        # make sure the upload is NOT done, as validation is invalid
        mock_api_handler.upload_sequencing_run.assert_not_called()
