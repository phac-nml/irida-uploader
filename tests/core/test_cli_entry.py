import unittest
from unittest.mock import patch, MagicMock
from os import path
import os

from core import cli_entry, logger

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestValidateAndUploadSingleEntry(unittest.TestCase):
    """
    Tests the core.cli_entry.validate_and_upload_single_entry function
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
        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            @staticmethod
            def is_invalid():
                return False

            @staticmethod
            def is_new():
                return True

        # add mock data to the function calls that are essential
        mock_parsing_handler.get_run_status.side_effect = [StubDirectoryStatus]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]
        mock_progress.write_directory_status.side_effect = [None, None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory, force_upload=False)

        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(StubDirectoryStatus, run_id=None)
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
    def test_log_file_created(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        Mocks aren't used, the function fails almost right away,
            but we don't care because we are only ensuring the log file is created
        :return:
        """

        directory = path.join(path_to_module, "fake_ngs_data")
        log_file = path.join(directory, "irida-uploader.log")

        # Check that log file does not exist before starting
        self.assertFalse(path.exists(log_file))

        cli_entry.validate_and_upload_single_entry(directory)

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
            @staticmethod
            def is_invalid():
                return False

            @staticmethod
            def is_new():
                return True

        # add mock data to the function calls that are essential
        mock_parsing_handler.get_run_status.side_effect = [StubDirectoryStatus]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory)

        # Make sure the validation is tried
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # make sure the upload is NOT done, as validation is invalid
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
        class StubDirectoryStatus:
            @staticmethod
            def is_invalid():
                return True

            @staticmethod
            def directory():
                return None

            @staticmethod
            def message():
                return None

        # add mock data to the function calls that are essential
        mock_parsing_handler.get_run_status.side_effect = [StubDirectoryStatus]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [None]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory)

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
    def test_valid_force_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure that all functions are called when a valid directory in given
        In this case, we are forcing an upload, so no run is new check should happen
        :return:
        """
        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            @staticmethod
            def is_invalid():
                return False

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.is_new = MagicMock(return_value=True)
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_parsing_handler.run_is_new.side_effect = [None]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory, True)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done
        mock_stub_directory_status.is_new.assert_not_called()
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
        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        class StubDirectoryStatus:
            @staticmethod
            def is_invalid():
                return False

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.is_new = MagicMock(return_value=True)
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory, False)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done
        mock_stub_directory_status.is_new.assert_called_with()
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
        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        # add mock data to the function calls that are essential
        class StubDirectoryStatus:
            @staticmethod
            def is_invalid():
                return False

        # add mock data to the function calls that are essential
        mock_stub_directory_status = StubDirectoryStatus()
        mock_stub_directory_status.is_new = MagicMock(return_value=False)
        mock_parsing_handler.get_run_status.side_effect = [mock_stub_directory_status]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory, False)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done
        mock_stub_directory_status.is_new.assert_called_with()
        # Make sure parsing and validation is NOT done
        mock_parsing_handler.parse_and_validate.assert_not_called()
        # make sure the upload is NOT done, as validation is invalid
        mock_api_handler.upload_sequencing_run.assert_not_called()
