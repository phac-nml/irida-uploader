from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
import requests
from requests import ConnectionError
from urllib.error import URLError
from os import path
from time import time, sleep
import sys
import subprocess
from http import HTTPStatus


class SetupIridaData:

    def __init__(self, base_url, user, password, branch, db_host, db_port):
        """
        :param base_url: url of the IRIDA instance's API
        :param user: default admin username
        :param password: default admin password
        :param branch: the github branch to run the integration tests on (e.g. 'master' or 'development')
        """

        # Login info
        self.base_url = base_url
        self.user = user
        self.password = password
        self.driver = None
        self.branch = branch

        # IRIDA info
        self.IRIDA_PASSWORD_ID = 'password_client'
        self.IRIDA_AUTH_CODE_ID = 'auth_code_client'
        self.IRIDA_USER = "admin"
        self.IRIDA_PASSWORD = "Password1!"  # new password

        # Database info
        self.DB_HOST = db_host
        self.DB_PORT = db_port
        self.DB_NAME = "irida_uploader_test"
        self.DB_USERNAME = "test"
        self.DB_PASSWORD = "test"
        self.DB_JDBC_URL = "jdbc:mysql://" + self.DB_HOST + ":" + self.DB_PORT + "/" + self.DB_NAME

        self.TIMEOUT = 600  # seconds

        self.IRIDA_DB_RESET = 'echo '\
            '"drop database if exists ' + self.DB_NAME + ';'\
            'create database ' + self.DB_NAME + ';'\
            '"| mysql -h ' + self.DB_HOST + ' -P ' + self.DB_PORT + ' -u test -ptest'

        root_dir = "tests_integration/tmp"
        output_files = "tests_integration/tmp/output-files"
        reference_file = "tests_integration/tmp/reference-files"
        sequence_files = "tests_integration/tmp/sequence-files"
        assembly_files = "tests_integration/tmp/assembly-files"

        self.IRIDA_CMD = ['mvn', 'clean', 'jetty:run', '--quiet',
                          '-Djdbc.url=' + self.DB_JDBC_URL,
                          '-Djdbc.username=' + self.DB_USERNAME, '-Djdbc.password=' + self.DB_PASSWORD,
                          '-Dliquibase.update.database.schema=true',
                          '-Dhibernate.hbm2ddl.auto=',
                          '-Dhibernate.hbm2ddl.import_files=',
                          '-Dirida.it.rootdirectory={}'.format(root_dir),
                          '-Dsequence.file.base.directory={}'.format(sequence_files),
                          '-Dreference.file.base.directory={}'.format(reference_file),
                          '-Doutput.file.base.directory={}'.format(output_files),
                          '-Dassembly.file.base.directory={}'.format(assembly_files)
                          ]

        self.IRIDA_STOP = 'mvn jetty:stop'

        self.PATH_TO_MODULE = path.dirname(__file__)
        if len(self.PATH_TO_MODULE) == 0:
            self.PATH_TO_MODULE = "."

        self.SCRIPT_FOLDER = path.join(self.PATH_TO_MODULE, "bash_scripts")
        self.INSTALL_IRIDA_EXEC = path.join(
            self.SCRIPT_FOLDER, "install_irida.sh")

        self.REPO_PATH = path.join(self.PATH_TO_MODULE, "repos")
        self.IRIDA_PATH = path.join(self.REPO_PATH, "irida")

    @contextmanager
    def wait_for_page_load(self, timeout=30):
        old_page = self.driver.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.driver, timeout).until(
            EC.staleness_of(old_page)
        )

    def install_irida(self):
        install_proc = subprocess.Popen(
            [self.INSTALL_IRIDA_EXEC, self.branch], cwd=self.PATH_TO_MODULE)
        proc_res = install_proc.wait()
        if proc_res == 1:  # failed to execute
            sys.exit(1)

    def reset_irida_db(self):
        db_reset_proc = subprocess.Popen(self.IRIDA_DB_RESET, shell=True)
        proc_res = db_reset_proc.wait()

        if proc_res == 1:  # failed to execute
            print("Unable to execute:\n {cmd}".format(cmd=self.IRIDA_DB_RESET))
            sys.exit(1)

    def run_irida(self):
        subprocess.Popen(
            self.IRIDA_CMD, cwd=self.IRIDA_PATH)
        self.wait_until_up()

    def wait_until_up(self):

        start_time = time()
        elapsed = 0
        status_code = -1
        print("Waiting for " + self.base_url)

        while status_code != HTTPStatus.OK and elapsed < self.TIMEOUT:
            try:
                status_code = requests.api.get(self.base_url).status_code
                elapsed = time() - start_time

            except (URLError, ConnectionError):
                sleep(10)

    def start_driver(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(30)

    def login(self):
        self.driver.get(self.base_url + "/login")
        self.driver.find_element_by_id("loginForm_username").clear()
        self.driver.find_element_by_id("loginForm_username").send_keys(self.user)
        self.driver.find_element_by_id("loginForm_password").clear()
        self.driver.find_element_by_id("loginForm_password").send_keys(self.password)
        with self.wait_for_page_load(timeout=10):
            self.driver.find_element_by_id("t-submit-btn").click()

    def set_new_admin_pw(self):
        self.driver.find_element_by_id("password").clear()
        self.driver.find_element_by_id(
            "password").send_keys(self.IRIDA_PASSWORD)
        self.driver.find_element_by_id("confirmPassword").clear()
        self.driver.find_element_by_id(
            "confirmPassword").send_keys(self.IRIDA_PASSWORD)
        with self.wait_for_page_load(timeout=100):
            xpath = "//button[@type='submit']"
            submit = self.driver.find_element_by_xpath(xpath)
            submit.click()

    def create_client(self):
        self.driver.get(self.base_url + "/clients/create")
        self.driver.find_element_by_id(
            "clientId").send_keys(self.IRIDA_AUTH_CODE_ID)

        self.driver.find_element_by_id("scope_write").click()  # for sending
        with self.wait_for_page_load(timeout=10):
            self.driver.find_element_by_id("create-client-submit").click()

    def get_irida_secret(self):

        self.driver.get(self.base_url + "/admin/clients")
        self.driver.find_element_by_xpath(
            "//*[contains(text(), '" + self.IRIDA_AUTH_CODE_ID + "')]").click()
        secret = self.driver.find_element_by_id(
            "client-secret").get_attribute("textContent")

        return secret

    def stop_irida(self):
        stopper = subprocess.Popen(
            self.IRIDA_STOP, cwd=self.IRIDA_PATH, shell=True)
        stopper.wait()

    def close_driver(self):
        self.driver.quit()
