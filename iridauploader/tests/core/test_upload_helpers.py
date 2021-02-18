import unittest
from unittest.mock import patch, MagicMock
from os import path

from iridauploader.api import UPLOAD_MODES, MODE_DEFAULT, MODE_FAST5, MODE_ASSEMBLIES
from iridauploader.core import upload_helpers
from iridauploader.model import DirectoryStatus, SequencingRun, Project, Sample
from iridauploader import progress
from iridauploader import parsers
from iridauploader.api.exceptions import FileError, IridaResourceError, IridaConnectionError

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestSetAndWriteDirectoryStatus(unittest.TestCase):
    """
    Tests core.upload_helpers._set_and_write_directory_status
    """

    class StubDirectoryStatus:
        status = None
        message = ""

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers.progress")
    def test_valid_write(self, mock_progress):
        """
        Tessts a valid write attempt
        :param mock_progress:
        :return:
        """
        mock_status = "status"
        mock_message = "message"
        stub_dir_status = self.StubDirectoryStatus()
        # mock main call to test
        mock_progress.write_directory_status.side_effect = [None]
        # run function
        upload_helpers._set_and_write_directory_status(stub_dir_status, mock_status, mock_message)
        # verify write
        mock_progress.write_directory_status.assert_called_with(stub_dir_status)

    @patch("iridauploader.core.upload_helpers.progress.write_directory_status")
    def test_invalid_write(self, mock_progress):
        """
        Tessts a valid write attempt
        :param mock_progress:
        :return:
        """
        mock_status = "status"
        mock_message = "message"
        stub_dir_status = self.StubDirectoryStatus()
        # mock main call to test
        mock_progress.side_effect = progress.exceptions.DirectoryError("", "")
        # run function
        with self.assertRaises(progress.exceptions.DirectoryError):
            upload_helpers._set_and_write_directory_status(stub_dir_status, mock_status, mock_message)


