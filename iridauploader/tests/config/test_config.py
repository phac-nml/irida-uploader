import unittest
from unittest.mock import patch
import os

import iridauploader.config as config

path_to_module = os.path.abspath(os.path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


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
        # set the config module level variables back to None
        config.config._conf_parser = None
        config.config._user_config_file = None

    @patch("iridauploader.config.config._init_config_parser")
    @patch("iridauploader.config.config._load_config_from_file")
    @patch("iridauploader.config.config._create_new_config_file")
    @patch("os.path.exists")
    def test_basic_setup_all_functions_called(self, mock_path_exists, mock_create_new_config_file,
                                              mock_load_config_from_file, mock_init_config_parser):

        # Set the config file to True so that it thinks there is a config file
        config.set_config_file(True)
        # start up config setup
        config.setup()
        # First init happens
        mock_init_config_parser.assert_called_with()
        # make sure no attempt to create a file happens
        mock_create_new_config_file.assert_not_called()
        # make sure it tries to load from file
        mock_load_config_from_file.assert_called_with()

    @patch("iridauploader.config.config._load_config_from_file")
    @patch("iridauploader.config.config._create_new_config_file")
    @patch("os.path.exists")
    def test_create_new_file_if_none_exist(self, mock_path_exists, mock_create_new_config_file,
                                           mock_load_config_from_file):

        # Set the config file to False so that the function will check if a default file is set
        config.set_config_file(False)
        # When it checks for a default path and override path,
        # return False for bothso it will attempt to create a new file
        mock_path_exists.side_effect = [False, False]
        # try setting up config to trigger creating a new file
        config.setup()
        # make sure the attempt to create a file happens
        mock_create_new_config_file.assert_called_with()
        # It will attempt to use the file that was just created
        mock_load_config_from_file.assert_called_with()

    @patch("iridauploader.config.config._init_config_parser")
    @patch("iridauploader.config.config._load_config_from_file")
    @patch("iridauploader.config.config._create_new_config_file")
    @patch("os.path.exists")
    def test_dont_create_new_file_if_exists(self, mock_path_exists, mock_create_new_config_file,
                                            mock_load_config_from_file, mock_init_config_parser):

        # Set the config file to False so that the function will check if a default file is set
        config.set_config_file(False)
        # When it checks for a default path, return True so it will attempt to use that file
        mock_path_exists.side_effect = [True]
        # If a new file is created, no exit will happen
        config.setup()
        # First init happens
        mock_init_config_parser.assert_called_with()
        # make sure no attempt to create a file happens
        mock_create_new_config_file.assert_not_called()
        # make sure it tries to load from file
        mock_load_config_from_file.assert_called_with()

    @patch("iridauploader.config.config._init_config_parser")
    @patch("iridauploader.config.config._load_config_from_file")
    @patch("iridauploader.config.config._create_new_config_file")
    @patch("os.path.exists")
    def test_dont_create_new_file_if_override_file_exists(self, mock_path_exists, mock_create_new_config_file,
                                                          mock_load_config_from_file, mock_init_config_parser):
        # Set the config file to False so that the function will check if a default file is set
        config.set_config_file(False)
        # When it checks for config files, return True on check for override so it wont attempt to create a new file
        mock_path_exists.side_effect = [False, True]
        # If a new file is created, no exit will happen
        config.setup()
        # First init happens
        mock_init_config_parser.assert_called_with()
        # make sure no attempt to create a file happens
        mock_create_new_config_file.assert_not_called()
        # make sure it tries to load from file
        mock_load_config_from_file.assert_called_with()

    def test_read_config_option(self):
        """
        Test writing to config file, make sure writen values are written correctly
        :return:
        """
        # set up config
        config.set_config_file(os.path.join(path_to_module, "test_config.conf"))
        config.setup()
        # Test that all the parameters loaded from file are correct
        self.assertEqual(config.read_config_option('client_id'), 'uploader')
        self.assertEqual(config.read_config_option('client_secret'), 'secret')
        self.assertEqual(config.read_config_option('username'), 'admin')
        self.assertEqual(config.read_config_option('password'), 'password1')
        self.assertEqual(config.read_config_option('base_url'), 'http://localhost:8080/irida-latest/api/')
        self.assertEqual(config.read_config_option('parser'), 'miseq')
        self.assertEqual(config.read_config_option('readonly', bool), False)

    def test_set_config_options(self):
        """
        Test writing to config file, make sure writen values are written correctly
        :return:
        """
        # set up config
        config.set_config_file(os.path.join(path_to_module, "test_config.conf"))
        config.setup()
        # Make sure id is initially set to what we expect
        self.assertEqual(config.read_config_option('client_id'), 'uploader')
        # Set and test to a new id
        config.set_config_options(client_id="new_id")
        self.assertEqual(config.read_config_option('client_id'), "new_id")
