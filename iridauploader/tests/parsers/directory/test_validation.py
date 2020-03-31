import unittest
from unittest.mock import patch
from csv import reader
from io import StringIO

from iridauploader.parsers.directory.validation import validate_sample_sheet
from iridauploader.parsers.exceptions import SampleSheetError


class TestValidation(unittest.TestCase):
    """
    Tests valid and invalid sample sheets
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_validate_sample_sheet_no_data_header(self, mock_csv_reader):
        """
        Given a sample sheet with no header, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        field_values = (
            "Sample_Name,Project_ID,File_Forward,File_Reverse\n"
            "my-sample-1, 72,file_1.fastq.gz,file_2.fastq.gz\n"
        )

        file_contents_str = (
            "{field_values}"
        ).format(field_values=field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be an invalid sample sheet
        self.assertFalse(res.is_valid())
        # Only should have 2 error
        self.assertEqual(len(res.error_list), 2)
        # Error type should be SampleSheetError
        self.assertEqual(type(res.error_list[0]), SampleSheetError)
        self.assertEqual(type(res.error_list[1]), SampleSheetError)

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_validate_sample_sheet_no_data(self, mock_csv_reader):
        """
        Given a sample sheet with no data, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        file_contents_str = "[Data]\n"

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be an invalid sample sheet
        self.assertFalse(res.is_valid())
        # Only should have 1 error
        self.assertEqual(len(res.error_list), 1)
        # Error type should be SampleSheetError
        self.assertEqual(type(res.error_list[0]), SampleSheetError)

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_validate_sample_sheet_valid(self, mock_csv_reader):
        """
        Given a valid sample sheet, make sure the response shows as valid
        :param mock_csv_reader:
        :return:
        """
        field_values = (
            "[Data]\n"
            "Sample_Name,Project_ID,File_Forward,File_Reverse\n"
            "my-sample-1,72,file_1.fastq.gz,file_2.fastq.gz\n"
        )

        file_contents_str = (
            "{field_values}"
        ).format(field_values=field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be a valid sample sheet
        self.assertTrue(res.is_valid())