class TestDirectoryHasReadonlyConflict(unittest.TestCase):
    """
    Tests core.upload_helpers.directory_has_readonly_conflict
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("os.access")
    @patch("iridauploader.core.upload_helpers.config")
    def test_case_matrix(self, mock_config, mock_access):
        """
        Tests all possible cases for readonly config and access response
        :param mock_config:
        :param mock_access:
        :return:
        """
        # Matrix of tests
        # config:  T  F
        # access
        # T        X  X
        # F        X  O
        mock_config.read_config_option.side_effect = [
            True, True, False, False
        ]
        mock_access.side_effect = [
            True, False, True, False
        ]

        self.assertEqual(False, upload_helpers.directory_has_readonly_conflict(""))
        self.assertEqual(False, upload_helpers.directory_has_readonly_conflict(""))
        self.assertEqual(False, upload_helpers.directory_has_readonly_conflict(""))
        self.assertEqual(True, upload_helpers.directory_has_readonly_conflict(""))


class TestParseAndValidate(unittest.TestCase):
    """
    Tests core.upload_helpers.parse_and_validate
    """

    class StubDirectoryStatus:
        directory = "dir"

        def get_sample_status_list(self):
            return ['item']

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.parsing_handler")
    def test_valid_parse(self, mock_parsing_handler, mock_set_and_write):
        """
        verifies parse and validate was called,
        and _set_and_write_directory_status is called once with PARTIAL
        :param mock_parsing_handler:
        :param mock_set_and_write:
        :return:
        """
        stub_directory_status = self.StubDirectoryStatus()
        mock_parsing_handler.parse_and_validate.side_effect = ["return_value"]
        mock_set_and_write.side_effect = [True]

        self.assertEqual("return_value", upload_helpers.parse_and_validate(
            directory_status=stub_directory_status, parse_as_partial=False))

        mock_parsing_handler.parse_and_validate.assert_called_with(stub_directory_status.directory)
        mock_set_and_write.assert_called_with(stub_directory_status, DirectoryStatus.PARTIAL)

    @patch("iridauploader.core.upload_helpers.set_uploaded_samples_to_skip")
    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.parsing_handler")
    def test_valid_partial_parse(self, mock_parsing_handler, mock_set_and_write, mock_set_uploaded_samples_to_skip):
        """
        verifies parse and validate was called,
        and _set_and_write_directory_status is called once with PARTIAL
        :param mock_parsing_handler:
        :param mock_set_and_write:
        :return:
        """
        stub_directory_status = self.StubDirectoryStatus()
        mock_parsing_handler.parse_and_validate.side_effect = ["return_value"]
        mock_set_and_write.side_effect = [True]
        mock_set_uploaded_samples_to_skip.side_effect = ["modified_return_value"]

        self.assertEqual("modified_return_value", upload_helpers.parse_and_validate(
            directory_status=stub_directory_status, parse_as_partial=True))

        mock_parsing_handler.parse_and_validate.assert_called_with(stub_directory_status.directory)
        mock_set_and_write.assert_called_with(stub_directory_status, DirectoryStatus.PARTIAL)
        mock_set_uploaded_samples_to_skip.assert_called_with("return_value",
                                                             stub_directory_status.get_sample_status_list())

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.parsing_handler")
    def test_invalid_directory(self, mock_parsing_handler, mock_set_and_write):
        """
        verifies parse and validate was called, throwing DirectoryError
        and _set_and_write_directory_status is called with ERROR
        :param mock_parsing_handler:
        :param mock_set_and_write:
        :return:
        """
        stub_directory_status = self.StubDirectoryStatus()
        mock_parsing_handler.parse_and_validate.side_effect = [parsers.exceptions.DirectoryError("", "")]
        mock_set_and_write.side_effect = [True, True]

        with self.assertRaises(parsers.exceptions.DirectoryError):
            upload_helpers.parse_and_validate(directory_status=stub_directory_status, parse_as_partial=False)

        mock_parsing_handler.parse_and_validate.assert_called_with(stub_directory_status.directory)
        mock_set_and_write.assert_called_with(stub_directory_status, DirectoryStatus.ERROR,
                                              "ERROR! An error occurred with directory '', with message: ")

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.parsing_handler")
    def test_invalid_validation(self, mock_parsing_handler, mock_set_and_write):
        """
        verifies parse and validate was called, throwing ValidationError
        and _set_and_write_directory_status is called with ERROR
        :param mock_parsing_handler:
        :param mock_set_and_write:
        :return:
        """

        class StubValidationResult:
            error_list = []

        stub_validation_result = StubValidationResult()
        stub_directory_status = self.StubDirectoryStatus()
        mock_parsing_handler.parse_and_validate.side_effect = [parsers.exceptions.ValidationError(
            "",
            stub_validation_result)]
        mock_set_and_write.side_effect = [True, True]

        with self.assertRaises(parsers.exceptions.ValidationError):
            upload_helpers.parse_and_validate(directory_status=stub_directory_status, parse_as_partial=False)

        mock_parsing_handler.parse_and_validate.assert_called_with(stub_directory_status.directory)
        mock_set_and_write.assert_called_with(stub_directory_status, DirectoryStatus.ERROR,
                                              'ERROR! Errors occurred during validation with message: , Error list: []')


class TestSetUploadedSamplesToSkip(unittest.TestCase):
    """
    Tests core.upload_helpers.set_uploaded_samples_to_skip
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_remove_one(self):
        """
        Test setting a single sample to skip in a project

        :return:
        """
        seq_run = SequencingRun(None, sequencing_run_type="test",
                                project_list=[
                                    Project(sample_list=[
                                        Sample("one"),
                                        Sample("two"),
                                        Sample("three")
                                    ], id=1)
                                ])
        sample_status_list = [DirectoryStatus.SampleStatus(sample_name="one", project_id="1", uploaded=False),
                              DirectoryStatus.SampleStatus(sample_name="two", project_id="1", uploaded=True),
                              DirectoryStatus.SampleStatus(sample_name="three", project_id="1", uploaded=False)]

        res = upload_helpers.set_uploaded_samples_to_skip(seq_run, sample_status_list)

        res_samples = res.project_list[0].sample_list
        self.assertEqual(res_samples[0].skip, False)
        self.assertEqual(res_samples[1].skip, True)
        self.assertEqual(res_samples[2].skip, False)


