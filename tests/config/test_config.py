import unittest
from unittest.mock import patch
import os

import config
import global_settings

path_to_module = os.path.abspath(os.path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'

test_config_file_dir = os.path.join(path_to_module, "test_config_file_dir")


class TestConfig(unittest.TestCase):
    """
    Tests the config module's functionality
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def tearDown(self):
        """
        Deletes files and directories that are used when a test is run
        Sets the module level variables in the config module back to None, so each test is executed from a clean state
        :return:
        """
        # delete files and directory that get created when tests run
        if os.path.exists(os.path.join(test_config_file_dir, "config.conf")):
            os.remove(os.path.join(test_config_file_dir, "config.conf"))
        if os.path.exists(os.path.join(test_config_file_dir)):
            os.rmdir(os.path.join(test_config_file_dir))
        # set the config module level variables back to None
        config.config.conf_parser = None
        config.config.user_config_file = None
        # Set the global settings variable back to None
        global_settings.config_file = None

    @patch("config.config.user_config_dir")
    def test_user_directory(self, mock_user_config_dir):
        """
        Make sure when using the default setup (system variable user directory),
            the config file is found in the correct place
        :param mock_user_config_dir:
        :return:
        """
        mock_user_config_dir.side_effect = [test_config_file_dir]

        config.setup()

        self.assertTrue(os.path.exists(os.path.join(test_config_file_dir, "config.conf")))

    def test_parameter(self):
        """
        Tests that reading from the global variables (parameter passing) works

        Also ensures that it can read from the file correctly with read_config_option
        :return:
        """
        example_path = os.path.join(path_to_module, "example_config.conf")
        global_settings.config_file = example_path

        config.setup()

        self.assertEqual(config.config.user_config_file, example_path)
        # Verify all the options were set correctly
        self.assertEqual(config.read_config_option('client_id'), 'uploader')
        self.assertEqual(config.read_config_option('client_secret'), 'secret')
        self.assertEqual(config.read_config_option('username'), 'admin')
        self.assertEqual(config.read_config_option('password'), 'password1')
        self.assertEqual(config.read_config_option('base_url'), 'http://localhost:8080/irida-latest/api/')
        self.assertEqual(config.read_config_option('parser'), 'miseq')

    @patch("config.config.user_config_dir")
    def test_write_config_option(self, mock_user_config_dir):
        """
        Test writing to config file, make sure writen values are written correctly
        :param mock_user_config_dir:
        :return:
        """
        mock_user_config_dir.side_effect = [test_config_file_dir]

        config.setup()

        self.assertEqual(config.read_config_option('client_id'), '')

        config.write_config_option('client_id', "new_id")

        self.assertEqual(config.read_config_option('client_id'), "new_id")
