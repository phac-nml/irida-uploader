import unittest
from unittest.mock import patch
from csv import reader
from io import StringIO

from iridauploader.parsers.miseq.validation import validate_sample_sheet
from iridauploader.parsers.exceptions import SampleSheetError


class TestValidation(unittest.TestCase):
    """
    Tests valid and invalid sample sheets
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_validate_sample_sheet_no_header(self, mock_csv_reader):
        """
        Given a sample sheet with no header, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        headers = ("Sample_ID,Sample_Name,Sample_Plate,Sample_Well,"
                   "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,"
                   "Description")

        field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT,203\n"
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        reads = (
            "251\n"
            "251\n"
        )

        file_contents_str = (
            "[Reads]\n"
            "{reads}\n"
            "[Data]\n"
            "{headers}\n"
            "{field_values}"
        ).format(headers=headers, reads=reads, field_values=field_values)

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
    def test_validate_sample_sheet_no_data(self, mock_csv_reader):
        """
        Given a sample sheet with no data, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT,203\n"
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
            "IEMFileVersion, 4\n"
            "Investigator Name, Test Name\n"
            "Experiment Name, Some_Test_Data\n"
            "Date, 2015-05-14\n"
            "Workflow, GenerateFASTQ\n"
            "Application, FASTQ Only\n"
            "Assay, ASDF\n"
            "Description, 12-34\n"
            "Chemistry, Yes\n"
        )

        reads = (
            "251\n"
            "251\n"
        )

        file_contents_str = (
            "[Header]\n"
            "{field_values}\n"
            "[Reads]\n"
            "{reads}"
        ).format(field_values=field_values, reads=reads)

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
    def test_validate_sample_sheet_missing_data_header(self, mock_csv_reader):
        """
        Given a sample sheet with no data header, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        h_field_values = (
            "IEMFileVersion, 4\n"
            "Investigator Name, Test Name\n"
            "Experiment Name, Some_Test_Data\n"
            "Date, 2015-05-14\n"
            "Workflow, GenerateFASTQ\n"
            "Application, FASTQ Only\n"
            "Assay, ASDF\n"
            "Description, 12-34\n"
            "Chemistry, Yes\n"
        )

        reads = (
            "251\n"
            "251\n"
        )

        d_headers = ("Sample_Name,Sample_Plate,Sample_Well,"
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,"
                     "Description")

        d_field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT,203\n"
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        file_contents_str = (
            "[Header]\n"
            "{h_field_values}\n"
            "[Reads]\n"
            "{reads}\n"
            "[Data]\n"
            "{d_headers}\n"
            "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

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
        Given a valid sample sheet, test that everything shows as valid
        :param mock_csv_reader:
        :return:
        """
        h_field_values = (
            "IEMFileVersion, 4\n"
            "Investigator Name, Test Name\n"
            "Experiment Name, Some_Test_Data\n"
            "Date, 2015-05-14\n"
            "Workflow, GenerateFASTQ\n"
            "Application, FASTQ Only\n"
            "Assay, ASDF\n"
            "Description, 12-34\n"
            "Chemistry, Yes\n"
        )

        reads = (
            "251\n"
            "251\n"
        )

        d_headers = ("Sample_ID,Sample_Name,Sample_Plate,Sample_Well,"
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,"
                     "Description")

        d_field_values = (
            "15-0318,,2015-08-05-SE,A01,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
            "15-0455,,2015-08-05-SE,B01,N701,TAAGGCGA,S503,TATCCTCT,203\n"
            "15-0462,,2015-08-05-SE,C01,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        file_contents_str = (
            "[Header]\n"
            "{h_field_values}\n"
            "[Reads]\n"
            "{reads}\n"
            "[Data]\n"
            "{d_headers}\n"
            "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be a valid sample sheet
        self.assertTrue(res.is_valid())
