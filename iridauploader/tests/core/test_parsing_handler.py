import unittest
from unittest.mock import patch
from os import path

import iridauploader.parsers as parsers
from iridauploader.core import parsing_handler

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestGetParserFromConfig(unittest.TestCase):
    """
    When a new parser is added to the uploader, a test that it can be gotten should be added here
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.parsing_handler.config.read_config_option")
    def test_get_miseq_parser(self, mock_read_config_option):
        # force the handler to grab 'miseq' when it tries to call config
        mock_read_config_option.side_effect = ["miseq"]

        res = parsing_handler.get_parser_from_config()
        # verify we grabbed the right parser
        self.assertEqual(type(res), parsers.parsers.miseq.Parser)

    @patch("iridauploader.core.parsing_handler.config.read_config_option")
    def test_get_directory_parser(self, mock_read_config_option):
        # force the handler to grab 'directory' when it tries to call config
        mock_read_config_option.side_effect = ["directory"]

        res = parsing_handler.get_parser_from_config()
        # verify we grabbed the right parser
        self.assertEqual(type(res), parsers.parsers.directory.Parser)


class TestParseAndValidate(unittest.TestCase):
    """
    Tests the core.parsing_handler.parse_and_validate function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.parsing_handler.model_validator.validate_sequencing_run")
    @patch("iridauploader.core.parsing_handler.get_parser_from_config")
    def test_all_functions_called(self, mock_get_parser, mock_validate):
        """
        Makes sure that all relevant functions are called so that it will parse and validate fully
        :return:
        """
        # add mock data (as strings) to the function calls that are essential
        mock_parser_instance = unittest.mock.MagicMock()
        mock_parser_instance.get_sample_sheet.side_effect = ["mock_sample_sheet"]
        mock_parser_instance.get_sequencing_run.side_effect = ["mock_sequencing_run"]

        mock_get_parser.side_effect = [mock_parser_instance]

        mock_validation_result = unittest.mock.MagicMock()
        mock_validation_result.is_valid.side_effect = [True]

        mock_validate.side_effect = [mock_validation_result]

        res = parsing_handler.parse_and_validate("mock_directory")

        # verify that the functions were called the mock data we set up
        mock_parser_instance.get_sample_sheet.assert_called_once_with("mock_directory")
        mock_parser_instance.get_sequencing_run.assert_called_once_with("mock_sample_sheet")
        mock_validate.assert_called_once_with("mock_sequencing_run")
        self.assertEqual(res, "mock_sequencing_run")

    @patch("iridauploader.core.parsing_handler.model_validator.validate_sequencing_run")
    @patch("iridauploader.core.parsing_handler.get_parser_from_config")
    def test_invalid_sequencing_run(self, mock_get_parser, mock_validate):
        """
        Check that an exception is thrown when a given SequencingRun is given
        :return:
        """
        # add mock data (as strings) to the function calls that are essential
        mock_parser_instance = unittest.mock.MagicMock()
        mock_parser_instance.get_sample_sheet.side_effect = ["mock_sample_sheet"]
        mock_parser_instance.get_sequencing_run.side_effect = ["mock_sequencing_run"]

        mock_get_parser.side_effect = [mock_parser_instance]

        mock_validation_result = unittest.mock.MagicMock()
        mock_validation_result.is_valid.side_effect = [False]

        mock_validate.side_effect = [mock_validation_result]

        # make sure the invalid sequencing run raises a ValidationError
        with self.assertRaises(parsers.exceptions.ValidationError):
            parsing_handler.parse_and_validate("mock_directory")
