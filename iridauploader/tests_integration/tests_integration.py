"""
This file is responsible for managing the execution of an IRIDA instance and Test Suites
"""
import unittest

from iridauploader.tests_integration.integration_data_setup import SetupIridaData
from iridauploader.tests_integration.test_api_integration import TestApiIntegration
from iridauploader.tests_integration.test_end_to_end import TestEndToEnd

# Modules level variables that can/will be changed when the setup starts
base_url = "http://localhost:8080/api"
username = "jeff"
password = "password1"
client_id = "sequencerClient"
client_secret = "sequencerClientSecret"


def init_irida_setup(branch, db_host, db_port):
    """
    Initializes the Irida setup object
    :param branch: what branch from github to check out
    :param db_host: database host override
    :param db_port: database port override
    :return: SetupIridaData object
    """
    global base_url
    global username
    global password
    global client_id
    global client_secret

    return SetupIridaData(base_url[:base_url.index("/api")], username, password, branch, db_host, db_port)


def create_test_suite():
    """
    Finds all the integration tests and adds them to a test suite
    :return: unittest.TestSuite
    """
    suite = unittest.TestSuite()

    # Include all the classes that contain tests
    test_class_list = [
        TestApiIntegration,
        TestEndToEnd
    ]

    # for each class, find the tests and add them to the test suite
    for test_class in test_class_list:
        for class_method in [*test_class.__dict__]:
            if class_method.startswith("test_"):
                suite.addTest(test_class(class_method))

    return suite


def start(branch="master", db_host="localhost", db_port="3306"):
    """
    Start running the integration tests

    This is the entry point for the integration tests
    :param branch: what branch from github to check out
    :param db_host: database host override
    :param db_port: database port override
    :return:
    """
    exit_code = 0

    # create a handler to manage a headless IRIDA instance
    irida_handler = init_irida_setup(branch, db_host, db_port)
    # Install IRIDA packages
    irida_handler.install_irida()
    # Delete and recreate the database
    irida_handler.reset_irida_db()
    # Launch IRIDA
    # Note: This initializes the database tables
    # Note: This call waits until IRIDA is running
    irida_handler.run_irida()
    # Add data to database that the tests depend on
    irida_handler.update_irida_db()

    # Run tests
    try:
        full_suite = create_test_suite()

        runner = unittest.TextTestRunner()
        res = runner.run(full_suite)
        if not res.wasSuccessful():
            exit_code = 1
    except Exception as e:
        raise e
    finally:
        # Make sure IRIDA is stopped even when an exception is raised
        irida_handler.stop_irida()

    return exit_code
