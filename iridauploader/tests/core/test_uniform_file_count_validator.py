import unittest
from os import path


from iridauploader.core import uniform_file_count_validator
from iridauploader.parsers.miseq import parser as miseq_parser
from iridauploader.parsers.exceptions import SequenceFileError
from iridauploader import model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestValidateFileSizeMinimum(unittest.TestCase):
    """
    Testing the validate_uniform_file_count function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @staticmethod
    def _make_seq_run_paired():
        """
        Make a sequencing run pointed at real data for the tests
        This dataset is a paired end run
        :return: SequencingRun object
        """
        files_1 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz"),
        ])
        files_2 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222_S1_L001_R2_001.fastq.gz"),
        ])
        files_3 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R2_001.fastq.gz"),
        ])
        sample_1 = model.Sample("test_sample", "description", 1)
        sample_1.sequence_file = files_1
        sample_2 = model.Sample("test_sample", "description", 1)
        sample_2.sequence_file = files_2
        sample_3 = model.Sample("test_sample", "description", 1)
        sample_3.sequence_file = files_3
        project = model.Project("test_project", [sample_1, sample_2, sample_3], "description")
        sequencing_run = model.SequencingRun({"layoutType": "PAIRED_END"}, [project], "miseq")
        return sequencing_run

    @staticmethod
    def _make_seq_run_single():
        """
        Make a sequencing run pointed at real data for the tests
        This dataset is a single end run
        :return: SequencingRun object
        """
        files_1 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
        ])
        files_2 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222_S1_L001_R1_001.fastq.gz"),
        ])
        files_3 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R1_001.fastq.gz"),
        ])
        sample_1 = model.Sample("test_sample", "description", 1)
        sample_1.sequence_file = files_1
        sample_2 = model.Sample("test_sample", "description", 1)
        sample_2.sequence_file = files_2
        sample_3 = model.Sample("test_sample", "description", 1)
        sample_3.sequence_file = files_3
        project = model.Project("test_project", [sample_1, sample_2, sample_3], "description")
        sequencing_run = model.SequencingRun({"layoutType": "SINGLE_END"}, [project], "miseq")
        return sequencing_run

    @staticmethod
    def _make_seq_run_mixed():
        """
        Make a sequencing run pointed at real data for the tests
        This dataset mixes single end and paired end runs, but identifies as paired end
        :return: SequencingRun object
        """
        files_1 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz"),
        ])
        files_2 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222_S1_L001_R1_001.fastq.gz"),
        ])
        files_3 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R1_001.fastq.gz"),
        ])
        sample_1 = model.Sample("test_sample", "description", 1)
        sample_1.sequence_file = files_1
        sample_2 = model.Sample("test_sample", "description", 1)
        sample_2.sequence_file = files_2
        sample_3 = model.Sample("test_sample", "description", 1)
        sample_3.sequence_file = files_3
        project = model.Project("test_project", [sample_1, sample_2, sample_3], "description")
        sequencing_run = model.SequencingRun({"layoutType": "PAIRED_END"}, [project], "miseq")
        return sequencing_run

    @staticmethod
    def _make_seq_run_paired_with_incorrect_file_name():
        """
        Make a sequencing run pointed at real data for the tests
        This dataset is a paired end run with a common user error of a misnamed file
        :return: SequencingRun object
        """
        files_1 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "01-1111_S1_L001_R2_001.fastq.gz"),
        ])
        files_2 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "02-2222x_S1_L001_R2_001.fastq.gz"),
        ])
        files_3 = model.SequenceFile([
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R1_001.fastq.gz"),
            path.join(path_to_module,
                      "fake_ngs_data", "Data", "Intensities", "BaseCalls", "03-3333_S1_L001_R2_001.fastq.gz"),
        ])
        sample_1 = model.Sample("test_sample", "description", 1)
        sample_1.sequence_file = files_1
        sample_2 = model.Sample("test_sample", "description", 1)
        sample_2.sequence_file = files_2
        sample_3 = model.Sample("test_sample", "description", 1)
        sample_3.sequence_file = files_3
        project = model.Project("test_project", [sample_1, sample_2, sample_3], "description")
        sequencing_run = model.SequencingRun({"layoutType": "PAIRED_END"}, [project], "miseq")
        return sequencing_run

    def test_run_valid_paired(self):
        sequencing_run = self._make_seq_run_paired()

        # Run code to test
        res = uniform_file_count_validator.validate_uniform_file_count(sequencing_run)

        # validate result
        self.assertTrue(res.is_valid(), "valid run is being detected as invalid")

    def test_run_valid_single(self):
        sequencing_run = self._make_seq_run_single()

        # Run code to test
        res = uniform_file_count_validator.validate_uniform_file_count(sequencing_run)

        # validate result
        self.assertTrue(res.is_valid(), "valid run is being detected as invalid")

    def test_run_valid_mixed_expecting_paired(self):
        sequencing_run = self._make_seq_run_mixed()

        # Run code to test
        res = uniform_file_count_validator.validate_uniform_file_count(sequencing_run)

        # validate result
        self.assertFalse(res.is_valid(), "invalid run is being detected as valid")

    def test_run_valid_mixed_expecting_single(self):
        sequencing_run = self._make_seq_run_mixed()
        # change metadata to expect single end run
        sequencing_run.metadata["layoutType"] = "SINGLE_END"

        # Run code to test
        res = uniform_file_count_validator.validate_uniform_file_count(sequencing_run)

        # validate result
        self.assertFalse(res.is_valid(), "invalid run is being detected as valid")

    def test_run_invalid_name_error(self):
        # Build sequencing run from real data with common user error
        # One of the files has an extra character in the filename in a spot that is within spec to be parsed,
        # but results in mixing single end and paired end files in the same run.
        sample_sheet_path = path.join(
            path_to_module, "fake_ngs_data_name_error", "SampleSheet.csv")
        parser_instance = miseq_parser.Parser()
        sequencing_run = parser_instance.get_sequencing_run(sample_sheet_path)

        # Run code to test
        res = uniform_file_count_validator.validate_uniform_file_count(sequencing_run)

        # validate result
        self.assertFalse(res.is_valid(), "invalid run is being detected as valid")
        self.assertEqual(
            str(res.error_list),
            str([SequenceFileError(
                'File count for sample `02-2222` does not match the expected file count `2`. Please verify your data.'
            )]))
