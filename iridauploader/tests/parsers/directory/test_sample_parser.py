import unittest
from os import path
from unittest.mock import patch

import iridauploader.parsers.directory.sample_parser as sample_parser
from iridauploader.parsers.exceptions import SampleSheetError
import iridauploader.model as model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestVerifySampleSheetFileNamesInFileList(unittest.TestCase):
    """
    test file existence verification function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid(self):
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_simple.csv")

        run_data_directory_file_list = ["file_1.fastq.gz", "file_2.fastq.gz"]

        sample_parser.verify_sample_sheet_file_names_in_file_list(sheet_file, run_data_directory_file_list)

    def test_file_names_do_not_match_paired_end(self):
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_simple.csv")

        run_data_directory_file_list = ["file_1.fastq.gz", "file_a.fastq.gz"]

        with self.assertRaises(SampleSheetError):
            sample_parser.verify_sample_sheet_file_names_in_file_list(sheet_file, run_data_directory_file_list)

    def test_file_names_do_not_match_single_end(self):
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "no_reverse.csv")

        run_data_directory_file_list = ["file_a.fastq.gz"]

        with self.assertRaises(SampleSheetError):
            sample_parser.verify_sample_sheet_file_names_in_file_list(sheet_file, run_data_directory_file_list)


class TestBuildSampleListFromSampleSheetWithAbsPath(unittest.TestCase):
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

        res = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(sheet_file)

        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], "file_1.fastq.gz")
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], "file_2.fastq.gz")
        self.assertEqual(res[0].sequence_file.file_list[0], file_path_1)
        self.assertEqual(res[0].sequence_file.file_list[1], file_path_2)

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

        res = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(sheet_file)

        mock_parse_samples.assert_called_with(sheet_file)
        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], path.abspath(file_path_1))
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], path.abspath(file_path_2))
        self.assertEqual(res[0].sequence_file.file_list[0], file_path_1)
        self.assertEqual(res[0].sequence_file.file_list[1], file_path_2)

    def test_no_forward_read(self):
        """
        No Valid files were found with names given in sample sheet
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_forward.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(file_path)

    def test_no_reverse_read(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_reverse.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(file_path)


class TestBuildSampleListFromSampleSheetNoVerify(unittest.TestCase):
    """
    test parsing the list of samples from a sample sheet
    These samplelists are built without verification that the files exist
    But we still check the positive test cases
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

        res = sample_parser.build_sample_list_from_sample_sheet_no_verify(sheet_file)

        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0].sample_name, "my-sample-1")
        self.assertEqual(res[0].get_uploadable_dict()["sample_project"], "75")
        self.assertEqual(res[0].get_uploadable_dict()["File_Forward"], file_name_1)
        self.assertEqual(res[0].get_uploadable_dict()["File_Reverse"], file_name_2)
        self.assertEqual(res[0].sequence_file.file_list[0], file_name_1)
        self.assertEqual(res[0].sequence_file.file_list[1], file_name_2)


class TestOnlySingleOrPairedInSampleList(unittest.TestCase):
    """
    test boolean of if there is only one of paired or single end files in a list of samples
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_mixed_paired_and_single_reads(self):
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_mixed.csv")

        sample_list = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(file_path)
        res = sample_parser.only_single_or_paired_in_sample_list(sample_list)

        self.assertFalse(res)

    def test_only_single_end_reads(self):
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "no_reverse.csv")

        sample_list = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(file_path)
        res = sample_parser.only_single_or_paired_in_sample_list(sample_list)

        self.assertTrue(res)

    def test_only_paired_end_reads(self):
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "SampleList.csv")

        sample_list = sample_parser.build_sample_list_from_sample_sheet_with_abs_path(file_path)
        res = sample_parser.only_single_or_paired_in_sample_list(sample_list)

        self.assertTrue(res)


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
