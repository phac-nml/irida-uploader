import unittest
from collections import OrderedDict
from os import path
from unittest.mock import patch

import parsers.directory
import parsers.directory.sample_parser as sample_parser
from parsers.exceptions import SampleSheetError
import model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestBuildSequencingRunFromSamples(unittest.TestCase):
    """
    Test building the sequencing run from a sample sheet with a csv reader
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_build_valid(self):
        """
        When given a valid directory, ensure a valid SequencingRun is built with Projects, Samples, ect
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList.csv")

        sequencing_run = sample_parser.build_sequencing_run_from_samples(sheet_file)

        # Returns a SequencingRun
        self.assertEqual(type(sequencing_run), model.SequencingRun)
        # Includes 2 projects
        self.assertEqual(len(sequencing_run.project_list), 2)
        # is of type Project
        self.assertEqual(type(sequencing_run.project_list[0]), model.Project)
        # Project has 2 samples
        self.assertEqual(len(sequencing_run.project_list[0].sample_list), 2)
        # Other Project has 1 sample
        self.assertEqual(len(sequencing_run.project_list[1].sample_list), 1)
        # samples are of type Sample
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0]), model.Sample)
        # samples have SequenceFile
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0].sequence_file), model.SequenceFile)

    def test_build_valid_extra_line_on_sample_list(self):
        """
        Ensure a valid SequencingRun is made when extra lines are present in sample list
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList_with_space.csv")

        sequencing_run = sample_parser.build_sequencing_run_from_samples(sheet_file)

        # Returns a SequencingRun
        self.assertEqual(type(sequencing_run), model.SequencingRun)
        # Includes 2 projects
        self.assertEqual(len(sequencing_run.project_list), 2)
        # is of type Project
        self.assertEqual(type(sequencing_run.project_list[0]), model.Project)
        # Project has 2 samples
        self.assertEqual(len(sequencing_run.project_list[0].sample_list), 2)
        # Other Project has 1 sample
        self.assertEqual(len(sequencing_run.project_list[1].sample_list), 1)
        # samples are of type Sample
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0]), model.Sample)
        # samples have SequenceFile
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0].sequence_file), model.SequenceFile)

    def test_parse_samples_valid(self):
        """
        Verify samples created from parser match expected samples
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "SampleList.csv")

        sample1 = model.Sample(
            "my-sample-1",
            "",
        )

        sample2 = model.Sample(
            "my-sample-2",
            "",
        )

        sample3 = model.Sample(
            "my-sample-3",
            "",
        )

        res = sample_parser.build_sequencing_run_from_samples(sheet_file)

        self.assertEqual(res.metadata, {'layoutType': 'PAIRED_END'})
        self.assertEqual(res.project_list[0].id, "75")
        self.assertEqual(res.project_list[1].id, "76")
        self.assertEqual(res.project_list[0].sample_list[0].get_uploadable_dict(),
                         sample1.get_uploadable_dict())
        self.assertEqual(res.project_list[0].sample_list[1].get_uploadable_dict(),
                         sample2.get_uploadable_dict())
        self.assertEqual(res.project_list[1].sample_list[0].get_uploadable_dict(),
                         sample3.get_uploadable_dict())


class TestGetCsvReader(unittest.TestCase):
    """
    Test that the csv reader behaves as expected
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_get_csv_reader_valid_sheet(self):
        """
        Given a valid sample sheet, ensure the parsed sheet matches expected output
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data",
                               "test_csv_reader.csv")

        lines = sample_parser.get_csv_reader(sheet_file)
        # This is a sample of what the miseq sample sheet looks like, but it also makes a good
        # example for what we want our csv reader to be able to parse.
        correct_lines = [
            ['[Header]'],
            ['IEMFileVersion', '4'],
            ['Investigator Name', 'Some Guy'],
            ['Experiment Name', '1'],
            ['Date', '10/15/2013'],
            ['Workflow', 'GenerateFASTQ'],
            ['Application', 'FASTQ Only'],
            ['Assay', 'Nextera XT'],
            ['Description', 'Superbug'],
            ['Chemistry', 'Amplicon'],
            [],
            ['[Reads]'],
            ['251'],
            ['250'],
            [],
            ['[Settings]'],
            ['ReverseComplement', '0'],
            ['Adapter', 'AAAAGGGGAAAAGGGGAAA'],
            [],
            ['[Data]'],
            ['Sample_ID', 'Sample_Name', 'Sample_Plate', 'Sample_Well', 'I7_Index_ID', 'index', 'I5_Index_ID', 'index2',
             'Sample_Project', 'Description'],
            ['01-1111', '01-1111', '1', '01', 'N01', 'AAAAAAAA', 'S01', 'TTTTTTTT', '6', 'Super bug '],
            ['02-2222', '02-2222', '2', '02', 'N02', 'GGGGGGGG', 'S02', 'CCCCCCCC', '6', 'Scary bug '],
            ['03-3333', '03-3333', '3', '03', 'N03', 'CCCCCCCC', 'S03', 'GGGGGGGG', '6', 'Deadly bug ']
        ]

        for line, c_line in zip(lines, correct_lines):
            self.assertEqual(line, c_line)

    def test_get_csv_reader_no_sheet(self):
        """
        When no sheet is given to parser, throw error
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_dir_data")

        with self.assertRaises(SampleSheetError):
            sample_parser.get_csv_reader(sheet_file)


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

        res = sample_parser._parse_sample_list(sheet_file)

        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0]["Sample_Name"], "my-sample-1")
        self.assertEqual(res[0]["Project_ID"], "75")
        self.assertEqual(res[0]["File_Forward"], file_path_1)
        self.assertEqual(res[0]["File_Reverse"], file_path_2)

    @patch("parsers.directory.sample_parser._parse_samples")
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

        sample_dict_list = [OrderedDict([
            ('Sample_Name', 'my-sample-1'),
            ('Project_ID', '75'),
            ('File_Forward', path.abspath(file_path_1)),
            ('File_Reverse', path.abspath(file_path_2))
        ])]

        mock_parse_samples.return_value = sample_dict_list

        res = parsers.directory.sample_parser._parse_sample_list(sheet_file)

        mock_parse_samples.assert_called_with(sheet_file)
        # Check we have 1 sample
        self.assertEqual(len(res), 1)
        # Check if data is correct
        self.assertEqual(res[0]["Sample_Name"], "my-sample-1")
        self.assertEqual(res[0]["Project_ID"], "75")
        self.assertEqual(res[0]["File_Forward"], path.abspath(file_path_1))
        self.assertEqual(res[0]["File_Reverse"], path.abspath(file_path_2))

    def test_no_forward_read(self):
        """
        No Valid files were found with names given in sample sheet
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_forward.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser._parse_sample_list(file_path)

    def test_no_reverse_read(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_no_reverse.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser._parse_sample_list(file_path)

    def test_mixed_paired_and_single_reads(self):
        directory = path.join(path_to_module, "fake_dir_data")
        file_path = path.join(directory, "list_mixed.csv")

        with self.assertRaises(SampleSheetError):
            res = sample_parser._parse_sample_list(file_path)


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
        self.assertEqual(res[0]["Sample_Name"], "my-sample-1")
        self.assertEqual(res[0]["Project_ID"], "75")
        self.assertEqual(res[0]["File_Forward"], file_name_1)
        self.assertEqual(res[0]["File_Reverse"], file_name_2)

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
