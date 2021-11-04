import unittest
from unittest.mock import patch
from os import path


from iridauploader.core import file_size_validator
from iridauploader import model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestValidateFileSizeMinimum(unittest.TestCase):
    """
    Testing the validate_file_size_minimum function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @staticmethod
    def _make_seq_run():
        """
        Make a sequencing run pointed at real data for the tests
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

    @patch("iridauploader.core.file_size_validator.config.read_config_option")
    def test_files_too_small(self, mock_read_file_size_config_option):
        # force the function to grab 100 (min file size) when it tries to call config
        mock_read_file_size_config_option.side_effect = [100]

        # make a sequencing run to work with
        sequencing_run = self._make_seq_run()

        # Run code to test
        res = file_size_validator.validate_file_size_minimum(sequencing_run)

        # validate result
        self.assertFalse(res.is_valid(), "File size is not too small")
        print(res)

    @patch("iridauploader.core.file_size_validator.config.read_config_option")
    def test_files_not_too_small(self, mock_read_file_size_config_option):
        # force the function to grab 0 (min file size) when it tries to call config
        mock_read_file_size_config_option.side_effect = [0]

        # make a sequencing run to work with
        sequencing_run = self._make_seq_run()

        # Run code to test
        res = file_size_validator.validate_file_size_minimum(sequencing_run)

        # validate result
        self.assertTrue(res.is_valid(), "File size is too small")
        print(res)
