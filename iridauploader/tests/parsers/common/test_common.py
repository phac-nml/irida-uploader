import unittest
import os

from iridauploader.parsers import common

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
