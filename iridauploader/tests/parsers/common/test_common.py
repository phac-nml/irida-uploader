import unittest
import os

from iridauploader.parsers import common
from iridauploader.parsers.exceptions import SampleSheetError

path_to_module = os.path.abspath(os.path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestFindDirectoryList(unittest.TestCase):
    """
    Test getting the list of directories
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_find_three(self):
        """
        Given a directory with 3 run directories in it, make sure all 3 directories are included in result
        :return:
        """
        directory = os.path.join(path_to_module, "three_dirs")
        dir_1 = os.path.join(directory, "first")
        dir_2 = os.path.join(directory, "second")
        dir_3 = os.path.join(directory, "third")
        res = common.find_directory_list(directory)

        self.assertIn(dir_1, res)
        self.assertIn(dir_2, res)
        self.assertIn(dir_3, res)

    def test_find_none(self):
        """
        Given a directory with no sequencing run directories in it, make sure an empty list is returned
        :return:
        """
        directory = os.path.join(path_to_module, "no_dirs")
        res = common.find_directory_list(directory)

        self.assertEqual(res, [])


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
        sheet_file = os.path.join(path_to_module, "test_csv_reader.csv")

        lines = common.get_csv_reader(sheet_file)
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
        sheet_file = os.path.join(path_to_module, "fake_dir_data")

        with self.assertRaises(SampleSheetError):
            common.get_csv_reader(sheet_file)
