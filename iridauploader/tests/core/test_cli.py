import unittest
from unittest.mock import patch
from os import path

from iridauploader.core import cli

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestCliEntryPoints(unittest.TestCase):
    """
    Tests the core.cli package entry points into core.upload via main()
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload.upload_run_single_entry")
    @patch("iridauploader.core.cli._config_uploader")
    @patch("iridauploader.core.cli.init_argparser")
    def test_upload_regular(self, mock_init_argparser, mock_configure_uploader, mock_upload_run_single_entry):

        class StubArgs:
            """
            Contains dummy properties that mimic the actual arguments object
            """
            @property
            def directory(self):
                return path_to_module

            @property
            def force(self):
                return False

            @property
            def continue_partial(self):
                return False

            @property
            def batch(self):
                return False

            @property
            def upload_mode(self):
                return None

        stub_args_object = StubArgs()
        # stub_argparser returns the above args object
        stub_argparser = unittest.mock.MagicMock()
        stub_argparser.parse_args.side_effect = [stub_args_object]
        # mock_init_argparser returns the above stub_argparser, which contains the args object
        mock_init_argparser.side_effect = [stub_argparser]

        mock_configure_uploader.side_effect = [None]
        # mock the core code exiting
        stub_upload_exit = unittest.mock.MagicMock()
        stub_upload_exit.exit_code.side_effect = 0
        mock_upload_run_single_entry.side_effect = [stub_upload_exit]

        cli.main()

        # ensure the configuration is called
        mock_configure_uploader.assert_called_once_with(stub_args_object)
        # Verify final call
        mock_upload_run_single_entry.assert_called_once_with(stub_args_object.directory,
                                                             stub_args_object.force,
                                                             stub_args_object.upload_mode,
                                                             stub_args_object.continue_partial)

    @patch("iridauploader.core.upload.batch_upload_single_entry")
    @patch("iridauploader.core.cli._config_uploader")
    @patch("iridauploader.core.cli.init_argparser")
    def test_upload_batch(self, mock_init_argparser, mock_configure_uploader, mock_batch_upload_single_entry):

        class StubArgs:
            """
            Contains dummy properties that mimic the actual arguments object
            """
            @property
            def directory(self):
                return path_to_module

            @property
            def force(self):
                return False

            @property
            def continue_partial(self):
                return False

            @property
            def batch(self):
                return True

            @property
            def upload_mode(self):
                return None

        stub_args_object = StubArgs()
        # stub_argparser returns the above args object
        stub_argparser = unittest.mock.MagicMock()
        stub_argparser.parse_args.side_effect = [stub_args_object]
        # mock_init_argparser returns the above stub_argparser, which contains the args object
        mock_init_argparser.side_effect = [stub_argparser]

        mock_configure_uploader.side_effect = [None]
        # mock the core code exiting
        stub_upload_exit = unittest.mock.MagicMock()
        stub_upload_exit.exit_code.side_effect = 0
        mock_batch_upload_single_entry.side_effect = [stub_upload_exit]

        cli.main()

        # ensure the configuration is called
        mock_configure_uploader.assert_called_once_with(stub_args_object)
        # Verify final call
        mock_batch_upload_single_entry.assert_called_once_with(stub_args_object.directory,
                                                               stub_args_object.force,
                                                               stub_args_object.upload_mode,
                                                               stub_args_object.continue_partial)
