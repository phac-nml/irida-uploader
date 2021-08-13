import unittest
from unittest.mock import patch, call
from os import path
import os

from iridauploader.api import MODE_DEFAULT
from iridauploader.core import upload, logger, exit_return
from iridauploader.config import config
from iridauploader.model import DirectoryStatus

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestUploadRunSingleEntry(unittest.TestCase):
    """
    Tests the core.upload.upload_run_single_entry function
    """

    # Reusable stubs
    class StubValidationResult:
        _valid = True
        _error_count = 0
        _error_list = []

        def is_valid(self):
            return self._valid

        def error_count(self):
            return self._error_count

        @property
        def error_list(self):
            return self._error_list

    class StubDirectoryStatus:
        directory = path.join(path_to_module, "fake_ngs_data")
        _status = DirectoryStatus.NEW
        _message = ""

        def status_equals(self, status):
            return status == self._status

        @property
        def message(self):
            return self._message

        @property
        def status(self):
            return self._status
        #
        # @status.setter
        # def status(self, status):
        #     self._status = status

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

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_invalid_directory_status(self, mock_parsing_handler, mock_api_handler,
                                      mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits when directory status is invalid
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.INVALID

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_completed_directory_status(self, mock_parsing_handler, mock_api_handler,
                                        mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits when directory status is complete
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.COMPLETE

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_error_directory_status(self, mock_parsing_handler, mock_api_handler,
                                    mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits when directory status is error
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.ERROR

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_partial_directory_status(self, mock_parsing_handler, mock_api_handler,
                                      mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits when directory status is partial
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.PARTIAL

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_not_called()

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_completed_force_directory_status(self, mock_parsing_handler, mock_api_handler,
                                              mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function with force when directory status is complete
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.COMPLETE

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory, force_upload=True)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_partial_force_directory_status(self, mock_parsing_handler, mock_api_handler,
                                            mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function continues with force when directory status is partial
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.PARTIAL

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory, force_upload=True)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_partial_continue_directory_status(self, mock_parsing_handler, mock_api_handler,
                                               mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function continues with force when directory status is partial
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.PARTIAL

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(
            stub_directory_status.directory, force_upload=False, continue_upload=True)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", True)

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_error_force_directory_status(self, mock_parsing_handler, mock_api_handler,
                                          mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function continues with force when directory status is error
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.ERROR

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory, force_upload=True)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_delayed_force_directory_status(self, mock_parsing_handler, mock_api_handler,
                                            mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function continues with force when directory status is delayed
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.DELAYED

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory, force_upload=True)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_new_directory_status(self, mock_parsing_handler, mock_api_handler,
                                  mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function continues when directory status is new
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.NEW

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload occurs
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.progress.upload_status._set_run_delayed")
    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_new_with_delay_config_directory_status(self, mock_parsing_handler, mock_api_handler,
                                                    mock_validate_and_upload, mock_upload_helpers,
                                                    mock_set_run_delayed):
        """
        Checks that function exits with success when directory status is new and there is a delay set
        :return:
        """
        # set a delay
        config.set_config_options(delay=1)

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.NEW

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_set_run_delayed.side_effect = [None]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_SUCCESS)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)
        mock_set_run_delayed.assert_called_with(stub_directory_status)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()

    # @patch("iridauploader.progress.upload_status._delayed_time_has_passed")
    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_delay_time_has_passed_directory_status(self, mock_parsing_handler, mock_api_handler,
                                                    mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits with success when directory status is delayed and the delay has passed
        :return:
        """
        # set a delay for 0 as time has passed
        config.set_config_options(delay=0)

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.DELAYED

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_api_handler.get_default_upload_mode.side_effect = ["mock_mode"]
        mock_validate_and_upload.side_effect = ["mock_result"]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result, "mock_result")

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)

        # ensure upload occurs
        mock_validate_and_upload.assert_called_with(stub_directory_status, "mock_mode", False)

    @patch("iridauploader.progress.upload_status._delayed_time_has_passed")
    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_delay_not_passed_directory_status(self, mock_parsing_handler, mock_api_handler,
                                               mock_validate_and_upload, mock_upload_helpers,
                                               mock_delayed_time_has_passed):
        """
        Checks that function exits with success when directory status is delayed and there is still delay time
        :return:
        """
        # set a delay
        config.set_config_options(delay=1)

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.DELAYED

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_delayed_time_has_passed.side_effect = [False]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [False]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_SUCCESS)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)
        mock_delayed_time_has_passed.assert_called_with(stub_directory_status, 1)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()

    @patch("iridauploader.core.upload.upload_helpers")
    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.api_handler")
    @patch("iridauploader.core.upload.parsing_handler")
    def test_directory_not_writable_no_readonly_status(self, mock_parsing_handler, mock_api_handler,
                                                       mock_validate_and_upload, mock_upload_helpers):
        """
        Checks that function exits with success when directory status is delayed and there is still delay time
        :return:
        """

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status._status = DirectoryStatus.DELAYED

        mock_parsing_handler.get_run_status.side_effect = [stub_directory_status]
        mock_upload_helpers.directory_has_readonly_conflict.side_effect = [True]

        result = upload.upload_run_single_entry(stub_directory_status.directory)

        # verify result
        self.assertEqual(result.exit_code, exit_return.EXIT_CODE_ERROR)

        # verify calls occurred
        mock_parsing_handler.get_run_status.assert_called_with(stub_directory_status.directory)
        mock_upload_helpers.directory_has_readonly_conflict.assert_called_with(stub_directory_status.directory)

        # ensure upload did not occur
        mock_validate_and_upload.assert_not_called()


class TestBatchUploadSingleEntry(unittest.TestCase):
    """
    Tests the core.upload.batch_upload_single_entry function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        config._init_config_parser()

    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.parsing_handler")
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
        upload.batch_upload_single_entry("fake_directory", upload_mode=MODE_DEFAULT)

        # validate calls only happen once
        mock_validate_and_upload.assert_called_once_with(stub_directory_status_valid, MODE_DEFAULT, False)

    @patch("iridauploader.core.upload._validate_and_upload")
    @patch("iridauploader.core.upload.parsing_handler")
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
        upload.batch_upload_single_entry("fake_directory", force_upload=True)

        # assert calls are what we expect
        self.assertEqual(mock_validate_and_upload.call_count, 3, "Expected 3 calls to mock_validate_and_upload")
        expected_call_args = [
            call(stub_directory_status_valid, MODE_DEFAULT, False),
            call(stub_directory_status_complete, MODE_DEFAULT, False),
            call(stub_directory_status_partial, MODE_DEFAULT, False)
        ]
        self.assertEqual(mock_validate_and_upload.call_args_list, expected_call_args, "Call args do not match expected")
