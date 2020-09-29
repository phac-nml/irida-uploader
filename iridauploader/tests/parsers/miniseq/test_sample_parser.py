import unittest
from unittest.mock import patch
from os import path
from csv import reader
from io import StringIO

from iridauploader import parsers
import iridauploader.parsers.miniseq.sample_parser as sample_parser
from iridauploader.parsers.exceptions import SampleSheetError, SequenceFileError
from iridauploader.parsers import common
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
            "Local Run Manager Analysis Id,4004\n"
            "Experiment Name,Some_Test_Data\n"
            "Date,2015-05-14\n"
            "Workflow,GenerateFastQWorkflow\n"
            "Description,12-34\n"
            "Chemistry,Yes\n"
        )

        reads = (
            "151\n"
            "151\n"
        )

        d_headers = ("Sample_ID,Sample_Name,"
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project")

        d_field_values = ("15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
                          "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n"
                          "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n")

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
        self.assertEqual(metadata['readLengths'], "151")
        self.assertEqual(metadata['layoutType'], "PAIRED_END")
        # Other meta data should also be here
        self.assertEqual(metadata['localrunmanager'], "4004")
        self.assertEqual(metadata['experimentName'], "Some_Test_Data")
        self.assertEqual(metadata['date'], "2015-05-14")
        self.assertEqual(metadata['workflow'], "GenerateFastQWorkflow")
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
            "Local Run Manager Analysis Id,4004\n"
            "Experiment Name,Some_Test_Data\n"
            "Date,2015-05-14\n"
            "Workflow,GenerateFastQWorkflow\n"
            "Description,12-34\n"
            "Chemistry,Yes\n"
        )

        reads = (
            "151\n"
        )

        d_headers = ("Sample_ID,Sample_Name,"
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project")

        d_field_values = ("15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n"
                          "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n"
                          "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n")

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

        correct_metadata = {"readLengths": "151",
                            "workflow": "GenerateFastQWorkflow",
                            "localrunmanager": "4004",
                            "date": "10/15/2013",
                            "chemistry": "Amplicon",
                            "description": "Superbug",
                            "experimentName": '1',
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

        correct_metadata = {"readLengths": "151",
                            "workflow": "GenerateFastQWorkflow",
                            "localrunmanager": "4004",
                            "date": "10/15/2013",
                            "chemistry": "Amplicon",
                            "description": "Superbug",
                            "experimentName": '1',
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

        lines = common.get_csv_reader(sheet_file)

        correct_lines = [
            ['[Header]'],
            ['Local Run Manager Analysis Id', '4004'],
            ['Experiment Name', '1'],
            ['Date', '10/15/2013'],
            ['Workflow', 'GenerateFastQWorkflow'],
            ['Description', 'Superbug'],
            ['Chemistry', 'Amplicon'],
            [],
            ['[Reads]'],
            ['151'],
            ['151'],
            [],
            ['[Settings]'],
            ['Adapter', 'AAAAGGGGAAAAGGGGAAA'],
            [],
            ['[Data]'],
            ['Sample_ID', 'Sample_Name', 'index', 'I7_Index_ID', 'index2', 'I5_Index_ID',
             'Sample_Project'],
            ['01-1111-4004', '01-1111', 'AAAAAAAA', 'N01', 'TTTTTTTT', 'S01', '6'],
            ['02-2222-4004', '02-2222', 'GGGGGGGG', 'N02', 'CCCCCCCC', 'S02', '6'],
            ['03-3333-4004', '03-3333', 'CCCCCCCC', 'N03', 'GGGGGGGG', 'S03', '6']
        ]

        for line, c_line in zip(lines, correct_lines):
            self.assertEqual(line, c_line)

    def test_get_csv_reader_no_sheet(self):
        """
        Make sure an error is raised if the csv reader is not given a valid sample sheet
        :return:
        """
        sheet_file = path.join(path_to_module, "fake_ngs_data",
                               "Alignment_1")

        with self.assertRaises(SampleSheetError):
            common.get_csv_reader(sheet_file)


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
        data_dir = path.join(directory, parsers.miniseq.Parser.get_relative_data_directory())
        data_dir = data_dir.replace("*", "some_dir")
        file_list = parsers.common.get_file_list(data_dir)

        sample = model.Sample(
            "01-1111",
            "",
            1,
            {
                "index": "AAAAAAAA",
                "I7_Index_ID": "N01",
                "sample_project": "6",
                "sequencer_sample_ID": "01-1111-4004",
                "I5_Index_ID": "S01",
                "index2": "TTTTTTTT"
            }
        )

        sequence_file_properties = {
            "sequencer_sample_ID": "01-1111-4004",
            "index": "AAAAAAAA",
            "I7_Index_ID": "N01",
            "I5_Index_ID": "S01",
            "index2": "TTTTTTTT",
            "description": ""
        }

        file_path_1 = path.join(path_to_module,
                                "fake_ngs_data", "Alignment_1", "some_dir", "Fastq", "01-1111_S1_L001_R1_001.fastq.gz")
        file_path_2 = path.join(path_to_module,
                                "fake_ngs_data", "Alignment_1", "some_dir", "Fastq", "01-1111_S1_L001_R2_001.fastq.gz")
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
        data_dir = path.join(directory, parsers.miniseq.Parser.get_relative_data_directory())
        data_dir = data_dir.replace("*", "some_dir")
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
        data_dir = path.join(directory, parsers.miniseq.Parser.get_relative_data_directory())
        data_dir = data_dir.replace("*", "some_dir")
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "SampleSheet.csv")

        with self.assertRaises(SequenceFileError):
            res = sample_parser.parse_sample_list(sample_sheet_file=file_path, run_data_directory=data_dir, run_data_directory_file_list=file_list)

    def test_space_in_sample_name(self):
        directory = path.join(path_to_module, "ngs_space_in_sample_name")
        data_dir = path.join(directory, parsers.miniseq.Parser.get_relative_data_directory())
        data_dir = data_dir.replace("*", "some_dir")
        file_list = parsers.common.get_file_list(data_dir)
        file_path = path.join(directory, "SampleSheet.csv")

        # Just making sure this doesn't throw an error
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
            "",
            1,
            {
                "index": "AAAAAAAA",
                "I7_Index_ID": "N01",
                "sample_project": "6",
                "sequencer_sample_ID": "01-1111-4004",
                "I5_Index_ID": "S01",
                "index2": "TTTTTTTT"
            }
        )

        sample2 = model.Sample(
            "02-2222",
            "",
            2,
            {
                "index": "GGGGGGGG",
                "I7_Index_ID": "N02",
                "sample_project": "6",
                "sequencer_sample_ID": "02-2222-4004",
                "I5_Index_ID": "S02",
                "index2": "CCCCCCCC"
            }
        )

        sample3 = model.Sample(
            "03-3333",
            "",
            3,
            {
                "index": "CCCCCCCC",
                "I7_Index_ID": "N03",
                "sample_project": "6",
                "sequencer_sample_ID": "03-3333-4004",
                "I5_Index_ID": "S03",
                "index2": "GGGGGGGG"
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
                "index": "CCCCCCCC",
                "I7_Index_ID": "N03",
                "sample_project": "6",
                "sequencer_sample_ID": "03-3333-4004",
                "I5_Index_ID": "S03",
                "index2": "GGGGGGGG"

            }
        )

        uploadable_dict = {'index': 'CCCCCCCC',
                           'I7_Index_ID': 'N03',
                           'sampleName': '03-3333',
                           'sample_project': '6',
                           'sequencer_sample_ID': '03-3333-4004',
                           'I5_Index_ID': 'S03',
                           'index2': 'GGGGGGGG',
                           'description': 'Deadly bug'}

        sequence_file_dict = {'index': 'CCCCCCCC',
                              'I7_Index_ID': 'N03',
                              'sequencer_sample_ID': '03-3333-4004',
                              'I5_Index_ID': 'S03',
                              'index2': 'GGGGGGGG',
                              'description': 'Deadly bug'}

        res = sample_parser._parse_out_sequence_file(sample)

        self.assertEqual(sample.get_uploadable_dict(), uploadable_dict)
        self.assertEqual(res, sequence_file_dict)


class TestBuildISeqRun(unittest.TestCase):
    """
    Test building the an iseq run from a sample sheet with a csv reader
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_build_valid_with_description_field(self):
        """
        When given a valid directory, ensure a valid SequencingRun is built with Projects, Samples, ect
        :return:
        """
        directory = path.join(path_to_module, "iseq_with_desc_field")
        sheet_file = path.join(directory, "SampleSheet.csv")
        meta_data = sample_parser.parse_metadata(sheet_file)
        data_dir = path.join(directory, parsers.miniseq.Parser.get_relative_data_directory())
        data_dir = data_dir.replace("*", "some_dir")
        file_list = parsers.common.get_file_list(data_dir)

        sample_list = sample_parser.parse_sample_list(sample_sheet_file=sheet_file,
                                                      run_data_directory=data_dir,
                                                      run_data_directory_file_list=file_list)
        sequence_run_type = 'miniseq'

        sequencing_run = parsers.common.build_sequencing_run_from_samples(sample_list, meta_data, sequence_run_type)

        # Returns a SequencingRun
        self.assertEqual(type(sequencing_run), model.SequencingRun)
        # Includes a single project
        self.assertEqual(len(sequencing_run.project_list), 1)
        # is of type Project
        self.assertEqual(type(sequencing_run.project_list[0]), model.Project)
        # Project has 3 samples
        self.assertEqual(len(sequencing_run.project_list[0].sample_list), 3)
        # samples are of type Sample
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0]), model.Sample)
        # samples have correct description
        self.assertEqual(sequencing_run.project_list[0].sample_list[0].description, "desc1")
        # samples have SequenceFile
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0].sequence_file), model.SequenceFile)
