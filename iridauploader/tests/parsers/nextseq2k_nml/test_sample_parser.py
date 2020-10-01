import unittest
from unittest.mock import patch
from os import path
from csv import reader
from io import StringIO

from iridauploader import parsers
import iridauploader.parsers.nextseq2k_nml.sample_parser as sample_parser
from iridauploader.parsers.exceptions import SampleSheetError, SequenceFileError
import iridauploader.model as model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestParseMetadata(unittest.TestCase):
    """
    Test building meta data from sample sheets with a csv reader
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_parse_metadata_paired_valid(self, mock_csv_reader):
        """
        When given a valid directory, ensure valid metadata is built
        paired end reads
        :return:
        """
        h_field_values = (
            "FileFormatVersion,2\n"
            "RunName,some_run\n"
            "InstrumentPlatform,NextSeq1k2k\n"
            "InstrumentType,NextSeq2000\n"
        )

        reads = (
            "Read1Cycles,101\n"
            "Read2Cycles,101\n"
            "Index1Cycles,8\n"
            "Index2Cycles,8\n"
        )

        d_headers = "Sample_ID,Index,Index2,Sample_Project"

        d_field_values = (
            "01A100001,AAAAAAAA,TTTTTTTT,6\n"
            "01A100002,GGGGGGGG,CCCCCCCC,6\n"
            "01A100003,GGGGGGGG,CCCCCCCC,6\n"
        )

        file_contents_str = (
            "[Header]\n"
            "{h_field_values}\n"
            "[Reads]\n"
            "{reads}\n"
            "[BCLConvert_Data]\n"
            "{d_headers}\n"
            "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        metadata = sample_parser.parse_metadata(None)
        # The meta data we care about the most
        self.assertEqual(metadata['readLengths'], "101")
        self.assertEqual(metadata['layoutType'], "PAIRED_END")
        self.assertEqual(metadata['indexCycles'], "8")

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_parse_metadata_single_valid(self, mock_csv_reader):
        """
        When given a valid directory, ensure valid metadata is built
        single end reads
        :return:
        """
        h_field_values = (
            "FileFormatVersion,2\n"
            "RunName,some_run\n"
            "InstrumentPlatform,NextSeq1k2k\n"
            "InstrumentType,NextSeq2000\n"
        )

        reads = (
            "Read1Cycles,101\n"
            "Index1Cycles,8\n"
        )

        d_headers = "Sample_ID,Index,Index2,Sample_Project"

        d_field_values = (
            "01A100001,AAAAAAAA,TTTTTTTT,6\n"
            "01A100002,GGGGGGGG,CCCCCCCC,6\n"
            "01A100003,GGGGGGGG,CCCCCCCC,6\n"
        )

        file_contents_str = (
            "[Header]\n"
            "{h_field_values}\n"
            "[Reads]\n"
            "{reads}\n"
            "[BCLConvert_Data]\n"
            "{d_headers}\n"
            "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        metadata = sample_parser.parse_metadata(None)
        self.assertEqual(metadata['layoutType'], "SINGLE_END")

    def test_parse_metadata(self):
        """
        Testing the parsing meta data with actual files, instead of mocked files
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "UploadList.csv")
        meta_data = sample_parser.parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "101",
                            "indexCycles": "8",
                            "layoutType": "PAIRED_END"}

        self.assertEqual(correct_metadata, meta_data)

    def test_parse_metadata_extra_commas(self):
        """
        Tests parsing meta data when extra commas are in the file
        Testing the parsing meta data with actual files, instead of mocked files
        :return:
        """
        sheet_file = path.join(path_to_module, "testValidSheetTrailingCommas",
                               "UploadList.csv")
        meta_data = sample_parser.parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "101",
                            "indexCycles": "8",
                            "layoutType": "PAIRED_END"}

        self.assertEqual(correct_metadata, meta_data)


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
        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "UploadList.csv")

        lines = parsers.common.get_csv_reader(sheet_file)

        correct_lines = [
            ['[Header]'],
            ['FileFormatVersion', '2'],
            ['RunName', 'some_run'],
            ['InstrumentPlatform', 'NextSeq1k2k'],
            ['InstrumentType', 'NextSeq2000'],
            [],
            ['[Reads]'],
            ['Read1Cycles', '101'],
            ['Read2Cycles', '101'],
            ['Index1Cycles', '8'],
            ['Index2Cycles', '8'],
            [],
            ['[BCLConvert_Settings]'],
            ['SoftwareVersion', '3.5.8'],
            ['AdapterRead1', 'CTGTCTCTTTTTTTTTTT'],
            ['AdapterRead2', 'CTGTCTCTCCCCCCCCCC'],
            [],
            ['[BCLConvert_Data]'],
            ['Sample_ID', 'Index', 'Index2', 'Sample_Project'],
            ['01A100001', 'AAAAAAAA', 'TTTTTTTT', '6'],
            ['01A100002', 'GGGGGGGG', 'CCCCCCCC', '6'],
            ['01A100003', 'GGGGGGGG', 'CCCCCCCC', '6']
        ]

        for line, c_line in zip(lines, correct_lines):
            self.assertEqual(line, c_line)

    def test_get_csv_reader_no_sheet(self):
        """
        Make sure an error is raised if the csv reader is not given a valid sample sheet
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "Data")

        with self.assertRaises(SampleSheetError):
            parsers.common.get_csv_reader(sheet_file)


class TestValidatePfList(unittest.TestCase):
    """
    Testing the various cases that can appear when validating the pf list
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid_lists(self):
        self.assertTrue(sample_parser._validate_pf_list(
            ['01A100001_S1_L001_R1_001.fastq.gz', '01-1111_S1_L001_R2_001.fastq.gz']
        ))
        self.assertTrue(sample_parser._validate_pf_list(
            ['01A100001_S1_L001_R1_001.fastq.gz']
        ))

    def test_invalid_lists(self):
        self.assertFalse(sample_parser._validate_pf_list(
            ['01A100001_S1_L001_R1_001.fastq.gz', '01-1111_S1_L001_R2_001.fastq.gz', '01-1111_S1_L001_R3_001.fastq.gz']
        ))

        self.assertFalse(sample_parser._validate_pf_list([]))

    def test_invalid_file_names(self):
        self.assertFalse(sample_parser._validate_pf_list(
            ['01A100001_S1_L001_R_001.fastq.gz', '01-1111_S1_L001_R_001.fastq.gz']
        ))
        self.assertFalse(sample_parser._validate_pf_list(
            ['01A100001_S1_L001_1_001.fastq.gz', '01-1111_S1_L001_2_001.fastq.gz']
        ))


