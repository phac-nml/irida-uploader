import unittest
from unittest.mock import patch
from os import path

from core import cli_entry

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestValidateAndUploadSingleEntry(unittest.TestCase):

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_valid_all_functions_called(self, mock_parsing_handler, mock_api_handler):
        """
        Makes sure that all functions are called when a valid directory in given
        :return:
        """
        class StubValidationResult:
            @staticmethod
            def is_valid():
                return True

        # add mock data to the function calls that are essential
        mock_parsing_handler.parse_and_validate.side_effect = ["Fake Sequencing Run"]
        mock_api_handler.initialize_api_from_config.side_effect = [None]
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [StubValidationResult]
        mock_api_handler.upload_sequencing_run.side_effect = [None]

        directory = path.join(path_to_module, "fake_ngs_data")

        cli_entry.validate_and_upload_single_entry(directory)

        # Make sure parsing and validation is done
        mock_parsing_handler.parse_and_validate.assert_called_with(directory)
        # api must be initialized
        mock_api_handler.initialize_api_from_config.assert_called()
        # api must prep for upload
        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("Fake Sequencing Run")
        # api should try to upload
        mock_api_handler.upload_sequencing_run.assert_called_with("Fake Sequencing Run")

    @patch("core.cli_entry.api_handler")
    @patch("core.cli_entry.parsing_handler")
    def test_invalid_sequencing_run(self, mock_parsing_handler, mock_api_handler):
        """
        Makes sure that all functions are called when a valid directory in given
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

        # add mock data to the function calls that are essential
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
