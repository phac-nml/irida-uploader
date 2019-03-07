import unittest
from os import path
import os

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

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_NEW)
        self.assertIsNone(res.message)

    def test_new_directory_with_info_file(self):
        directory = path.join(path_to_module, "new_dir_with_info_file")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_NEW)
        self.assertIsNone(res.message)

    def test_invalid_directory(self):
        directory = path.join(path_to_module, "invalid_dir")

        res = progress.get_directory_status(directory, "not a SampleSheeet.csv")

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_INVALID)
        self.assertIsNotNone(res.message)

    def test_inaccessible_directory(self):
        directory = path.join(path_to_module, "inaccessible_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_INVALID)
        self.assertIsNotNone(res.message)

    def test_complete_directory(self):
        directory = path.join(path_to_module, "complete_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_COMPLETE)
        self.assertIsNone(res.message)

    def test_partial_directory(self):
        directory = path.join(path_to_module, "partial_dir")

        res = progress.get_directory_status(directory, "SampleSheet.csv")

        self.assertEqual(res.status, progress.DIRECTORY_STATUS_PARTIAL)
        self.assertIsNone(res.message)


class TestWriteDirectoryStatus(unittest.TestCase):
    """
    This class tests that the status file is being written to correctly
    """
    directory = path.join(path_to_module, 'write_status_dir')
    status_file = path.join(directory, "irida_uploader_status.info")

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def tearDown(self):
        # remove status file after using it
        if path.exists(self.status_file):
            os.remove(self.status_file)

    def test_write_to_existing_file(self):
        # File does not exist yet
        self.assertFalse(path.exists(self.status_file))

        # Write to file
        progress.write_directory_status(self.directory, progress.DIRECTORY_STATUS_COMPLETE)
        # Check that file matches what we wrote
        status = progress.get_directory_status(self.directory, "SampleSheet.csv")
        self.assertEqual(progress.DIRECTORY_STATUS_COMPLETE, status.status)

        # Check that the file exists now
        self.assertTrue(path.exists(self.status_file))
        # Write a new status
        progress.write_directory_status(self.directory, progress.DIRECTORY_STATUS_ERROR)
        # Check that the file matches the status we wrote
        status = progress.get_directory_status(self.directory, "SampleSheet.csv")
        self.assertEqual(progress.DIRECTORY_STATUS_ERROR, status.status)

    def test_write_to_new_file(self):
        # File does not exist yet
        self.assertFalse(path.exists(self.status_file))

        # Write to file
        progress.write_directory_status(self.directory, progress.DIRECTORY_STATUS_COMPLETE)
        # Check that file matches what we wrote
        status = progress.get_directory_status(self.directory, "SampleSheet.csv")
        self.assertEqual(progress.DIRECTORY_STATUS_COMPLETE, status.status)