class TestVerifyUploadMode(unittest.TestCase):
    """
    Tests core.upload_helpers.verify_upload_mode
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    def test_valid_upload_modes(self):
        """
        No exceptions being thrown means it is working as intended
        :return:
        """
        upload_helpers.verify_upload_mode(MODE_DEFAULT)
        upload_helpers.verify_upload_mode(MODE_FAST5)
        upload_helpers.verify_upload_mode(MODE_ASSEMBLIES)

    def test_invalid_upload_mode(self):
        """
        verify exception is thrown
        :return:
        """
        # verify mode doesn't exist

        mode = "invalid_mode"
        self.assertFalse(mode in UPLOAD_MODES)

        with self.assertRaises(Exception):
            upload_helpers.verify_upload_mode(mode)


class TestInitFileStatusListFromSequencingRun(unittest.TestCase):
    """
    Tests core.upload_helpers.init_file_status_list_from_sequencing_run
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    def test_all_functions_called(self, mock_set_and_write):
        """
        verifies all functions are called, and _set_and_write_directory_status is DirectoryStatus.PARTIAL
        :param mock_set_and_write:
        :return:
        """
        mock_dir_status = MagicMock()
        mock_dir_status.init_file_status_list_from_sequencing_run.side_effect = [True]
        mock_set_and_write.side_effect = [True]

        upload_helpers.init_file_status_list_from_sequencing_run("seqrun", mock_dir_status)

        mock_dir_status.init_file_status_list_from_sequencing_run.assert_called_with("seqrun")


class TestInitializeApi(unittest.TestCase):
    """
    Tests core.upload_helpers.initialize_api
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_valid_init(self, mock_api_handler, mock_set_and_write):
        """
        verifies init was called, and _set_and_write_directory_status was not called
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.initialize_api_from_config.side_effect = [True]
        mock_set_and_write.side_effect = [True]

        upload_helpers.initialize_api(directory_status='status')

        mock_api_handler.initialize_api_from_config.assert_called_with()
        mock_set_and_write.assert_not_called()

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_init(self, mock_api_handler, mock_set_and_write):
        """
        verifies init was called, and because of error, _set_and_write_directory_status is DirectoryStatus.ERROR
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.initialize_api_from_config.side_effect = [IridaConnectionError]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(IridaConnectionError):
            upload_helpers.initialize_api(directory_status='status')

        mock_api_handler.initialize_api_from_config.assert_called_with()

        mock_set_and_write.assert_called_with("status", DirectoryStatus.ERROR,
                                              'ERROR! Could not initialize irida api. Errors: ()')


class TestIridaPrepAndValidation(unittest.TestCase):
    """
    Tests core.upload_helpers.irida_prep_and_validation
    """

    class StubValidationResult:
        valid = True
        error_list = []

        def is_valid(self):
            return self.valid

        @staticmethod
        def error_count():
            return 0

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_valid_prep_and_validation(self, mock_api_handler, mock_set_and_write):
        """
        verifies prep_and_validation was called, and _set_and_write_directory_status was not called
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        stub_validation_result = self.StubValidationResult()
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [stub_validation_result]
        mock_set_and_write.side_effect = [True]

        upload_helpers.irida_prep_and_validation("seqrun", "")

        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("seqrun")
        mock_set_and_write.assert_not_called()

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_connection(self, mock_api_handler, mock_set_and_write):
        """
        verifies prep_and_validation was called,
        and _set_and_write_directory_status was called with ERROR
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [IridaConnectionError]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(IridaConnectionError):
            upload_helpers.irida_prep_and_validation("seqrun", "")

        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("seqrun")
        mock_set_and_write.assert_called_with("", DirectoryStatus.ERROR, 'Lost connection to Irida. Errors: ()')

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_validation(self, mock_api_handler, mock_set_and_write):
        """
        verifies prep_and_validation was called,
        and _set_and_write_directory_status was called with ERROR
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        stub_validation_result = self.StubValidationResult()
        stub_validation_result.valid = False
        mock_api_handler.prepare_and_validate_for_upload.side_effect = [stub_validation_result]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(Exception):
            upload_helpers.irida_prep_and_validation("seqrun", "")

        mock_api_handler.prepare_and_validate_for_upload.assert_called_with("seqrun")
        mock_set_and_write.assert_called_with("", DirectoryStatus.ERROR,
                                              'Sequencing run can not be uploaded, Errors: []')


