import unittest
from unittest.mock import patch, MagicMock, Mock, call
from os import path
import os

from iridauploader.api import UPLOAD_MODES, MODE_DEFAULT, MODE_FAST5, MODE_ASSEMBLIES
from iridauploader.core import cli_entry, logger, exit_return
from iridauploader.config import config
from iridauploader.model import DirectoryStatus
from iridauploader.parsers.exceptions import DirectoryError
from iridauploader.api.exceptions import FileError, IridaResourceError, IridaConnectionError

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestUploadRunSingleEntry(unittest.TestCase):
    """
    Tests the core.cli_entry.upload_run_single_entry function
    Indirectly does testing on core.cli_entry._validate_and_upload function too
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        # config.setup()
        config._init_config_parser()

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

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        cli_entry.upload_run_single_entry(my_directory, force_upload=False)

        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should check upload modes
        mock_api_handler.get_default_upload_mode.assert_called_with()
        mock_api_handler.get_upload_modes.assert_called_with()
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_assemblies_all_functions_called(self, mock_parsing_handler, mock_api_handler, mock_progress):
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        cli_entry.upload_run_single_entry(my_directory, force_upload=True, upload_mode=MODE_ASSEMBLIES)

        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_ASSEMBLIES)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_fast5_all_functions_called(self, mock_parsing_handler, mock_api_handler, mock_progress):
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        cli_entry.upload_run_single_entry(my_directory, force_upload=True, upload_mode=MODE_FAST5)

        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_FAST5)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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

        cli_entry._validate_and_upload(directory_status, False)

        # Make sure log file is created
        self.assertTrue(path.exists(log_file))

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

        cli_entry.upload_run_single_entry(directory)

        # Make sure the validation is tried
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # make sure the upload is NOT done, as validation is invalid
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.upload_run_single_entry(directory)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure the later functions are not called
        mock_parsing_handler.parse_and_validate.assert_not_called()
        mock_api_handler.initialize_api_from_config.assert_not_called()
        mock_api_handler.prepare_and_validate_for_upload.assert_not_called()
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

        cli_entry.upload_run_single_entry(directory)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure the error throwing function is called
        mock_parsing_handler.parse_and_validate.assert_called_with(directory)
        # Make sure the later functions are not called
        mock_api_handler.initialize_api_from_config.assert_not_called()
        mock_api_handler.prepare_and_validate_for_upload.assert_not_called()
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

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
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

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
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
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
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]

        cli_entry.upload_run_single_entry(directory, False)

        # Check that run status was found
        mock_parsing_handler.get_run_status.assert_called_with(directory)
        # Make sure run is new check is not done
        mock_stub_directory_status.status_equals.assert_called_with(DirectoryStatus.NEW)
        # Make sure parsing and validation is NOT done
        mock_parsing_handler.parse_and_validate.assert_not_called()
        # make sure the upload is NOT done, as validation is invalid
        mock_api_handler.upload_sequencing_run.assert_not_called()

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_connection_error_during_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure no crash occurs and program exits with error when IridaConnectionError occurs during upload
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
        mock_api_handler.upload_sequencing_run.side_effect = [IridaConnectionError("")]
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        result = cli_entry.upload_run_single_entry(my_directory, force_upload=False)

        # Check that the run failed to upload
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)
        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_resourse_error_during_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure no crash occurs and program exits with error when IridaResourceError occurs during upload
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
        mock_api_handler.upload_sequencing_run.side_effect = [IridaResourceError("")]
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        result = cli_entry.upload_run_single_entry(my_directory, force_upload=False)

        # Check that the run failed to upload
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)
        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry.progress")
    @patch("iridauploader.core.cli_entry.api_handler")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_file_error_during_upload(self, mock_parsing_handler, mock_api_handler, mock_progress):
        """
        Makes sure no crash occurs and program exits with error when FileError occurs during upload
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
        mock_api_handler.upload_sequencing_run.side_effect = [FileError("")]
        mock_api_handler.get_default_upload_mode.side_effect = [MODE_DEFAULT]
        mock_api_handler.get_upload_modes.side_effect = [UPLOAD_MODES]
        mock_progress.write_directory_status.side_effect = [None, None]

        result = cli_entry.upload_run_single_entry(my_directory, force_upload=False)

        # Check that the run failed to upload
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)
        # Make sure directory status is init
        mock_progress.write_directory_status.assert_called_with(stub_directory_status, None)
        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(my_directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called_with()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with(sequencing_run="Fake Sequencing Run",
                                                                  upload_mode=MODE_DEFAULT)


class TestBatchUploadSingleEntry(unittest.TestCase):
    """
    Tests the core.cli_entry.batch_upload_single_entry function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.cli_entry._validate_and_upload")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid(self, mock_parsing_handler, mock_validate_and_upload):
        """
        Makes sure that _validate_and_upload is only called on a new run
        :return:
        """
        class StubDirectoryStatus:
            def __init__(self, directory, status):
                self.directory = directory
                self.status = status
                self.message = None

            def status_equals(self, other_status):
                return self.status == other_status

        # add mock data to the function calls that are essential
        stub_directory_status_valid = StubDirectoryStatus("valid", DirectoryStatus.NEW)
        stub_directory_status_invalid = StubDirectoryStatus("invalid", DirectoryStatus.INVALID)
        stub_directory_status_complete = StubDirectoryStatus("complete", DirectoryStatus.COMPLETE)
        stub_directory_status_partial = StubDirectoryStatus("partial", DirectoryStatus.PARTIAL)

        mock_parsing_handler.get_run_status_list.side_effect = [
            [stub_directory_status_valid,
             stub_directory_status_invalid,
             stub_directory_status_complete,
             stub_directory_status_partial]
        ]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]

        # start
        cli_entry.batch_upload_single_entry("fake_directory", upload_mode=MODE_DEFAULT)

        # validate calls only happen once
        mock_validate_and_upload.assert_called_once_with(stub_directory_status_valid, MODE_DEFAULT)

    @patch("iridauploader.core.cli_entry._validate_and_upload")
    @patch("iridauploader.core.cli_entry.parsing_handler")
    def test_valid_force(self, mock_parsing_handler, mock_validate_and_upload):
        """
        Makes sure that _validate_and_upload is called on all runs except invalid
        :return:
        """
        class StubDirectoryStatus:
            def __init__(self, directory, status):
                self.directory = directory
                self.status = status
                self.message = None

            def status_equals(self, other_status):
                return self.status == other_status

        # add mock data to the function calls that are essential
        stub_directory_status_valid = StubDirectoryStatus("valid", DirectoryStatus.NEW)
        stub_directory_status_invalid = StubDirectoryStatus("invalid", DirectoryStatus.INVALID)
        stub_directory_status_complete = StubDirectoryStatus("complete", DirectoryStatus.COMPLETE)
        stub_directory_status_partial = StubDirectoryStatus("partial", DirectoryStatus.PARTIAL)

        mock_parsing_handler.get_run_status_list.side_effect = [
            [stub_directory_status_valid,
             stub_directory_status_invalid,
             stub_directory_status_complete,
             stub_directory_status_partial]
        ]
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]

        # start
        cli_entry.batch_upload_single_entry("fake_directory", force_upload=True)

        # assert calls are what we expect
        self.assertEqual(mock_validate_and_upload.call_count, 3, "Expected 3 calls to mock_validate_and_upload")
        expected_call_args = [
            call(stub_directory_status_valid, MODE_DEFAULT),
            call(stub_directory_status_complete, MODE_DEFAULT),
            call(stub_directory_status_partial, MODE_DEFAULT)
        ]
        self.assertEqual(mock_validate_and_upload.call_args_list, expected_call_args, "Call args do not match expected")
