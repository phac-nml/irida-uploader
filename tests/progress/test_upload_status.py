import unittest
from os import path

import progress

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestGetDirectoryStatus(unittest.TestCase):
    """
    This testing class checks the different cases for new, complete, partial, and invalid sequencing run directories
    """
    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_new_directory(self):
        directory = path.join(path_to_module, "new_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_NEW)
        self.assertIsNone(res.message)

    def test_new_directory_with_info_file(self):
        directory = path.join(path_to_module, "new_dir_with_info_file")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_NEW)
        self.assertIsNone(res.message)

    def test_invalid_directory(self):
        directory = path.join(path_to_module, "invalid_dir")

        res = progress.get_directory_status(directory, "not a SampleSheeet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_INVALID)
        self.assertIsNotNone(res.message)

    def test_inaccessible_directory(self):
        directory = path.join(path_to_module, "inaccessible_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_INVALID)
        self.assertIsNotNone(res.message)

    def test_complete_directory(self):
        directory = path.join(path_to_module, "complete_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_COMPLETE)
        self.assertIsNone(res.message)

    def test_partial_directory(self):
        directory = path.join(path_to_module, "partial_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.upload_status.DIRECTORY_STATUS_PARTIAL)
        self.assertIsNone(res.message)
