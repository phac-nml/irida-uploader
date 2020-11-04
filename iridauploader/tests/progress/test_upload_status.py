import unittest
from unittest.mock import patch
from os import path
import os
import time

import iridauploader.progress as progress
from iridauploader.model import DirectoryStatus
from iridauploader.config import config

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

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.NEW)
        self.assertEqual(res.directory, directory)
        self.assertIsNone(res.message)

    def test_new_directory_multiple_files(self):
        directory = path.join(path_to_module, "new_dir_two_files")

        res = progress.get_directory_status(directory, ["SampleSheet.csv", 'CompletedJobInfo.xml'])

        self.assertEqual(res.status, DirectoryStatus.NEW)
        self.assertEqual(res.directory, directory)
        self.assertIsNone(res.message)

    def test_new_directory_one_file_missing(self):
        directory = path.join(path_to_module, "new_dir")

        res = progress.get_directory_status(directory, ["SampleSheet.csv", 'not_a_file.txt'])

        self.assertEqual(res.status, DirectoryStatus.INVALID)
        self.assertEqual(res.directory, directory)
        self.assertIsNotNone(res.message)

    def test_new_directory_with_info_file(self):
        directory = path.join(path_to_module, "new_dir_with_info_file")

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.NEW)
        self.assertEqual(res.directory, directory)
        self.assertIsNone(res.message)

    def test_invalid_directory(self):
        directory = path.join(path_to_module, "invalid_dir")

        res = progress.get_directory_status(directory, ["not a SampleSheeet.csv"])

        self.assertEqual(res.status, DirectoryStatus.INVALID)
        self.assertEqual(res.directory, directory)
        self.assertIsNotNone(res.message)

    def test_inaccessible_directory(self):
        directory = path.join(path_to_module, "inaccessible_dir")

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.INVALID)
        self.assertEqual(res.directory, directory)
        self.assertIsNotNone(res.message)

    def test_complete_directory(self):
        directory = path.join(path_to_module, "complete_dir")

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.COMPLETE)
        self.assertEqual(res.directory, directory)
        self.assertIsNone(res.message)

    def test_partial_directory(self):
        directory = path.join(path_to_module, "partial_dir")

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.PARTIAL)
        self.assertEqual(res.directory, directory)
        self.assertIsNone(res.message)

    def test_has_miseq_complete_file(self):
        """
        Tests legacy support to show runs that contain .miseqUploaderComplete as COMPLETE
        :return:
        """
        directory = path.join(path_to_module, "has_miseq_complete")

        res = progress.get_directory_status(directory, ["SampleSheet.csv"])

        self.assertEqual(res.status, DirectoryStatus.COMPLETE)
        self.assertEqual(res.directory, directory)
        self.assertEqual(res.message, "Legacy uploader run. Set to complete to avoid uploading duplicate data.")


class TestWriteDirectoryStatus(unittest.TestCase):
    """
    This class tests that the status file is being written to correctly
    """
    directory = path.join(path_to_module, 'write_status_dir')
    status_file = path.join(directory, "irida_uploader_status.info")

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        config._init_config_parser()

    def tearDown(self):
        # remove status file after using it
        if path.exists(self.status_file):
            os.remove(self.status_file)

    def test_write_to_existing_file(self):
        # File does not exist yet
        self.assertFalse(path.exists(self.status_file))

        # Create DirectoryStatus to use for writing
        directory_status = DirectoryStatus(self.directory)

        # Write to file
        directory_status.status = DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status)
        # Check that file matches what we wrote
        status = progress.get_directory_status(self.directory, ["SampleSheet.csv"])
        self.assertEqual(DirectoryStatus.COMPLETE, status.status)

        # Check that the file exists now
        self.assertTrue(path.exists(self.status_file))
        # Write a new status
        directory_status.status = DirectoryStatus.ERROR
        progress.write_directory_status(directory_status)
        # Check that the file matches the status we wrote
        status = progress.get_directory_status(self.directory, ["SampleSheet.csv"])
        self.assertEqual(DirectoryStatus.ERROR, status.status)

    def test_write_to_new_file(self):
        # File does not exist yet
        self.assertFalse(path.exists(self.status_file))

        # Create DirectoryStatus to use for writing
        directory_status = DirectoryStatus(self.directory)

        # Write to file
        directory_status.status = DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status)
        # Check that file matches what we wrote
        status = progress.get_directory_status(self.directory, ["SampleSheet.csv"])
        self.assertEqual(DirectoryStatus.COMPLETE, status.status)

    def test_write_with_readonly_is_true_file(self):
        # set readonly to True in config
        config.set_config_options(readonly=True)
        # File does not exist yet
        self.assertFalse(path.exists(self.status_file))

        # Create DirectoryStatus to use for writing
        directory_status = DirectoryStatus(self.directory)

        # Try write to file (WRITE COMPLETE)
        directory_status.status = DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status)
        # Check that file matches what we wrote
        # We should find it as NEW as we have readonly=True
        status = progress.get_directory_status(self.directory, ["SampleSheet.csv"])
        self.assertEqual(DirectoryStatus.NEW, status.status)


class TestDelayedTimeHasPassed(unittest.TestCase):
    """
    Tests core.upload_helpers.delayed_time_has_passed
    """

    class StubDirectoryStatus:
        time = None

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("time.mktime")
    def test_has_passed(self, mock_mktime):
        """
        Tests that True is returned when enough time has passed
        :return:
        """
        # time.mktime will return the time float from 2 minutes ago
        mock_mktime.side_effect = [time.time() - (2 * 60)]

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status.time = time.strftime(DirectoryStatus.JSON_DATE_TIME_FORMAT)
        # run was delayed for 1 minute
        delay_minutes = 1

        self.assertEqual(True, progress.upload_status._delayed_time_has_passed(stub_directory_status, delay_minutes))

    def test_delay_is_zero(self):
        """
        Tests that True is returned when there is no delay
        :return:
        """
        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status.time = time.strftime(DirectoryStatus.JSON_DATE_TIME_FORMAT)
        # run was delayed for 1 minute
        delay_minutes = 0

        self.assertEqual(True, progress.upload_status._delayed_time_has_passed(stub_directory_status, delay_minutes))

    @patch("time.mktime")
    def test_has_not_passed(self, mock_mktime):
        """
        Tests that False is returned when enough time has not passed
        :return:
        """
        # time.mktime will return the time float from right now
        mock_mktime.side_effect = [time.time()]

        stub_directory_status = self.StubDirectoryStatus()
        stub_directory_status.time = time.strftime(DirectoryStatus.JSON_DATE_TIME_FORMAT)
        # run was delayed for 10 minute
        delay_minutes = 10

        self.assertEqual(False, progress.upload_status._delayed_time_has_passed(stub_directory_status, delay_minutes))
