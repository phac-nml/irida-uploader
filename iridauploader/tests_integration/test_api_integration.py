import unittest
from os import path

from iridauploader.tests_integration import tests_integration

import iridauploader.api as api
import iridauploader.model as model


path_to_module = path.dirname(__file__)
if len(path_to_module) == 0:
    path_to_module = '.'


class TestApiIntegration(unittest.TestCase):

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        self.test_api = api.ApiCalls(
            client_id=tests_integration.client_id,
            client_secret=tests_integration.client_secret,
            base_url=tests_integration.base_url,
            username=tests_integration.username,
            password=tests_integration.password
        )

    def test_send_and_get_project(self):
        """
        Tests sending and receiving project data
        :return:
        """
        # try sending a project
        project_name = "test_project"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)

        json_res = self.test_api.send_project(project)

        # make sure the json response is what we expect it to be
        self.assertEqual(json_res['resource']['name'], project_name)
        self.assertEqual(json_res['resource']['projectDescription'], project_description)

        # get a list of all projects
        proj_list = self.test_api.get_projects()
        proj = proj_list[len(proj_list) - 1]

        # verify info matches what we uploaded
        self.assertEqual(type(proj), model.Project)
        self.assertEqual(proj.name, project_name)
        self.assertEqual(proj.description, project_description)

        # make sure identifiers match
        self.assertEqual(json_res['resource']['identifier'], str(len(proj_list)))
        self.assertEqual(json_res['resource']['identifier'], proj.id)

    def test_project_exists(self):
        """
        upload a project and check if project can be found with the projects_exists method
        :return:
        """
        project_name = "test_project_exists"
        project_description = "test_project_exists_description"
        project = model.Project(name=project_name, description=project_description)

        json_res = self.test_api.send_project(project)
        project_id = json_res['resource']['identifier']
        self.assertTrue(self.test_api.project_exists(project_id))

    def test_send_and_get_sample(self):
        """
        Tests sending and receiving sample data
        :return:
        """
        # set up a project to upload samples to
        project_name = "test_project_2"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)

        proj_json_res = self.test_api.send_project(project)
        project_identifier = proj_json_res['resource']['identifier']

        # upload a sample
        sample_name = "test_sample"
        sample_desc = "test_sample_desc"
        sample = model.Sample(sample_name, sample_desc)

        sample_json_res = self.test_api.send_sample(sample, project_identifier)

        # make sure the returned values match what we tried to upload
        self.assertEqual(sample_json_res['resource']['sampleName'], sample_name)
        self.assertEqual(sample_json_res['resource']['description'], sample_desc)

        # get a list of samples on our project and make sure they match what we uploaded
        sample_list = self.test_api.get_samples(project_identifier)

        self.assertEqual(len(sample_list), 1)
        self.assertEqual(type(sample_list[0]), model.Sample)
        self.assertEqual(sample_list[0].sample_name, sample_name)
        self.assertEqual(sample_list[0].description, sample_desc)

    def test_sample_exists(self):
        """
        Upload a sample and make sure it can be found with the sample_exists method
        :return:
        """
        # create a project to upload samples to
        project_name = "test_project_exists"
        project_description = "test_project_exists_description"
        project = model.Project(name=project_name, description=project_description)

        json_res = self.test_api.send_project(project)
        project_id = json_res['resource']['identifier']

        # create and upload a sample, and verify it exists
        sample_name = "test_sample_exists"
        sample_desc = "test_sample_exists_desc"
        sample = model.Sample(sample_name, sample_desc)

        self.test_api.send_sample(sample, project_id)
        self.assertTrue(self.test_api.sample_exists(sample_name, project_id))

    def test_send_and_get_sequence_files(self):
        """
        Tests sending and receiving sequence files
        :return:
        """
        # upload a project
        project_name = "test_project_2"
        project_description = "test_project_description"
        project = model.Project(name=project_name, description=project_description)

        proj_json_res = self.test_api.send_project(project)
        project_identifier = proj_json_res['resource']['identifier']

        # upload a sample
        sample_name = "test_sample"
        sample_desc = "test_sample_desc"
        sample = model.Sample(sample_name, sample_desc)

        self.test_api.send_sample(sample, project_identifier)

        # upload sequence files
        sequence_file_list = [
            path.join(path_to_module, "fake_dir_data", "file_1.fastq.gz"),
            path.join(path_to_module, "fake_dir_data", "file_2.fastq.gz")
        ]
        sequence_file = model.SequenceFile(sequence_file_list)

        upload_id = self.test_api.create_seq_run({'layoutType': 'PAIRED_END'}, 'miseq')

        self.test_api.send_sequence_files(sequence_file, sample_name, project_identifier, upload_id)

        # verify sequence files match what we sent to IRIDA
        returned_sequence_files = self.test_api.get_sequence_files(project_identifier, sample_name)

        self.assertEqual(returned_sequence_files[0]['fileName'], 'file_1.fastq.gz')
        self.assertEqual(returned_sequence_files[1]['fileName'], 'file_2.fastq.gz')

    def test_create_and_get_sequencing_runs(self):
        """
        Create a new sequencing run and verify it can be gotten back from IRIDA
        This test tests paired end runs
        :return:
        """
        # create a new paired end sequencing run on IRIDA
        run_id = self.test_api.create_seq_run({'layoutType': 'PAIRED_END'}, 'miseq')

        # get a list of all sequencing runs and verify out new one is there and matches
        response = self.test_api.get_seq_runs()

        seq_run = None
        for run in response:
            if run['identifier'] == run_id:
                seq_run = run

        self.assertIsNotNone(seq_run)

        self.assertEqual(seq_run['layoutType'], 'PAIRED_END')
        self.assertEqual(seq_run['uploadStatus'], 'UPLOADING')

    def test_create_and_get_sequencing_runs_single_end(self):
        """
        Create a new sequencing run and verify it can be gotten back from IRIDA
        This one tests single end runs
        :return:
        """
        # create a new paired end sequencing run on IRIDA
        run_id = self.test_api.create_seq_run({'layoutType': 'SINGLE_END'}, 'miseq')

        # get a list of all sequencing runs and verify out new one is there and matches
        response = self.test_api.get_seq_runs()

        seq_run = None
        for run in response:
            if run['identifier'] == run_id:
                seq_run = run

        self.assertIsNotNone(seq_run)

        self.assertEqual(seq_run['layoutType'], 'SINGLE_END')
        self.assertEqual(seq_run['uploadStatus'], 'UPLOADING')

    def test_set_sequencing_runs(self):
        """
        Tests the various set sequencing run methods
        :return:
        """
        def get_seq_run(run_identifier):
            response = self.test_api.get_seq_runs()

            s_run = None
            for run in response:
                if run['identifier'] == run_identifier:
                    s_run = run

            return s_run

        run_id = self.test_api.create_seq_run({'layoutType': 'PAIRED_END'}, 'miseq')

        seq_run = get_seq_run(run_id)

        # Starts off as uploading
        self.assertEqual(seq_run['uploadStatus'], 'UPLOADING')

        # Test Error, uploading, and error
        self.test_api.set_seq_run_error(run_id)
        seq_run = get_seq_run(run_id)
        self.assertEqual(seq_run['uploadStatus'], 'ERROR')

        self.test_api.set_seq_run_uploading(run_id)
        seq_run = get_seq_run(run_id)
        self.assertEqual(seq_run['uploadStatus'], 'UPLOADING')

        self.test_api.set_seq_run_complete(run_id)
        seq_run = get_seq_run(run_id)
        self.assertEqual(seq_run['uploadStatus'], 'COMPLETE')