class TestUploadSequencingRun(unittest.TestCase):
    """
    Tests core.upload_helpers.upload_sequencing_run
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_valid_upload(self, mock_api_handler, mock_set_and_write):
        """
        verifies upload was called, and _set_and_write_directory_status is DirectoryStatus.COMPLETE
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.upload_sequencing_run.side_effect = [True]
        mock_set_and_write.side_effect = [True]

        upload_helpers.upload_sequencing_run(directory_status='status',
                                             sequencing_run='run',
                                             upload_mode='mode')

        mock_api_handler.upload_sequencing_run.assert_called_with(directory_status='status',
                                                                  sequencing_run='run',
                                                                  upload_mode='mode',
                                                                  run_id=None)
        mock_set_and_write.assert_called_with("status", DirectoryStatus.COMPLETE)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_valid_partial_upload(self, mock_api_handler, mock_set_and_write):
        """
        verifies upload was called, and _set_and_write_directory_status is DirectoryStatus.COMPLETE
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """

        class MockDirStatus:
            run_id = 1

        mock_api_handler.upload_sequencing_run.side_effect = [True]
        mock_set_and_write.side_effect = [True]
        mock_directory_status = MockDirStatus()

        upload_helpers.upload_sequencing_run(directory_status=mock_directory_status,
                                             sequencing_run='run',
                                             upload_mode='mode',
                                             upload_from_partial=True)

        mock_api_handler.upload_sequencing_run.assert_called_with(directory_status=mock_directory_status,
                                                                  sequencing_run='run',
                                                                  upload_mode='mode',
                                                                  run_id=1)
        mock_set_and_write.assert_called_with(mock_directory_status, DirectoryStatus.COMPLETE)

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_connection(self, mock_api_handler, mock_set_and_write):
        """
        tests catching and raising IridaConnectionError
        and _set_and_write_directory_status is DirectoryStatus.COMPLETE
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.upload_sequencing_run.side_effect = [IridaConnectionError]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(IridaConnectionError):
            upload_helpers.upload_sequencing_run(directory_status='status',
                                                 sequencing_run='run',
                                                 upload_mode='mode')

        mock_api_handler.upload_sequencing_run.assert_called_with(directory_status='status',
                                                                  sequencing_run='run',
                                                                  upload_mode='mode',
                                                                  run_id=None)
        mock_set_and_write.assert_called_with("status", DirectoryStatus.ERROR, 'Lost connection to Irida. Errors: ()')

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_resource(self, mock_api_handler, mock_set_and_write):
        """
        tests catching and raising IridaResourceError
        and _set_and_write_directory_status is DirectoryStatus.COMPLETE
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.upload_sequencing_run.side_effect = [IridaResourceError("")]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(IridaResourceError):
            upload_helpers.upload_sequencing_run(directory_status='status',
                                                 sequencing_run='run',
                                                 upload_mode='mode')

        mock_api_handler.upload_sequencing_run.assert_called_with(directory_status='status',
                                                                  sequencing_run='run',
                                                                  upload_mode='mode',
                                                                  run_id=None)
        mock_set_and_write.assert_called_with("status", DirectoryStatus.ERROR,
                                              "Could not access IRIDA resource Errors: ('',)")

    @patch("iridauploader.core.upload_helpers._set_and_write_directory_status")
    @patch("iridauploader.core.upload_helpers.api_handler")
    def test_invalid_file(self, mock_api_handler, mock_set_and_write):
        """
        tests catching and raising FileError
        and _set_and_write_directory_status is DirectoryStatus.COMPLETE
        :param mock_api_handler:
        :param mock_set_and_write:
        :return:
        """
        mock_api_handler.upload_sequencing_run.side_effect = [FileError]
        mock_set_and_write.side_effect = [True]

        with self.assertRaises(FileError):
            upload_helpers.upload_sequencing_run(directory_status='status',
                                                 sequencing_run='run',
                                                 upload_mode='mode')

        mock_api_handler.upload_sequencing_run.assert_called_with(directory_status='status',
                                                                  sequencing_run='run',
                                                                  upload_mode='mode',
                                                                  run_id=None)
        mock_set_and_write.assert_called_with("status", DirectoryStatus.ERROR,
                                              'Could not upload file to IRIDA. Errors: ()')
