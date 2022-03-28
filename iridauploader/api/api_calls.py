import ast
import json
import logging
import threading

from http import HTTPStatus
from pathlib import Path
from rauth import OAuth2Service
from requests import ConnectionError
from requests.adapters import HTTPAdapter
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from urllib.parse import urljoin, urlparse
from urllib.error import URLError

import iridauploader.model as model
# For a truly independent api module, we should have a signal, or pubsub system in the module, that the progress module
# can subscribe to. That way, the api module is seperate, and other applications could use the emits/messages in their
# own setups.
import iridauploader.progress as progress

from . import exceptions

# These strings are used to determine which upload mode is being used when uploading sequence files
# They are included in the `api` __init__.py s.t. they can be used by the other modules without interacting with the
# api layer
MODE_DEFAULT = "default"
MODE_ASSEMBLIES = "assemblies"
MODE_FAST5 = "fast5"

UPLOAD_MODES = [
    MODE_DEFAULT,
    MODE_ASSEMBLIES,
    MODE_FAST5
]

# Timeout values for sequence file data upload
# Wait at least 1 second for each mb of data
TIMEOUT_BYTES_TO_MB_DIVISOR = 1024 * 1024
# 20 minute minimum timeout
TIMEOUT_MINIMUM = 1200

SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/71.1.2222.33 Safari/537.36",
    "Accept-Encoding": "*",
    "Connection": "keep-alive"
}

JSON_HEADERS = {"headers": {'Content-Type': 'application/json', **SESSION_HEADERS}}


