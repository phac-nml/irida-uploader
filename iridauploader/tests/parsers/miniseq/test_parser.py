import unittest
from os import path

from iridauploader.parsers.miniseq.parser import Parser
from iridauploader.parsers.exceptions import DirectoryError, ValidationError, SampleSheetError
import iridauploader.model as model

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestFindRuns(unittest.TestCase):
    """
    Test finding runs in a directory filled with (possible) run directories
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_find_one_of_three(self):
        """
        Given a directory with 3 potential run directories in it, determine which are new and invalid
        :return:
        """
        directory = path.join(path_to_module, "three_dirs")
        dir_1 = path.join(directory, "first")
        dir_2 = path.join(directory, "second")
        dir_3 = path.join(directory, "third")
        correct_dirs = [dir_1, dir_2, dir_3]

        res = Parser().find_runs(directory)

        self.assertIn(res[0].directory, correct_dirs)
        self.assertIn(res[1].directory, correct_dirs)
        self.assertIn(res[2].directory, correct_dirs)

        for c_dir in res:
            if c_dir.directory == dir_1:
                self.assertEqual(c_dir.status, "new")
            elif c_dir.directory == dir_2:
                self.assertEqual(c_dir.status, "invalid")
            elif c_dir.directory == dir_3:
                self.assertEqual(c_dir.status, "invalid")

    def test_find_none(self):
        """
        Given a directory with no run directories in it, return a empty list
        :return:
        """
        directory = path.join(path_to_module, "no_dirs")

        res = Parser().find_runs(directory)

        self.assertEqual(res, [])


class TestFindSingleRun(unittest.TestCase):
    """
    Test checking if a single directory is a run
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_find_in_dir_with_three_dirs(self):
        """
        Given a directory with directories in it (but no actual run at highest level), show as invalid
        :return:
        """
        directory = path.join(path_to_module, "three_dirs")

        res = Parser().find_single_run(directory)

        self.assertEqual(type(res), model.DirectoryStatus)
        self.assertEqual(res.status, "invalid")
        self.assertEqual(res.directory, directory)

    def test_find_none(self):
        """
        Given a directory with nothing in it, show as invalid
        :return:
        """
        directory = path.join(path_to_module, "no_dirs")

        res = Parser().find_single_run(directory)

        self.assertEqual(type(res), model.DirectoryStatus)
        self.assertEqual(res.status, "invalid")
        self.assertEqual(res.directory, directory)

    def test_find_dir(self):
        """
        Given a valid run directory, show as new
        :return:
        """
        directory = path.join(path_to_module, "three_dirs", "first")

        res = Parser().find_single_run(directory)

        self.assertEqual(type(res), model.DirectoryStatus)
        self.assertEqual(res.status, "new")
        self.assertEqual(res.directory, directory)

    def test_find_dir_no_completed_file(self):
        """
        Given a run directory with no run completed file, show as invalid
        :return:
        """
        directory = path.join(path_to_module, "fake_ngs_data_no_completed")

        res = Parser().find_single_run(directory)

        self.assertEqual(type(res), model.DirectoryStatus)
        self.assertEqual(res.status, "invalid")
        self.assertEqual(res.directory, directory)


class TestGetSampleSheet(unittest.TestCase):
    """
    Test cases related to getting a sample sheet from a known run directory
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid_directory(self):
        """
        test the file path of a valid sequencing run is gotten correctly
        :return:
        """
        directory = path.join(path_to_module, "three_dirs", "first")
        file_path = path.join(directory, "SampleSheet.csv")

        res = Parser().get_sample_sheet(directory)

        self.assertEqual(res, file_path)

    def test_no_sheet_in_directory(self):
        """
        Given an invalid directory, ensure an error is thrown
        :return:
        """
        directory = path.join(path_to_module, "three_dirs", "third")

        with self.assertRaises(DirectoryError) as context:
            Parser().get_sample_sheet(directory)

        self.assertEqual(context.exception.directory, directory)

    def test_unreadable_directory(self):
        """
        Given an invalid directory (chmod 000), ensure the correct error is thown
        :return:
        """
        directory = path.join(path_to_module, "inaccessible_dir")

        with self.assertRaises(DirectoryError) as context:
            Parser().get_sample_sheet(directory)

        self.assertEqual(context.exception.directory, directory)


class TestGetSequencingRun(unittest.TestCase):
    """
    Test building a sequencing run from a sample sheet
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_invalid_sample_sheets(self):
        """
        Given an invalid sample sheet, ensure the correct errors are included in the validation result
        :return:
        """
        sample_sheet = path.join(path_to_module, "invalid_sample_sheet", "SampleSheet.csv")

        with self.assertRaises(ValidationError) as context:
            Parser().get_sequencing_run(sample_sheet)

        validation_result = context.exception.validation_result
        self.assertEqual(type(validation_result), model.ValidationResult)

        for error in validation_result.error_list:
            self.assertEqual(type(error), DirectoryError)

    def test_valid_run(self):
        """
        Given a valid sample sheet, ensure a sequencing run is created
        :return:
        """
        sample_sheet = path.join(path_to_module, "fake_ngs_data", "SampleSheet.csv")

        sequencing_run = Parser().get_sequencing_run(sample_sheet)

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
        # samples have SequenceFile
        self.assertEqual(type(sequencing_run.project_list[0].sample_list[0].sequence_file), model.SequenceFile)