class TestParseSampleList(unittest.TestCase):
    """
    test parsing the list of samples from a sample sheet
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid(self):
        """
        Ensure a a parsed valid directory matches the expected sample list
        :return:
        """
        directory = path.join(path_to_module, "fake_ngs_data")
        sheet_file = path.join(directory, "UploadList.csv")
        data_dir = path.join(directory, parsers.nextseq2k_nml.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)

        sample = model.Sample(
            "01A100001",
            "",
            1,
            {
                "Index": "AAAAAAAA",
                "sample_project": "6",
                "Index2": "TTTTTTTT",
            }
        )

        sequence_file_properties = {
            'Index': 'AAAAAAAA',
            'Index2': 'TTTTTTTT',
            'description': "",
        }

        file_path_1 = path.join(path_to_module,
                                "fake_ngs_data", "Analysis", "1", "Data", "fast1", "01A100001_S1_L001_R1_001.fastq.gz")
        file_path_2 = path.join(path_to_module,
                                "fake_ngs_data", "Analysis", "1", "Data", "fast1", "01A100001_S1_L001_R2_001.fastq.gz")
        raw_file_list = [file_path_1, file_path_2]

        res = sample_parser.parse_sample_list(sample_sheet_file=sheet_file, run_data_directory=data_dir,
                                              run_data_directory_file_list=file_list)

        # Check sample is the same
        self.assertEqual(res[0].get_uploadable_dict(), sample.get_uploadable_dict())
        # Check sequencing file is correct
        self.assertEqual(res[0].sequence_file.properties_dict, sequence_file_properties)
        self.assertEqual(res[0].sequence_file.file_list.sort(), raw_file_list.sort())

    def test_not_pf_list(self):
        """
        No Valid files were found with names given in sample sheet
        :return:
        """
        directory = path.join(path_to_module, "ngs_not_pf_list")
        data_dir = path.join(directory, parsers.nextseq2k_nml.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "UploadList.csv")

        with self.assertRaises(SequenceFileError):
            res = sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir,
                                                  run_data_directory_file_list=file_list)

    def test_not_valid_pf_list(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "ngs_not_valid_pf_list")
        data_dir = path.join(directory, parsers.nextseq2k_nml.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "UploadList.csv")

        with self.assertRaises(SequenceFileError):
            res = sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir,
                                                  run_data_directory_file_list=file_list)

    def test_space_in_sample_name(self):
        directory = path.join(path_to_module, "ngs_space_in_sample_name")
        data_dir = path.join(directory, parsers.nextseq2k_nml.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "UploadList.csv")

        # Just making sure this doesn't throw an error
        sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir,
                                        run_data_directory_file_list=file_list)


class TestParseSamples(unittest.TestCase):
    """
    Test validity or invalidity of parsed samples
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_parse_samples_valid(self):
        """
        Ensure a a parsed valid directory matches the expected samples
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "UploadList.csv")

        sample1 = model.Sample(
            "01A100001",
            "",
            1,
            {
                "Index": "AAAAAAAA",
                "sample_project": "6",
                "Index2": "TTTTTTTT",
                "description": ''
            }
        )

        sample2 = model.Sample(
            "01A100002",
            "",
            2,
            {
                "Index": "GGGGGGGG",
                "sample_project": "6",
                "Index2": "CCCCCCCC",
                "description": ''
            }
        )

        sample3 = model.Sample(
            "01A100003",
            "",
            3,
            {
                "Index": "GGGGGGGG",
                "sample_project": "6",
                "Index2": "CCCCCCCC",
                "description": ''
            }
        )

        correct_samples = [sample1, sample2, sample3]

        res = sample_parser._parse_samples(sheet_file)
        for r_sample, c_sample in zip(res, correct_samples):
            self.assertEqual(r_sample.get_uploadable_dict(), c_sample.get_uploadable_dict())


class TestParseOutSequenceFile(unittest.TestCase):
    """
    test building the sample object
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_parse_out_sequence_file(self):
        """
        Tests that parse out sequence file correctly filters sample related data from the extra params dict
        And ensures that the uploadable dict correctly includes all the needed data after removal
        :return:
        """
        sample = model.Sample(
            "01A100003",
            "",
            3,
            {
                "Index": "GGGGGGGG",
                "sampleProject": "6",
                "Index2": "CCCCCCCC",
                "description": ''
            }
        )

        uploadable_dict = {'Index': 'GGGGGGGG',
                           'sampleName': '01A100003',
                           'sampleProject': '6',
                           'Index2': 'CCCCCCCC',
                           'description': ''}

        sequence_file_dict = {'Index': 'GGGGGGGG',
                              'sampleProject': '6',
                              'Index2': 'CCCCCCCC',
                              'description': ''}

        res = sample_parser._parse_out_sequence_file(sample)

        self.assertEqual(sample.get_uploadable_dict(), uploadable_dict)
        self.assertEqual(res, sequence_file_dict)
