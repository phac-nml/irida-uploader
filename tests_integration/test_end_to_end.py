import unittest
from os import path
import os

from tests_integration import tests_integration

import global_settings
import config
import api
import model
import progress

from core.cli_entry import validate_and_upload_single_entry


path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'

CLEANUP_DIRECTORY_LIST = [
    path.join(path_to_module, "fake_dir_data"),
    path.join(path_to_module, "fake_ngs_data"),
    path.join(path_to_module, "fake_ngs_data_force"),
    path.join(path_to_module, "fake_ngs_data_nonexistent_project"),
    path.join(path_to_module, "fake_ngs_data_parse_fail")
]


class TestEndToEnd(unittest.TestCase):
    """
    This class is for End to End tests

    It uses the single entry point for the CLI to make sure all parts of the program are working together correctly
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        # Set the config file to our test config, so that when the upload is run it grabs out config file correctly
        global_settings.config_file = path.join(path_to_module, "test_config.conf")
        config.setup()

    def tearDown(self):
        """
        Return the sample config file to blank after tests

        Deletes status file from data directories if they exist
        :return:
        """
        self.write_to_config_file("", "", "", "", "", "")

        for directory_path in CLEANUP_DIRECTORY_LIST:
            status_file_path = path.join(directory_path, 'irida_uploader_status.info')
            if path.exists(status_file_path):
                os.remove(status_file_path)
            log_file_path = path.join(directory_path, 'irida-uploader.log')
            if path.exists(log_file_path):
                os.remove(log_file_path)

    @staticmethod
    def write_to_config_file(client_id, client_secret, username, password, base_url, parser):
        """
        Write to out sample configuration file so that the IRIDA instance will be accessed
        :param client_id:
        :param client_secret:
        :param username:
        :param password:
        :param base_url:
        :param parser:
        :return:
        """
        config.write_config_option("client_id", client_id)
        config.write_config_option("client_secret", client_secret)
        config.write_config_option("username", username)
        config.write_config_option("password", password)
        config.write_config_option("base_url", base_url)
        config.write_config_option("parser", parser)

    def test_valid_miseq_upload(self):
        """
        Test a valid miseq directory for upload from end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq"
        )

        # instance an api
        test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

        # Create a test project, the uploader does not make new projects on its own
        # so one must exist to upload samples into
        # This may not be the project that the files get uploaded to,
        # but one will be made in the case this is the only test being run
        project_name = "test_project"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_ngs_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_found = False
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["01-1111", "02-2222", "03-3333"]:
                if sample.sample_name == "01-1111":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '01-1111_S1_L001_R1_001.fastq.gz',
                        '01-1111_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "02-2222":
                    sample_2_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '02-2222_S1_L001_R1_001.fastq.gz',
                        '02-2222_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "03-3333":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '03-3333_S1_L001_R1_001.fastq.gz',
                        '03-3333_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)
        self.assertEqual(sample_3_found, True)

    def test_valid_directory_upload(self):
        """
        Test a valid directory for upload end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="directory"
        )

        # instance an api
        test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

        # Create a test project, the uploader does not make new projects on its own
        # so one must exist to upload samples into
        # This may not be the project that the files get uploaded to,
        # but one will be made in the case this is the only test being run
        project_name = "test_project_2"
        project_description = "test_project_description_2"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_dir_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_found = False
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["my-sample-1", "my-sample-2", "my-sample-3"]:
                if sample.sample_name == "my-sample-1":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    self.assertEqual(sequence_files[0]['fileName'], 'file_1.fastq.gz')
                    self.assertEqual(sequence_files[1]['fileName'], 'file_2.fastq.gz')
                elif sample.sample_name == "my-sample-2":
                    sample_2_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    self.assertEqual(sequence_files[0]['fileName'], 'samp_F.fastq.gz')
                    self.assertEqual(sequence_files[1]['fileName'], 'samp_R.fastq.gz')
                elif sample.sample_name == "my-sample-3":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    self.assertEqual(sequence_files[0]['fileName'], 'germ_f.fastq.gz')
                    self.assertEqual(sequence_files[1]['fileName'], 'germ_r.fastq.gz')

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)
        self.assertEqual(sample_3_found, True)

    def test_upload_to_nonexistent_project(self):
        """
        Everything is correct except the sample sheet file specifies an invalid project
        Samples should not be uploaded
        :return:
        """
        # try to upload to a non existent project
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq"
        )

        # instance an api
        test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

        # Create a test project, the uploader does not make new projects on its own
        # so one must exist to upload samples into
        # This may not be the project that the files get uploaded to,
        # but one will be made in the case this is the only test being run
        project_name = "test_project"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)

        # Do the upload
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_ngs_data_nonexistent_project"))

        # Make sure the upload was a failure
        self.assertEqual(upload_result, 1)

        # Verify that the project does not exist
        project_id = "1000"
        with self.assertRaises(api.exceptions.IridaKeyError):
            test_api.get_samples(project_id)

    def test_upload_parse_fail(self):
        """
        Given an invalid sample sheet, make sure that the upload does not happen
        :return:
        """
        # try to upload to a non existent project
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq"
        )

        # instance an api
        test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

        # Create a test project, the uploader does not make new projects on its own
        # so one must exist to upload samples into
        # This may not be the project that the files get uploaded to,
        # but one will be made in the case this is the only test being run
        project_name = "test_project"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)

        # Do the upload
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_ngs_data_parse_fail"))

        # Make sure the upload was a failure
        self.assertEqual(upload_result, 1)

    def test_valid_miseq_with_status_file_force(self):
        """
        Test a valid miseq directory for upload from end to end
        We create a status file that indicates the files have already been uploaded,
        and then use the force option to upload anyways
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq"
        )

        # instance an api
        test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

        # Create a test project, the uploader does not make new projects on its own
        # so one must exist to upload samples into
        # This may not be the project that the files get uploaded to,
        # but one will be made in the case this is the only test being run
        project_name = "test_project_3"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Write a status file to the upload directory that we can force past
        progress.write_directory_status(directory=path.join(path_to_module, "fake_ngs_data_force"),
                                        status=progress.DIRECTORY_STATUS_COMPLETE)

        # Do the upload, with force option
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_ngs_data_force"), True)

        # Make sure the upload was a success
        self.assertEqual(upload_result, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_found = False
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["01-1111", "02-2222", "03-3333"]:
                if sample.sample_name == "01-1111":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '01-1111_S1_L001_R1_001.fastq.gz',
                        '01-1111_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "02-2222":
                    sample_2_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '02-2222_S1_L001_R1_001.fastq.gz',
                        '02-2222_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "03-3333":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '03-3333_S1_L001_R1_001.fastq.gz',
                        '03-3333_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)
        self.assertEqual(sample_3_found, True)

    def test_valid_miseq_with_status_file_already_uploaded(self):
        """
        Test a valid miseq directory for upload from end to end
        We create a status file that indicates the files have already been uploaded,
        Then make sure it does not upload
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq"
        )

        # Write a status file to the upload directory
        progress.write_directory_status(directory=path.join(path_to_module, "fake_ngs_data"),
                                        status=progress.DIRECTORY_STATUS_COMPLETE)

        # Do the upload, without force option
        upload_result = validate_and_upload_single_entry(path.join(path_to_module, "fake_ngs_data"), False)

        # Make sure the upload was a failure
        self.assertEqual(upload_result, 1)
