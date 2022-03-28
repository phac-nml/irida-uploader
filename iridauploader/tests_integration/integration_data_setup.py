"""
This file is responsible for Managing an IRIDA instance, including all the parameters associated with testing and
database management.
"""
import requests
from requests import ConnectionError
from urllib.error import URLError
from os import path
from time import time, sleep
import sys
import subprocess
from http import HTTPStatus
from pathlib import Path


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
        self.branch = branch

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

        root_dir = Path(__file__).parent.absolute()
        sql_file = Path(root_dir, "create_sequencer_client.sql")
        output_files = Path(root_dir, "tmp", "output-files")
        reference_file = Path(root_dir, "tmp", "reference-files")
        sequence_files = Path(root_dir, "tmp", "sequence-files")
        assembly_files = Path(root_dir, "tmp", "assembly-files")

        self.IRIDA_DB_UPDATE = 'mysql -h ' + self.DB_HOST + ' -P ' + self.DB_PORT + ' -u test -ptest ' + \
                               self.DB_NAME + ' < {}'.format(sql_file)

        self.IRIDA_CMD = \
            'mvn clean compile spring-boot:start -DskipTests --quiet ' +\
            '-Dspring-boot.run.arguments=\"' +\
            '--spring.datasource.url={} '.format(self.DB_JDBC_URL) +\
            '--spring.datasource.username={} '.format(self.DB_USERNAME) +\
            '--spring.datasource.password={} '.format(self.DB_PASSWORD) +\
            '--liquibase.update.database.schema=true ' +\
            '--spring.jpa.hibernate.ddl-auto= ' +\
            '--spring.jpa.properties.hibernate.hbm2ddl.import_files= ' +\
            '--sequence.file.base.directory={} '.format(sequence_files) +\
            '--reference.file.base.directory={} '.format(reference_file) +\
            '--output.file.base.directory={} '.format(output_files) +\
            '--assembly.file.base.directory={} '.format(assembly_files) +\
            '--logging.pattern.console=' +\
            '\"'

        self.IRIDA_STOP = 'mvn spring-boot:stop'

        self.PATH_TO_MODULE = path.dirname(__file__)
        if len(self.PATH_TO_MODULE) == 0:
            self.PATH_TO_MODULE = "."

        self.SCRIPT_FOLDER = path.join(self.PATH_TO_MODULE, "bash_scripts")
        self.INSTALL_IRIDA_EXEC = path.join(
            self.SCRIPT_FOLDER, "install_irida.sh")

        self.REPO_PATH = path.join(self.PATH_TO_MODULE, "repos")
        self.IRIDA_PATH = path.join(self.REPO_PATH, "irida")

    def install_irida(self):
        """
        Installs IRIDA
        :return:
        """
        install_proc = subprocess.Popen(
            [self.INSTALL_IRIDA_EXEC, self.branch], cwd=self.PATH_TO_MODULE)
        proc_res = install_proc.wait()
        if proc_res == 1:  # failed to execute
            sys.exit(1)

    def reset_irida_db(self):
        """
        Deletes the database and creates a new empty one
        :return:
        """
        db_reset_proc = subprocess.Popen(self.IRIDA_DB_RESET, shell=True)
        proc_res = db_reset_proc.wait()

        if proc_res == 1:  # failed to execute
            print("Unable to execute:\n {cmd}".format(cmd=self.IRIDA_DB_RESET))
            sys.exit(1)

    def update_irida_db(self):
        """
        Adds a user and a client for api operations to IRIDA database
        :return:
        """
        db_update_proc = subprocess.Popen(self.IRIDA_DB_UPDATE, shell=True)
        proc_res = db_update_proc.wait()

        if proc_res == 1:  # failed to execute
            print("Unable to execute:\n {cmd}".format(cmd=self.IRIDA_DB_UPDATE))
            sys.exit(1)

    def run_irida(self):
        """
        Runs IRIDA with first initialization
        Waits until IRIDA is up to return
        :return:
        """
        subprocess.Popen(
            self.IRIDA_CMD, cwd=self.IRIDA_PATH, shell=True)
        self._wait_until_up()

    def _wait_until_up(self):
        """
        Queries IRIDA until it responds with HTTP 200
        :return:
        """
        start_time = time()
        elapsed = 0
        status_code = -1
        print("Waiting for " + self.base_url)

        while status_code != HTTPStatus.OK and elapsed < self.TIMEOUT:
            try:
                print("Trying to connect...")
                status_code = requests.api.get(self.base_url).status_code
                elapsed = time() - start_time

            except (URLError, ConnectionError):
                sleep(10)
        print("Connected.")

    def stop_irida(self):
        """
        Stops the IRIDA mvn process
        This will sometimes dump errors into the log, but it is harmless
        :return:
        """
        stopper = subprocess.Popen(
            self.IRIDA_STOP, cwd=self.IRIDA_PATH, shell=True)
        stopper.wait()
