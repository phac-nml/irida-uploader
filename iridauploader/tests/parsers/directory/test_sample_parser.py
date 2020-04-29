import unittest
from collections import OrderedDict
from os import path
from unittest.mock import patch

import iridauploader.parsers as parsers
import iridauploader.parsers.directory.sample_parser as sample_parser
from iridauploader.parsers.exceptions import SampleSheetError
import iridauploader.model as model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestParseSampleList(unittest.TestCase):
    """
    test parsing the list of samples from a sample sheet
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid(self):
        """
        Given a valid sample sheet, parse correctly
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_simple.csv")

        file_path_1 = path.join(path_to_module,
                                "fake_dir_data", "file_1.fastq.gz")
        file_path_2 = path.join(path_to_module,
                                "fake_dir_data", "file_2.fastq.gz")

        run_data_directory_file_list = ["file_1.fastq.gz", "file_2.fastq.gz"]
        res = sample_parser.parse_sample_list(sheet_file, run_data_directory_file_list)

        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], "file_1.fastq.gz")
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], "file_2.fastq.gz")

    @patch("iridauploader.parsers.directory.sample_parser._parse_samples")
    def test_valid_full_file_path(self, mock_parse_samples):
        """
        Given a valid sample sheet with full file paths, parse correctly
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_simple.csv")

        file_path_1 = path.join(path_to_module,
                                "fake_dir_data", "file_1.fastq.gz")
        file_path_2 = path.join(path_to_module,
                                "fake_dir_data", "file_2.fastq.gz")

        sample_list = [
            model.Sample(
                sample_name='my-sample-1',
                description="",
                sample_number=0,
                samp_dict={
                    ('sample_project', '75'),
                    ('File_Forward', path.abspath(file_path_1)),
                    ('File_Reverse', path.abspath(file_path_2))
                }
            )
        ]

        mock_parse_samples.return_value = sample_list

        run_data_directory_file_list = ["file_1.fastq.gz", "file_2.fastq.gz"]
        res = sample_parser.parse_sample_list(sheet_file, run_data_directory_file_list)

        mock_parse_samples.assert_called_with(sheet_file)
        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], path.abspath(file_path_1))
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], path.abspath(file_path_2))

    def test_no_forward_read(self):
        """
        No Valid files were found with names given in sample sheet
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_forward.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser.parse_sample_list(file_path, directory)

    def test_no_reverse_read(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_reverse.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser.parse_sample_list(file_path, directory)

    def test_mixed_paired_and_single_reads(self):
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_mixed.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser.parse_sample_list(file_path, directory)


class TestParseSamples(unittest.TestCase):
    """
    Test validity or invalidity of parsed samples
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid(self):
        """
        Given a valid sample sheet, parse correctly
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_simple.csv")

        file_name_1 = "file_1.fastq.gz"
        file_name_2 = "file_2.fastq.gz"

        res = sample_parser._parse_samples(sheet_file)

        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], file_name_1)
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], file_name_2)

    def test_no_forward_read(self):
        """
        No Valid files were found with names given in sample sheet
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "no_forward.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser._parse_samples(file_path)

    def test_no_reverse_read(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "no_reverse.csv")

        res = sample_parser._parse_samples(file_path)
        # This should have an empty file reverse
        self.assertEqual(res[0]["File_Reverse"], "")

    def test_no_reverse_read_with_comma(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "no_reverse_with_comma.csv")

        res = sample_parser._parse_samples(file_path)
        # This should have an empty file reverse
        self.assertEqual(res[0]["File_Reverse"], "")

    def test_no_read_files_in_list(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "no_read_files.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser._parse_samples(file_path)