class ApiCalls(object):

    def __init__(self, client_id, client_secret,
                 base_url, username, password, timeout_multiplier=10, max_wait_time=20, http_max_retries=5):
        """
        Create OAuth2Session and store it

        arguments:
            client_id -- client_id for creating access token.
            client_secret -- client_secret for creating access token.
            base_url -- url of the IRIDA server
            username -- username for server
            password -- password for given username
            timeout_multiplier -- number of seconds to give per MB of data being transferred

        return ApiCalls object
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.username = username
        self.password = password
        self.timeout_multiplier = timeout_multiplier
        self.max_wait_time = max_wait_time
        self.http_max_retries = http_max_retries

        self._session_lock = threading.Lock()
        self._session_set_externally = False
        self._create_session()
        self.cached_projects = None
        self.cached_samples = {}

        # these two are used when sending signals to the progress module
        self._current_upload_project_id = None
        self._current_upload_sample_name = None

    @property
    def _session(self):
        try:  # Todo: rework this code without the try/catch/finally and odd exception raise
            self._session_lock.acquire()
            response = self._session_instance.options(self.base_url)
            if response.status_code != HTTPStatus.OK:
                raise Exception
            else:
                logging.debug("Existing session still works, going to reuse it.")
        except Exception:
            logging.debug("Token is probably expired, going to get a new session.")
            self._reinitialize_session()
        finally:
            self._session_lock.release()

        return self._session_instance

    def _reinitialize_session(self):
        oauth_service = self._get_oauth_service()
        access_token = self._get_access_token(oauth_service)
        _sess = oauth_service.get_session(access_token)
        # We add a HTTPAdapter with max retries so we don't fail out if one request gets lost
        _sess.mount('https://', HTTPAdapter(max_retries=self.http_max_retries))
        _sess.mount('http://', HTTPAdapter(max_retries=self.http_max_retries))
        self._session_instance = _sess

    def _create_session(self):
        """
        create session to be re-used until expiry for get and post calls

        returns session (OAuth2Session object)
        """

        def validate_url_form(url):
            """
                offline 'validation' of url. parse through url and see if its malformed
            """
            parsed = urlparse(url)
            valid = len(parsed.scheme) > 0
            return valid

        if self.base_url[-1:] != "/":
            self.base_url = self.base_url + "/"
        if not validate_url_form(self.base_url):
            logging.error("Cannot create session. {} is not a valid URL".format(self.base_url))
            raise exceptions.IridaConnectionError("Cannot create session." + self.base_url + " is not a valid URL")

        self._reinitialize_session()

    def _get_oauth_service(self):
        """
        get oauth service to be used to get access token

        returns oauthService
        """

        access_token_url = urljoin(self.base_url, "oauth/token")
        oauth_service = OAuth2Service(
            client_id=self.client_id,
            client_secret=self.client_secret,
            name="irida",
            access_token_url=access_token_url,
            base_url=self.base_url
        )

        return oauth_service

    def _get_access_token(self, oauth_service):
        """
        get access token to be used to get session from oauth_service

        arguments:
            oauth_service -- O2AuthService from get_oauth_service

        returns access token
        """

        def token_decoder(return_dict):
            """
            safely parse given dictionary

            arguments:
                return_dict -- access token dictionary

            returns evaluated dictionary
            """
            # It is supposedly safer to decode bytes to string and then use ast.literal_eval than just use eval()
            try:
                irida_dict = ast.literal_eval(return_dict.decode("utf-8"))
            except (SyntaxError, ValueError):
                # SyntaxError happens when something that looks nothing like a token is returned (ex: 404 page)
                # ValueError happens with the path returns something that looks like a token, but is invalid
                #   (ex: forgetting the /api/ part of the url)
                raise ConnectionError("Unexpected response from server, URL may be incorrect")
            return irida_dict

        params = {
            "data": {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }
        }

        try:
            access_token = oauth_service.get_access_token(
                decoder=token_decoder, **params)
        except ConnectionError as e:
            logging.error("Can not connect to IRIDA")
            raise exceptions.IridaConnectionError("Could not connect to the IRIDA server. URL may be incorrect."
                                                  " IRIDA returned with error message: {}".format(e.args))
        except KeyError as e:
            logging.error("Can not get access token from IRIDA")
            raise exceptions.IridaConnectionError("Could not get access token from IRIDA. Credentials may be incorrect."
                                                  " IRIDA returned with error message: {}".format(e.args))

        return access_token

    @staticmethod
    def _handle_rest_exception(url, e):
        """
        Given an exception, generates a more detailed description and a IRIDA specific error
        :param url: original url called (to be included in response)
        :param e: exception that was raised
        :return: IridaConnectionError to be raised by calling function
        """
        if type(e) is URLError:
            logging.error("Could not connect to IRIDA, URL '{}' responded with: {}"
                          "".format(url, str(e)))
            return exceptions.IridaConnectionError("Could not connect to IRIDA, URL '{}' responded with: {}"
                                                   "".format(url, str(e)))
        if type(e) is ConnectionError:
            # This could be anything from disconnection during post to IRIDA crashing
            logging.error("ConnectionError occurred while transferring data: " + str(e))
            raise exceptions.IridaConnectionError(e)
        else:
            logging.error("Could not connect to IRIDA, non URLError Exception occurred. URL '{}' Error: {}"
                          "".format(url, str(e)))
            return exceptions.IridaConnectionError("Could not connect to IRIDA, non URLError Exception occurred. "
                                                   "URL '{}' Error: {}".format(url, str(e)))

    @staticmethod
    def _handle_irida_exception(response):
        """
        Generates and returns an appropriate exception based on the status code in the response returned by irida

        :param response: response from irida (Non 201)
        :return: Exception Sub Class
        """
        logging.debug("response.status_code: " + str(response.status_code))
        logging.debug("response.text: " + response.text)
        if response.status_code == HTTPStatus.BAD_REQUEST:  # 400
            e = exceptions.IridaResourceError("Request to IRIDA was invalid: "
                                              "{status_code}: {err_msg}\n".format(
                                                  status_code=str(response.status_code),
                                                  err_msg=response.reason))
        elif response.status_code in [HTTPStatus.UNAUTHORIZED,
                                      HTTPStatus.FORBIDDEN]:  # 401, 403
            e = exceptions.IridaResourceError("Request to IRIDA is Forbidden. Do you have access to this resource?: "
                                              "{status_code}: {err_msg}\n".format(
                                                  status_code=str(response.status_code),
                                                  err_msg=response.reason))
        elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:  # 500
            e = exceptions.IridaConnectionError("IRIDA encountered an error while handling your request: "
                                                "{status_code}: {err_msg}\n".format(
                                                    status_code=str(response.status_code),
                                                    err_msg=response.reason))
        elif response.status_code == HTTPStatus.NOT_FOUND:  # 404
            e = exceptions.IridaResourceError("The url you specified could not be reached. Please verify your URL and "
                                              "the projects/samples/etc you specified.")
        else:
            e = exceptions.IridaConnectionError("Error encountered while communicating with IRIDA: "
                                                "{status_code}: {err_msg}\n".format(
                                                    status_code=str(response.status_code),
                                                    err_msg=response.reason))
        return e

    def get_projects(self):
        """
        API call to api/projects to get list of projects

        returns list containing projects. each project is Project object.
        """

        logging.info("Loading projects.")

        if self.cached_projects is None:
            logging.debug("Loading projects from IRIDA server.")
            url = f"{self.base_url}/projects"

            try:
                response = self._session.get(url)
            except Exception as e:
                raise ApiCalls._handle_rest_exception(url, e)

            if response.status_code == HTTPStatus.OK:  # 200
                result = response.json()["resource"]["resources"]
            else:
                raise self._handle_irida_exception(response)

            try:
                project_list = [
                    model.Project(
                        name=project_dict["name"],
                        description=project_dict["projectDescription"],
                        id=project_dict["identifier"]
                    )
                    for project_dict in result
                ]

            except KeyError as e:
                e.args = map(str, e.args)
                msg_arg = " ".join(e.args)
                logging.debug(msg_arg + " not found. Available keys: "
                              ", ".join(result[0].keys()))
                raise exceptions.IridaResourceError(msg_arg + " not found in data provided by IRIDA. Available keys: "
                                                    ", ".join(result[0].keys()))
            self.cached_projects = project_list
        else:
            logging.debug("Loading projects from cache.")

        return self.cached_projects

    """
    Potential future functionality:
    get_sample(sample_id): returns a single sample based on the irida sample identifier
    """

    def get_samples(self, project_id):
        """
        API call to api/projects/project_id/samples

        arguments:
            project_id -- project identifier from irida

        returns list of samples for the given project.
            each sample is a Sample object.
        """

        logging.info("Getting samples from project '{}'".format(project_id))

        if project_id not in self.cached_samples:
            url = f"{self.base_url}/projects/{project_id}/samples"

            try:
                response = self._session.get(url)
            except Exception as e:
                raise ApiCalls._handle_rest_exception(url, e)

            if response.status_code != HTTPStatus.OK:  # 200
                logging.error("Encountered error while getting samples: {} {}"
                              "".format(response.status_code, response.reason))
                raise ApiCalls._handle_irida_exception(response)

            result = response.json()["resource"]["resources"]

            sample_list = []
            for sample_dict in result:
                # use name and description from dictionary as base parameters when creating sample
                sample_name = sample_dict['sampleName']
                sample_desc = sample_dict['description']
                sample_id = int(sample_dict['identifier'])
                # remove them from the dict so we don't have useless duplicate data
                del sample_dict['sampleName']
                del sample_dict['description']
                del sample_dict['identifier']
                sample_list.append(model.Sample(
                    sample_name=sample_name,
                    description=sample_desc,
                    samp_dict=sample_dict,
                    sample_id=sample_id
                ))
            self.cached_samples[project_id] = sample_list

        return self.cached_samples[project_id]

    def get_sequence_files(self, project_id, sample_name):
        """
        API call to api/projects/project_id/sample_id/sequenceFiles
        We fetch the sample file through the project id on this route

        arguments:

            sample_name -- the sample name identifier to get from irida, relative to a project
            project_id -- the id of the project the sample is on

        returns list of sequencefile dictionary for given sample_id
        """

        logging.info("Getting sequence files from sample '{}' on project '{}'".format(sample_name, project_id))

        # Need the sample id for upload, not the sample name.
        # This is cached so it's only 1 call per project uploading to
        # TODO: In the future, this function should accept sample_id instead of sample_name
        sample_id = self.get_sample_id(sample_name, project_id)
        url = f"{self.base_url}/samples/{sample_id}/sequenceFiles"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            # todo future development
            # This response should be parsed into SequenceFile objects
            # This is a bit tricky because Forward and Reverse reads are different files in the returned resources
            result = response.json()["resource"]["resources"]
        else:
            raise self._handle_irida_exception(response)

        return result

    def get_assemblies_files(self, sample_id):
        """
        API call to api/samples/sample_id/assemblies

        :param sample_id: sample the assemblies are on
        :return: list of assemblies files dictionary for given sample_name
        """

        logging.info("Getting assemblies files from sample '{}'".format(sample_id))

        url = f"{self.base_url}/samples/{sample_id}/assemblies"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            # todo future development if needed one day
            # This response should be returned as some sort of file object
            # This is related to how we return get_sequence_files too, but there is no real use for it at the moment,
            # yagni
            result = response.json()["resource"]["resources"]
        else:
            raise self._handle_irida_exception(response)

        return result

    def get_fast5_files(self, project_id, sample_name):
        """
        API call to api/projects/project_id/sample_id/sequenceFiles/fast5
        We fetch the fast5 files through the project id on this route

        arguments:

            sample_name -- the sample name identifier to get from irida, relative to a project
            project_id -- the id of the project the sample is on

        returns list of fast5 files dictionary for given sample_id
        """

        logging.info("Getting fast5 files from sample '{}' on project '{}'".format(sample_name, project_id))

        # Need the sample id for upload, not the sample name.
        # This is cached so it's only 1 call per project uploading to
        # TODO: In the future, this function should accept sample_id instead of sample_name
        sample_id = self.get_sample_id(sample_name, project_id)
        url = f"{self.base_url}/samples/{sample_id}/fast5"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            # todo future development if needed one day
            # This response should be returned as some sort of file object
            # This is related to how we return get_sequence_files too, but there is no real use for it at the moment,
            # yagni
            result = response.json()["resource"]["resources"]
        else:
            raise self._handle_irida_exception(response)

        return result

    def get_metadata(self, sample_id):
        """
        API call to api/samples/{sampleId}/metadata
        arguments:
            sample_id
        returns list of metadata associated with sampleID
        """

        logging.info("Getting metadata from sample id '{}'".format(sample_id))

        url = f"{self.base_url}/samples/{sample_id}/metadata"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            result = response.json()["resource"]["metadata"]
        else:
            raise self._handle_irida_exception(response)

        # TODO: api refactor project: build this data into a model/Metadata object
        return result

    def send_project(self, project, clear_cache=True):
        """
        post request to send a project to IRIDA via API
        the project being sent requires a name that is at least
            5 characters long

        arguments:
            project -- a Project object to be sent.

        returns a dictionary containing the result of post request.
        when post is successful the dictionary it returns will contain the same
            name and projectDescription that was originally sent as well as
            additional keys like createdDate and identifier.
        when post fails then an error will be raised so return statement is
            not even reached.
        """
        logging.info("Sending project to IRIDA.")

        if clear_cache:
            self.cached_projects = None
        url = f"{self.base_url}/projects"
        json_obj = json.dumps(project.get_uploadable_dict())

        try:
            response = self._session.post(url, json_obj, **JSON_HEADERS)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Error sending project: {} {}".format(response.status_code, response.text))
            raise self._handle_irida_exception(response)

        return json_res

    def send_sample(self, sample, project_id):
        """
        Post request to send a sample to a project

        :param sample: Sample object to send
        :param project_id: id of project to send sample too
        :return: json response from server
        """

        logging.info("Creating sample '{}' for project '{}' on IRIDA.".format(sample.sample_name, project_id))

        self.cached_samples = {}  # reset the cache, we're updating stuff
        self.cached_projects = None

        url = f"{self.base_url}/projects/{project_id}/samples"
        json_obj = json.dumps(sample.get_uploadable_dict())

        try:
            response = self._session.post(url, json_obj, **JSON_HEADERS)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Did not create sample on server. Response code is '{}' and error message is '{}'"
                          "".format(response.status_code, response.text))
            raise self._handle_irida_exception(response)

        return json_res

    def get_sample_details(self, sample_id):
        """
        Given a sample id, returns response from server for the baseurl/samples/sample_id endpoint
        :param sample_id:
        :return: server resource response
        """
        logging.info("Getting sample info for sample id '{}'".format(sample_id))

        url = f"{self.base_url}/samples/{sample_id}"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            result = response.json()
        else:
            raise self._handle_irida_exception(response)

        # TODO: api refactor project: build this data into a model/Metadata object
        return result

    def send_sequence_files(self, sequence_file, sample_name, project_id, upload_id, upload_mode=MODE_DEFAULT):
        """
        post request to send sequence files found in given sample argument
        raises error if either project ID or sample ID found in Sample object
        doesn't exist in irida

        arguments:
            sequence_file -- SequenceFile object to send
            sample_name -- irida sample name identifier to send to
            project_id -- irida project identifier
            upload_id -- the run to upload the files to
            upload_mode -- default:MODE_DEFAULT -- which upload mode will be used

        returns result of post request.
        """

        # update which files are being sent
        self._current_upload_project_id = project_id
        self._current_upload_sample_name = sample_name

        # Get the url's needed to send sequence files
        # Need the sample id for upload, not the sample name.
        # This is cached so it's only 1 call per project uploading to
        # TODO: In the future, this function should accept sample_id instead of sample_name
        sample_id = self.get_sample_id(sample_name, project_id)
        sample_url = f"{self.base_url}/samples/{sample_id}"
        url = ApiCalls._get_sample_upload_url(sequence_file, sample_url, upload_mode)

        # Get the data encoder
        data_pkg = self._get_sequence_data_pkg(sequence_file, upload_id)
        # Generate headers from the data encoder
        headers_pkg = {'Content-Type': data_pkg.content_type, **SESSION_HEADERS}

        logging.debug("Sending files to [{}]".format(url))
        logging.debug("headers: " + str(headers_pkg))

        timeout = self._get_sequence_file_timeout(sequence_file)

        try:
            response = self._session.post(url, data=data_pkg, headers=headers_pkg, timeout=timeout)
        except Exception as e:
            logging.error("ConnectionError occurred while transferring data: " + str(e))
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.CREATED:
            json_res = json.loads(response.text)
        else:
            logging.error("Error while uploading [{}]: [{}]".format(sample_name, response.reason))
            raise self._handle_irida_exception(response)

        return json_res

    @staticmethod
    def _get_sample_upload_url(sequence_file, sample_url, upload_mode):
        """
        Gets the appropriate url for single end, paired end, or assemblies files.
        :param sequence_file: Sequence Fle to upload
        :param sample_url: Sample Url to upload to
        :param upload_mode: String indicating upload mode
        :return:
        """
        if upload_mode == MODE_ASSEMBLIES:
            url = f"{sample_url}/assemblies"
        elif upload_mode == MODE_FAST5:
            url = f"{sample_url}/fast5"
        elif upload_mode == MODE_DEFAULT:
            if sequence_file.is_paired_end():
                logging.debug("api_calls: sending paired-end file")
                url = f"{sample_url}/pairs"
            else:
                logging.debug("api_calls: sending single-end file")
                url = f"{sample_url}/sequenceFiles"
        else:
            error = "Upload mode '{}' is invalid. Upload mode must be one of {}".format(
                upload_mode,
                UPLOAD_MODES
            )
            logging.error(error)
            raise exceptions.IridaResourceError(error, upload_mode)

        return url

    def _get_sequence_file_timeout(self, sequence_file):
        """
        Approximates transfer time and generates a timeout according to variables defined in this module.

        These values can be overridden when importing the module
        :param sequence_file:
        :return:
        """
        # Get approximation for amount of data to send
        filesize_bytes = Path(sequence_file.file_list[0]).stat().st_size
        if sequence_file.is_paired_end():
            filesize_bytes = filesize_bytes * 2
        # Gives timeout_multiplier seconds per mb of data to transfer
        timeout_mb = (filesize_bytes * self.timeout_multiplier / TIMEOUT_BYTES_TO_MB_DIVISOR)
        # minimum time should be 20 minutes
        return timeout_mb if timeout_mb > TIMEOUT_MINIMUM else TIMEOUT_MINIMUM

    def send_metadata(self, metadata, sample_id):
        """
        Put request to add metadata to specific sample ID

        :param metadata: Metadata object
        :param sample_id: id of sample to add metadata to
        :return: json response from server
        """

        logging.info("Adding metadata to sample '{}' ".format(sample_id))

        url = f"{self.base_url}/samples/{sample_id}/metadata"

        json_obj = json.dumps(metadata.get_uploadable_dict())

        try:
            response = self._session.put(url, data=json_obj, **JSON_HEADERS)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            json_res = json.loads(response.text)
        else:
            logging.error("Did not add metadata to sample. Response code is '{}' and error message is '{}'"
                          "".format(response.status_code, response.text))
            raise self._handle_irida_exception(response)

        return json_res

    def _send_file_callback(self, monitor):
        """
        Sends data to the progress module to update file percentages
        """
        progress_percent = round(monitor.bytes_read / monitor.len * 100, 2)
        progress.send_progress(progress.ProgressData(
            sample=self._current_upload_sample_name,
            project=self._current_upload_project_id,
            progress=progress_percent
        ))
        print("Progress: ", progress_percent, "% Uploaded     \r", end="")

    def _get_sequence_data_pkg(self, sequence_file, upload_id):
        """
        Creates the data encoder, and attaches a monitor for callback functionality
        """
        # build data encoder
        encoder = ApiCalls._get_multipart_encoder(sequence_file, upload_id)
        # create callback monitor for file progress
        monitor = MultipartEncoderMonitor(encoder, self._send_file_callback)
        # override max byte read size
        # This lambda overrides httplibs hard coded 8192 byte read size
        # More details: https://github.com/requests/toolbelt/issues/75#issuecomment-237189952
        # Update: although configuring blocksize has been added to Python 3.7, it is not implemented in Requests, and is
        # labeled as "wontfix". So unless we want to move away from Multipart File Encoding, this lambda patch stays.
        # If we do move away from Multipart File Encoding, choosing a faster file transfer method that does not rely on
        # http would be better than switching to urllib3 or other python http packages.
        monitor._read = monitor.read
        monitor.read = lambda size: monitor._read(1024 * 1024)
        # return the monitor/encoder object
        return monitor

    @staticmethod
    def _get_multipart_encoder(sequence_file, upload_id):
        """
        Creates a multipart file encoder to be used for streaming files to IRIDA
        """

        logging.debug("building multipart encoder")

        boundary = "B0undary"

        if sequence_file.is_paired_end():
            # Get file names of sequence files
            file_name_a = sequence_file.file_list[0]
            file_name_b = sequence_file.file_list[1]

            file_metadata = sequence_file.properties_dict
            # miseqRunId is what irida uses to parse the upload id
            # we should think about renaming this in irida,
            # but when we do it will break compatibility with all older uploaders
            file_metadata["miseqRunId"] = str(upload_id)
            file_metadata_json = json.dumps(file_metadata)

            m_encoder = MultipartEncoder(
                fields={
                    'file1': (file_name_a.replace("\\", "/"), open(file_name_a, 'rb')),
                    'file2': (file_name_b.replace("\\", "/"), open(file_name_b, 'rb')),
                    'parameters1': (None, str(file_metadata_json), 'application/json'),
                    'parameters2': (None, str(file_metadata_json), 'application/json')
                },
                boundary=boundary
            )

            return m_encoder
        else:
            file_name = sequence_file.file_list[0]

            file_metadata = sequence_file.properties_dict
            # miseqRunId is what irida uses to parse the upload id
            # we should think about renaming this in irida,
            # but when we do it will break compatibility with all older uploaders
            file_metadata["miseqRunId"] = str(upload_id)
            file_metadata_json = json.dumps(file_metadata)

            m_encoder = MultipartEncoder(
                fields={
                    'file': (file_name.replace("\\", "/"), open(file_name, 'rb')),
                    'parameters': (None, str(file_metadata_json), 'application/json'),
                },
                boundary=boundary
            )

            return m_encoder

    def create_seq_run(self, metadata, sequencing_run_type):
        """
        Create a sequencing run.

        uploadStatus "UPLOADING"

        There are some parsed metadata keys from the SampleSheet.csv that are
        currently not accepted/used by the API so they are discarded.
        Everything not in the acceptable_properties list below is discarded.

        arguments:
            metadata -- SequencingRun's metadata
            sequencing_run_type -- string: used as the identifier for the type of sequencing run being uploaded

        returns: the sequencing run identifier for the sequencing run that was created
        """

        logging.debug("Creating new sequencing run on IRIDA")

        metadata_dict = metadata.copy()
        # metadata_dict requires the workflow parameter or else IRIDA will not create the seq run
        if 'workflow' not in metadata_dict:
            metadata_dict['workflow'] = 'workflow'

        url = f"{self.base_url}/sequencingrun/{sequencing_run_type}"

        acceptable_properties = [
            "layoutType", "chemistry", "projectName",
            "experimentName", "application", "uploadStatus",
            "investigatorName", "createdDate", "assay", "description",
            "workflow", "readLengths"]

        metadata_dict["uploadStatus"] = "UPLOADING"

        keys_to_remove = []
        for key in metadata_dict.keys():
            if key not in acceptable_properties:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del metadata_dict[key]

        json_obj = json.dumps(metadata_dict)

        try:
            response = self._session.post(url, json_obj, **JSON_HEADERS)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Encountered error while creating sequence run: {} {}"
                          "".format(response.status_code, response.reason))
            raise self._handle_irida_exception(response)

        # Grab the run identifier from the returned json
        sequencing_run_id = json_res['resource']['identifier']
        logging.debug("Sequencing run id '{}' has been created".format(sequencing_run_id))
        return sequencing_run_id

    def get_seq_runs(self):
        """
        Get list of all SequencingRun objects

        return list of SequencingRuns
        """
        logging.debug("Getting sequencing runs")

        url = f"{self.base_url}/sequencingrun"

        try:
            response = self._session.get(url)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            json_res_list = response.json()["resource"]["resources"]
        else:
            logging.error("Encountered error while getting sequence runs: {} {}"
                          "".format(response.status_code, response.reason))
            raise self._handle_irida_exception(response)

        return json_res_list

    def set_seq_run_complete(self, identifier):

        """
        Update a sequencing run's upload status to "COMPLETE"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "COMPLETE"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def set_seq_run_uploading(self, identifier):

        """
        Update a sequencing run's upload status to "UPLOADING"

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "UPLOADING"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def set_seq_run_error(self, identifier):

        """
        Update a sequencing run's upload status to "ERROR".

        arguments:
            identifier -- the id of the sequencing run to be updated

        returns result of patch request
        """

        status = "ERROR"
        json_res = self._set_seq_run_upload_status(identifier, status)

        return json_res

    def _set_seq_run_upload_status(self, identifier, status):

        """
        Update a sequencing run's upload status to the given status argument

        arguments:
            identifier -- the id of the sequencing run to be updated
            status     -- string that the sequencing run will be updated
                          with

        returns result of patch request
        """

        logging.debug("Setting sequencing run '{}' to '{}'".format(identifier, status))

        url = f"{self.base_url}/sequencingrun/{identifier}"
        update_dict = {"uploadStatus": status}
        json_obj = json.dumps(update_dict)

        try:
            response = self._session.patch(url, json_obj, **JSON_HEADERS)
        except Exception as e:
            raise ApiCalls._handle_rest_exception(url, e)

        if response.status_code == HTTPStatus.OK:  # 200
            json_res = json.loads(response.text)
        else:
            logging.error("Encountered error while changing upload status of run '{}' to '{}': {} {}"
                          "".format(identifier, status, response.status_code, response.reason))
            raise exceptions.IridaConnectionError("Error: " + str(response.status_code) + " " + response.reason)

        return json_res

    def project_exists(self, project_id):
        """
        Check if a project exists

        :param project_id: project that we are checking for existence
        :return: True or False
        """
        logging.debug("project exists: {}".format(project_id))
        project_id = str(project_id)
        project_list = self.get_projects()
        return any([p.id == project_id for p in project_list])

    def try_project_access(self, project_id):
        """
        Attempts a get request to a project, and returns the HTTPStatus that IRIDA returns
        This is useful for determining if a user does not have access to a project or if it does not exist at all.

        :param project_id:
        :return: HTTPStatus(IntEnum)
        """
        logging.debug("Trying to access project: {}".format(project_id))

        url = f"{self.base_url}/projects/{project_id}"

        try:
            response = self._session.get(url)
        except Exception as e:
            # Handle any exceptions where communication with the server fails
            raise ApiCalls._handle_rest_exception(url, e)

        logging.debug("IRIDA responded with status code: {}".format(response.status_code))
        return response.status_code

    def sample_exists(self, sample_name, project_id):
        """
        Given a sample name and project id, returns True or False for if sample exists
        :param sample_name:
        :param project_id:
        :return:
        """
        return True if (self.get_sample_id(sample_name, project_id) is not False) else False

    def get_sample_id(self, sample_name, project_id):
        """
        Given a sample name and project id, returns the sample id, or False if it doesn't exist

        This method shares sample caching with the get_samples method

        :param sample_name: sample to confirm existence of
        :param project_id: project that we think the sample is on
        :return: Integer of the sample identifier if it exists, otherwise False
        """
        logging.debug("sample exists: sample: {}, on project: {}".format(sample_name, project_id))
        sample_list = self.get_samples(project_id)
        for s in sample_list:
            if s.sample_name.lower() == sample_name.lower():
                return s.sample_id
        return False
