import unittest
from os import path
import os

from iridauploader.tests_integration import tests_integration

import iridauploader.config as config
import iridauploader.api as api
import iridauploader.model as model
import iridauploader.progress as progress

from iridauploader.core.upload import upload_run_single_entry, batch_upload_single_entry


path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'

CLEANUP_DIRECTORY_LIST = [
    path.join(path_to_module, "fake_dir_data"),
    path.join(path_to_module, "fake_miniseq_data"),
    path.join(path_to_module, "fake_nextseq_data"),
    path.join(path_to_module, "fake_nextseq2k_data"),
    path.join(path_to_module, "fake_ngs_data"),
    path.join(path_to_module, "fake_ngs_data_force"),
    path.join(path_to_module, "fake_ngs_data_nonexistent_project"),
    path.join(path_to_module, "fake_ngs_data_parse_fail"),
    path.join(path_to_module, "fake_ngs_data_no_completed_file"),
    path.join(path_to_module, "fake_fast5_data"),
    path.join(path_to_module, "fake_assemblies_data"),
    path.join(path_to_module, "fake_batch_data", "run_1"),
    path.join(path_to_module, "fake_batch_data", "run_2"),
    path.join(path_to_module, "fake_batch_data", "run_3")
]


class TestEndToEnd(unittest.TestCase):
    """
    This class is for End to End tests

    It uses the single entry point for the CLI to make sure all parts of the program are working together correctly
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        # Set the config file to our test config, so that when the upload is run it grabs out config file correctly
        config.set_config_file(path.join(path_to_module, "test_config.conf"))
        config.setup()

    def tearDown(self):
        """
        Return the sample config file to blank after tests

        Deletes status file from data directories if they exist
        :return:
        """
        self.write_to_config_file("", "", "", "", "", "", False)

        for directory_path in CLEANUP_DIRECTORY_LIST:
            status_file_path = path.join(directory_path, 'irida_uploader_status.info')
            if path.exists(status_file_path):
                os.remove(status_file_path)
            log_file_path = path.join(directory_path, 'irida-uploader.log')
            if path.exists(log_file_path):
                os.remove(log_file_path)

    @staticmethod
    def write_to_config_file(client_id, client_secret, username, password, base_url, parser, readonly):
        """
        Write to out sample configuration file so that the IRIDA instance will be accessed
        :param client_id:
        :param client_secret:
        :param username:
        :param password:
        :param base_url:
        :param parser:
        :param readonly:
        :return:
        """
        config.set_config_options(client_id=client_id,
                                  client_secret=client_secret,
                                  username=username,
                                  password=password,
                                  base_url=base_url,
                                  parser=parser,
                                  readonly=readonly)
        config.write_config_options_to_file()

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
            parser="miseq",
            readonly=False
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
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

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

    def test_batch_miseq_upload(self):
        """
        Test a valid miseq directory for upload from end to end
        We have 3 run directories
            run_1 has batch01-1111
            run_2 is invalid
            run_3 has batch03-3333
        we expect to see batch01-1111 and batch03-3333 uploaded
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq",
            readonly=False
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
        project_name = "test_batch_project"
        project_description = "test_batch_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = batch_upload_single_entry(path.join(path_to_module, "fake_batch_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_not_found = True
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["batch01-1111", "batch02-2222", "batch03-3333"]:
                if sample.sample_name == "batch01-1111":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        'batch01-1111_S1_L001_R1_001.fastq.gz',
                        'batch01-1111_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "batch02-2222":
                    # this one should not be found
                    sample_2_not_found = False
                elif sample.sample_name == "batch03-3333":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        'batch03-3333_S1_L001_R1_001.fastq.gz',
                        'batch03-3333_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_not_found, True)
        self.assertEqual(sample_3_found, True)

    def test_read_only_miseq_upload(self):
        """
        Test upload of a readonly miseq directory with readonly turned on
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq",
            readonly=True
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
        project_name = "test_read_only_project"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_read_only"),
                                                force_upload=False,
                                                upload_mode=api.MODE_DEFAULT)

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_found = False
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["R01-1111", "R02-2222", "R03-3333"]:
                if sample.sample_name == "R01-1111":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        'R01-1111_S1_L001_R1_001.fastq.gz',
                        'R01-1111_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "R02-2222":
                    sample_2_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        'R02-2222_S1_L001_R1_001.fastq.gz',
                        'R02-2222_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "R03-3333":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        'R03-3333_S1_L001_R1_001.fastq.gz',
                        'R03-3333_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)
        self.assertEqual(sample_3_found, True)

    def test_invalid_read_only_miseq_upload(self):
        """
        Test failing to upload a readonly miseq directory because readonly is turned off
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq",
            readonly=False
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
        project_name = "test_read_only_project_fail"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)

        # try the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_read_only"),
                                                force_upload=False,
                                                upload_mode=api.MODE_DEFAULT)

        # Make sure the upload was a failure
        self.assertEqual(upload_result.exit_code, 1)

    def test_continue_partial_miseq_upload(self):
        """
        We set sample 2 to be already uploaded, when we verify uploads at the bottom it should be missing from the 3
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="miseq",
            readonly=True
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
        project_name = "test_project_continue_partial"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # We must set the sequencing_run_id 1 on IRIDA to uploading
        # This is because we aren't actually uploading a partially uploaded run with an existing run_id
        # If we try to upload to the already completed run_id, we will get our upload rejected
        test_api.set_seq_run_uploading(1)

        # Do the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_continue_partial"),
                                                continue_upload=True)

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        for sample in sample_list:
            if sample.sample_name in ["01thread", "02thread", "03thread"]:
                if sample.sample_name == "01thread":
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '01thread_S1_L001_R1_001.fastq.gz',
                        '01thread_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "02thread":
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    # This one is 0 because we didn't actually upload them
                    self.assertEqual(len(sequence_files), 0)
                elif sample.sample_name == "03thread":
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '03thread_S1_L001_R1_001.fastq.gz',
                        '03thread_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

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
            parser="directory",
            readonly=False
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
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_dir_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

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

    def test_valid_assemblies_directory_upload(self):
        """
        Test a valid directory of assemblies for upload end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="directory",
            readonly="False"
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
        project_name = "test_project_assemblies"
        project_description = "test_project_description_assemblies"
        sample_name = "my-sample-1"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = upload_run_single_entry(directory=path.join(path_to_module, "fake_assemblies_data"),
                                                force_upload=True,
                                                upload_mode=api.MODE_ASSEMBLIES)

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sequence_files = test_api.get_assemblies_files(project_id, sample_name)
        self.assertEqual(len(sequence_files), 1)
        self.assertEqual(sequence_files[0]['fileName'], 'file_1.fasta')

    def test_valid_fast5_directory_upload(self):
        """
        Test a valid directory of fast5 for upload end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="directory",
            readonly="False"
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
        project_name = "test_project_fast5"
        project_description = "test_project_description_fast5"
        sample_name = "my-sample-1"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = upload_run_single_entry(directory=path.join(path_to_module, "fake_fast5_data"),
                                                force_upload=True,
                                                upload_mode=api.MODE_FAST5)

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sequence_files = test_api.get_fast5_files(project_id, sample_name)
        self.assertEqual(len(sequence_files), 1)
        self.assertEqual(sequence_files[0]['file']['fileName'], 'file_1.fast5')

    def test_valid_miniseq_upload(self):
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
            parser="miniseq",
            readonly=False
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
        project_name = "test_project_4"
        project_description = "test_project_description_4"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id = "1"

        # Do the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_miniseq_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list = test_api.get_samples(project_id)

        sample_1_found = False
        sample_2_found = False
        sample_3_found = False

        for sample in sample_list:
            if sample.sample_name in ["01-1111m", "02-2222m", "03-3333m"]:
                if sample.sample_name == "01-1111m":
                    sample_1_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '01-1111m_S1_L001_R1_001.fastq.gz',
                        '01-1111m_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "02-2222m":
                    sample_2_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '02-2222m_S1_L001_R1_001.fastq.gz',
                        '02-2222m_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())
                elif sample.sample_name == "03-3333m":
                    sample_3_found = True
                    sequence_files = test_api.get_sequence_files(project_id, sample.sample_name)
                    self.assertEqual(len(sequence_files), 2)
                    res_sequence_file_names = [
                        sequence_files[0]['fileName'],
                        sequence_files[1]['fileName']
                    ]
                    expected_sequence_file_names = [
                        '03-3333m_S1_L001_R1_001.fastq.gz',
                        '03-3333m_S1_L001_R2_001.fastq.gz'
                    ]
                    self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)
        self.assertEqual(sample_3_found, True)

    def test_valid_nextseq_upload(self):
        """
        Test a valid nextseq directory for upload from end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="nextseq",
            readonly=False
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
        project_name = "test_project_nextseq"
        project_description = "test_project_description_nextseq"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id_1 = "1"

        # we are uploading 2 projects, so create another one
        project_name_2 = "test_project_nextseq_2"
        project_description_2 = "test_project_description_nextseq_2"
        project_2 = model.Project(name=project_name_2, description=project_description_2)
        test_api.send_project(project_2)
        project_id_2 = "2"

        # Do the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_nextseq_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list_1 = test_api.get_samples(project_id_1)
        sample_list_2 = test_api.get_samples(project_id_2)

        sample_1_found = False
        sample_2_found = False

        for sample in sample_list_1:
            if sample.sample_name == "SA20121712":
                sample_1_found = True
                sequence_files = test_api.get_sequence_files(project_id_1, sample.sample_name)
                self.assertEqual(len(sequence_files), 2)
                res_sequence_file_names = [
                    sequence_files[0]['fileName'],
                    sequence_files[1]['fileName']
                ]
                expected_sequence_file_names = [
                    'SA20121712_S2_R1_001.fastq.qz',
                    'SA20121712_S2_R2_001.fastq.qz'
                ]
                self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        for sample in sample_list_2:
            if sample.sample_name == "SA20121716":
                sample_2_found = True
                sequence_files = test_api.get_sequence_files(project_id_2, sample.sample_name)
                self.assertEqual(len(sequence_files), 2)
                res_sequence_file_names = [
                    sequence_files[0]['fileName'],
                    sequence_files[1]['fileName']
                ]
                expected_sequence_file_names = [
                    'SA20121716_S1_R1_001.fastq.qz',
                    'SA20121716_S1_R2_001.fastq.qz'
                ]
                self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)

    def test_valid_nextseq2k_upload(self):
        """
        Test a valid nextseq2k directory for upload from end to end
        :return:
        """
        # Set our sample config file to use miseq parser and the correct irida credentials
        self.write_to_config_file(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            username=tests_integration.username,
            password=tests_integration.password,
            base_url=tests_integration.base_url,
            parser="nextseq2k_nml",
            readonly=False
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
        project_name = "test_project_nextseq2k"
        project_description = "test_project_description_nextseq2k"
        project = model.Project(name=project_name, description=project_description)
        test_api.send_project(project)
        # We always upload to project "1" so that tests will be consistent no matter how many / which tests are run
        project_id_1 = "1"

        # we are uploading 2 projects, so create another one
        project_name_2 = "test_project_nextseq2k_2"
        project_description_2 = "test_project_description_nextseq2k_2"
        project_2 = model.Project(name=project_name_2, description=project_description_2)
        test_api.send_project(project_2)
        project_id_2 = "2"

        # Do the upload
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_nextseq2k_data"))

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

        # Verify the files were uploaded
        sample_list_1 = test_api.get_samples(project_id_1)
        sample_list_2 = test_api.get_samples(project_id_2)

        sample_1_found = False
        sample_2_found = False

        for sample in sample_list_1:
            if sample.sample_name == "01A100001":
                sample_1_found = True
                sequence_files = test_api.get_sequence_files(project_id_1, sample.sample_name)
                self.assertEqual(len(sequence_files), 2)
                res_sequence_file_names = [
                    sequence_files[0]['fileName'],
                    sequence_files[1]['fileName']
                ]
                expected_sequence_file_names = [
                    '01A100001_S1_L001_R1_001.fastq.gz',
                    '01A100001_S1_L001_R2_001.fastq.gz'
                ]
                self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        for sample in sample_list_2:
            if sample.sample_name == "01A100002":
                sample_2_found = True
                sequence_files = test_api.get_sequence_files(project_id_2, sample.sample_name)
                self.assertEqual(len(sequence_files), 2)
                res_sequence_file_names = [
                    sequence_files[0]['fileName'],
                    sequence_files[1]['fileName']
                ]
                expected_sequence_file_names = [
                    '01A100002_S1_L001_R1_001.fastq.gz',
                    '01A100002_S1_L001_R2_001.fastq.gz'
                ]
                self.assertEqual(res_sequence_file_names.sort(), expected_sequence_file_names.sort())

        self.assertEqual(sample_1_found, True)
        self.assertEqual(sample_2_found, True)

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
            parser="miseq",
            readonly=False
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
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_nonexistent_project"))

        # Make sure the upload was a failure
        self.assertEqual(upload_result.exit_code, 1)

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
            parser="miseq",
            readonly=False
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
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_parse_fail"))

        # Make sure the upload was a failure
        self.assertEqual(upload_result.exit_code, 1)

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
            parser="miseq",
            readonly=False
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
        directory_status = model.DirectoryStatus(directory=path.join(path_to_module, "fake_ngs_data_force"))
        directory_status.status = model.DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status)

        # Do the upload, with force option
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_force"), True)

        # Make sure the upload was a success
        self.assertEqual(upload_result.exit_code, 0)

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
            parser="miseq",
            readonly=False
        )

        # Write a status file to the upload directory
        directory_status = model.DirectoryStatus(directory=path.join(path_to_module, "fake_ngs_data"))
        directory_status.status = model.DirectoryStatus.COMPLETE
        progress.write_directory_status(directory_status)

        # Do the upload, without force option
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data"), False)

        # Make sure the upload was a failure
        self.assertEqual(upload_result.exit_code, 1)

    def test_invalid_miseq_no_completed_file(self):
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
            parser="miseq",
            readonly=False
        )

        # Do the upload, without force option
        upload_result = upload_run_single_entry(path.join(path_to_module, "fake_ngs_data_no_completed_file"), False)

        # Make sure the upload was a failure
        self.assertEqual(upload_result.exit_code, 1)
