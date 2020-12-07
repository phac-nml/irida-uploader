import unittest

from iridauploader.tests_integration.integration_data_setup import SetupIridaData
from iridauploader.tests_integration.test_api_integration import TestApiIntegration
from iridauploader.tests_integration.test_end_to_end import TestEndToEnd

# Modules level variables that can/will be changed when the setup starts
base_url = "http://localhost:8080/api"
username = "admin"
password = "password1"
client_id = ""
client_secret = ""


def irida_setup(setup):
    """
    Kicks off setting up irida,
    installs from github, resets the database, and runs it
    :param setup:
    :return:
    """
    setup.install_irida()
    setup.reset_irida_db()
    setup.run_irida()


def data_setup(setup):
    """
    Starts a webdriver that interacts with IRIDA to have it ready for api use
    :param setup:
    :return: user id and passwords needed to interact with the IRIDA instance
    """
    irida_setup(setup)

    setup.start_driver()
    setup.login()
    setup.set_new_admin_pw()
    setup.create_client()

    irida_secret = setup.get_irida_secret()
    setup.close_driver()

    return setup.IRIDA_AUTH_CODE_ID, irida_secret, setup.IRIDA_PASSWORD


def start_setup(branch, db_host, db_port):
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

    setup = SetupIridaData(
        base_url[:base_url.index("/api")], username, password, branch, db_host, db_port)

    client_id, client_secret, password = data_setup(setup)

    return setup


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

    setup_handler = start_setup(branch, db_host, db_port)

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
        setup_handler.stop_irida()

    return exit_code
