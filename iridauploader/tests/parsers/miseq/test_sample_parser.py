import unittest
from unittest.mock import patch
from os import path
from csv import reader
from io import StringIO

from iridauploader import parsers
import iridauploader.parsers.miseq.sample_parser as sample_parser
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
            "IEMFileVersion,4\n"
            "Investigator Name,Test Name\n"
            "Experiment Name,Some_Test_Data\n"
            "Date,2015-05-14\n"
            "Workflow,GenerateFASTQ\n"
            "Application,FASTQ Only\n"
            "Assay,ASDF\n"
            "Description,12-34\n"
            "Chemistry,Yes\n"
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
        ).format(h_field_values=h_field_values,
                 reads=reads,
                 d_headers=d_headers,
                 d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        metadata = sample_parser.parse_metadata(None)
        # The meta data we care about the most
        self.assertEqual(metadata['readLengths'], "251")
        self.assertEqual(metadata['layoutType'], "PAIRED_END")
        # Other meta data should also be here
        self.assertEqual(metadata['iemfileversion'], "4")
        self.assertEqual(metadata['investigatorName'], "Test Name")
        self.assertEqual(metadata['experimentName'], "Some_Test_Data")
        self.assertEqual(metadata['date'], "2015-05-14")
        self.assertEqual(metadata['workflow'], "GenerateFASTQ")
        self.assertEqual(metadata['application'], "FASTQ Only")
        self.assertEqual(metadata['assay'], "ASDF")
        self.assertEqual(metadata['description'], "12-34")
        self.assertEqual(metadata['chemistry'], "Yes")

    @patch("iridauploader.parsers.common.get_csv_reader")
    def test_parse_metadata_single_valid(self, mock_csv_reader):
        """
        When given a valid directory, ensure valid metadata is built
        single end reads
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
        ).format(h_field_values=h_field_values,
                 reads=reads,
                 d_headers=d_headers,
                 d_field_values=d_field_values)

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
                               "SampleSheet.csv")
        meta_data = sample_parser.parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "251",
                            "assay": "Nextera XT",
                            "description": "Superbug",
                            "application": "FASTQ Only",
                            "investigatorName": "Some Guy",
                            "adapter": "AAAAGGGGAAAAGGGGAAA",
                            "workflow": "GenerateFASTQ",
                            "reversecomplement": "0",
                            "iemfileversion": "4",
                            "date": "10/15/2013",
                            "experimentName": "1",
                            "chemistry": "Amplicon",
                            "layoutType": "PAIRED_END"}

        self.assertEqual(correct_metadata, meta_data)

    def test_parse_metadata_extra_commas(self):
        """
        Tests parsing meta data when extra commas are in the file
        Testing the parsing meta data with actual files, instead of mocked files
        :return:
        """
        sheet_file = path.join(path_to_module, "testValidSheetTrailingCommas",
                               "SampleSheet.csv")
        meta_data = sample_parser.parse_metadata(sheet_file)

        correct_metadata = {"readLengths": "301",
                            "assay": "TruSeq HT",
                            "description": "252",
                            "application": "FASTQ Only",
                            "investigatorName": "Investigator",
                            "adapter": "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA",
                            "adapterread2": "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT",
                            "workflow": "GenerateFASTQ",
                            "reversecomplement": "0",
                            "iemfileversion": "4",
                            "date": "2015-11-12",
                            "experimentName": "252",
                            "chemistry": "Amplicon",
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
                               "SampleSheet.csv")

        lines = parsers.common.get_csv_reader(sheet_file)

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
            ['01-1111_S1_L001_R1_001.fastq.gz', '01-1111_S1_L001_R2_001.fastq.gz']
        ))
        self.assertTrue(sample_parser._validate_pf_list(
            ['01-1111_S1_L001_R1_001.fastq.gz']
        ))

    def test_invalid_lists(self):
        self.assertFalse(sample_parser._validate_pf_list(
            ['01-1111_S1_L001_R1_001.fastq.gz', '01-1111_S1_L001_R2_001.fastq.gz', '01-1111_S1_L001_R3_001.fastq.gz']
        ))

        self.assertFalse(sample_parser._validate_pf_list([]))

    def test_invalid_file_names(self):
        self.assertFalse(sample_parser._validate_pf_list(
            ['01-1111_S1_L001_R_001.fastq.gz', '01-1111_S1_L001_R_001.fastq.gz']
        ))
        self.assertFalse(sample_parser._validate_pf_list(
            ['01-1111_S1_L001_1_001.fastq.gz', '01-1111_S1_L001_2_001.fastq.gz']
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
        sheet_file = path.join(directory, "SampleSheet.csv")
        data_dir = path.join(directory, parsers.miseq.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)

        sample = model.Sample(
            "01-1111",
            "Super bug",
            1,
            {
                "Sample_Well": "01",
                "index": "AAAAAAAA",
                "Sample_Plate": "1",
                "I7_Index_ID": "N01",
                "sample_project": "6",
                "sequencer_sample_name": "01-1111",
                "I5_Index_ID": "S01",
                "index2": "TTTTTTTT",
            }
        )

        sequence_file_properties = {
            'Sample_Plate': '1',
            'Sample_Well': '01',
            'I7_Index_ID': 'N01',
            'index': 'AAAAAAAA',
            'I5_Index_ID': 'S01',
            'index2': 'TTTTTTTT'
        }

        file_path_1 = path.join(path_to_module,
                                "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz")
        file_path_2 = path.join(path_to_module,
                                "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz")
        raw_file_list = [file_path_1, file_path_2]

        res = sample_parser.parse_sample_list(sample_sheet_file=sheet_file, run_data_directory=data_dir, run_data_directory_file_list=file_list)

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
        data_dir = path.join(directory, parsers.miseq.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "SampleSheet.csv")

        with self.assertRaises(SequenceFileError):
            res = sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir, run_data_directory_file_list=file_list)

    def test_not_valid_pf_list(self):
        """
        The file list in the sample sheet is invalid
        :return:
        """
        directory = path.join(path_to_module, "ngs_not_valid_pf_list")
        data_dir = path.join(directory, parsers.miseq.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "SampleSheet.csv")

        with self.assertRaises(SequenceFileError):
            res = sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir, run_data_directory_file_list=file_list)

    def test_space_in_sample_name(self):
        directory = path.join(path_to_module, "ngs_space_in_sample_name")
        data_dir = path.join(directory, parsers.miseq.Parser.get_relative_data_directory())
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "SampleSheet.csv")

        # Just making sure this doesn't thow an error
        sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir, run_data_directory_file_list=file_list)


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
                               "SampleSheet.csv")

        sample1 = model.Sample(
            "01-1111",
            "Super bug",
            1,
            {
                "Sample_Well": "01",
                "index": "AAAAAAAA",
                "Sample_Plate": "1",
                "I7_Index_ID": "N01",
                "sample_project": "6",
                "sequencer_sample_name": "01-1111",
                "I5_Index_ID": "S01",
                "index2": "TTTTTTTT",
            }
        )

        sample2 = model.Sample(
            "02-2222",
            "Scary bug",
            2,
            {
                "Sample_Well": "02",
                "index": "GGGGGGGG",
                "Sample_Plate": "2",
                "I7_Index_ID": "N02",
                "sample_project": "6",
                "sequencer_sample_name": "02-2222",
                "I5_Index_ID": "S02",
                "index2": "CCCCCCCC",
            }
        )

        sample3 = model.Sample(
            "03-3333",
            "Deadly bug",
            3,
            {
                "Sample_Well": "03",
                "index": "CCCCCCCC",
                "Sample_Plate": "3",
                "I7_Index_ID": "N03",
                "sample_project": "6",
                "sequencer_sample_name": "03-3333",
                "I5_Index_ID": "S03",
                "index2": "GGGGGGGG",
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
            "03-3333",
            "Deadly bug",
            None,
            {
                "Sample_Well": "03",
                "index": "CCCCCCCC",
                "Sample_Plate": "3",
                "I7_Index_ID": "N03",
                "sampleName": "03-3333",
                "sampleProject": "6",
                "sequencerSampleId": "03-3333",
                "I5_Index_ID": "S03",
                "index2": "GGGGGGGG",
                "description": "Deadly bug"
            }
        )

        uploadable_dict = {'Sample_Well': '03',
                           'index': 'CCCCCCCC',
                           'Sample_Plate': '3',
                           'I7_Index_ID': 'N03',
                           'sampleName': '03-3333',
                           'sampleProject': '6',
                           'sequencerSampleId': '03-3333',
                           'I5_Index_ID': 'S03',
                           'index2': 'GGGGGGGG',
                           'description': 'Deadly bug'}

        sequence_file_dict = {'Sample_Well': '03',
                              'index': 'CCCCCCCC',
                              'Sample_Plate': '3',
                              'I7_Index_ID': 'N03',
                              'sampleProject': '6',
                              'sequencerSampleId': '03-3333',
                              'I5_Index_ID': 'S03',
                              'index2': 'GGGGGGGG'}

        res = sample_parser._parse_out_sequence_file(sample)

        self.assertEqual(sample.get_uploadable_dict(), uploadable_dict)
        self.assertEqual(res, sequence_file_dict)
