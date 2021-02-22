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

    def _validate_url_existence(self, url):
        """
        tries to validate existence of given url by trying to open it.
        true if HTTP OK and no errors when authenticating credentials
        if errors or non HTTP.OK code occur, throws a IridaConnectionError

        arguments:
            url -- the url link to open and validate

        returns
            true if http response OK 200
            raises IridaConnectionError otherwise
        """
        try:
            response = self._session.get(url)
        except URLError as e:
            logging.error("Could not connect to IRIDA, URL '{}' responded with: {}"
                          "".format(url, str(e)))
            raise exceptions.IridaConnectionError("Could not connect to IRIDA, URL '{}' responded with: {}"
                                                  "".format(url, str(e)))
        except Exception as e:
            logging.error("Could not connect to IRIDA, non URLError Exception occurred. URL '{}' Error: {}"
                          "".format(url, str(e)))
            raise exceptions.IridaConnectionError("Could not connect to IRIDA, non URLError Exception occurred. "
                                                  "URL '{}' Error: {}".format(url, str(e)))

        if response.status_code == HTTPStatus.OK:
            return True
        else:
            logging.error("Could not connect to IRIDA, URL '{}' responded with: {} {}"
                          "".format(url, response.status_code, response.reason))
            raise exceptions.IridaConnectionError("Could not connect to IRIDA, URL '{}' responded with: {} {}"
                                                  "".format(url, response.status_code, response.reason))

    def _get_link(self, target_url, target_key, target_dict=None):
        """
        makes a call to target_url(api) expecting a json response
        tries to retrieve target_key from response to find link to resource
        raises exceptions if target_key not found or target_url is invalid

        arguments:
            target_url -- URL to retrieve link from
            target_key -- name of link (e.g projects or project/samples)
            target_dict -- optional dict containing key and value to search
                in targets.
            (e.g {key="identifier",value="100"} to retrieve where
                identifier=100)

        returns link if it exists
        """

        logging.debug("api_calls._get_link: target_url: {}, target_key: {}".format(target_url, target_key))

        self._validate_url_existence(target_url)
        response = self._session.get(target_url)

        if target_dict:  # we are targeting specific resources in the response

            # TODO: This try except block has been added to log a crash that has occurred, to find the source.
            try:
                resources_list = response.json()["resource"]["resources"]
            except KeyError as e:
                # This is occurring for an unknown reason.
                # Once docs can be gathered displaying information, we can determine the source of the bug and fix it.
                logging.error("Dumping json response from IRIDA:")
                logging.error(str(response.json()))
                logging.error("Dumping python KeyError:")
                logging.error(e)
                error_txt = "Response from IRIDA Could not be parsed. Please show the log to your IRIDA Administrator."
                logging.error(error_txt)
                raise exceptions.IridaKeyError(error_txt)
            # try to get all keys from target_dict to our list or links
            try:
                links_list = next(
                    r["links"] for r in resources_list
                    if r[target_dict["key"]].lower() == str(target_dict["value"]).lower()
                )

            except KeyError:
                raise exceptions.IridaKeyError(target_dict["key"] + " not found. Available keys: "
                                               ", ".join(resources_list[0].keys()))

            except StopIteration:
                raise exceptions.IridaKeyError(target_dict["value"] + " not found.")

        else:  # get all the links in the response
            links_list = response.json()["resource"]["links"]
        try:
            ret_val = next(link["href"] for link in links_list
                           if link["rel"] == target_key)

        except StopIteration:
            logging.debug(target_key + " not found in links. Available links: "
                          ", ".join([str(link["rel"]) for link in links_list]))
            raise exceptions.IridaKeyError(target_key + " not found in links. Available links: " + ""
                                           ", ".join([str(link["rel"]) for link in links_list]))

        return ret_val

    def _get_upload_url(self, base_url, run_type_str):
        """
        Concatenates a base url with the run type for constructing the upload url path
        :param base_url: Upload url
        :param run_type_str: Type of sequencing run that is being uploaded
        :return: url
        """

        """TODO:
        There is currently an issue in the IRIDA API with finding links for different sequencer routes
        once that is fixed, the following should be written as:

        seq_run_url = self._get_link(base_url, "sequencingRuns")
        return urljoin(seq_run_url, run_type_str)

        or better yet:

        seq_run_url = self._get_link(base_url, "sequencingRuns")
        return self._get_link(seq_run_url, run_type_str)
        """
        seq_run_url = self._get_link(base_url, "sequencingRuns")
        return urljoin(seq_run_url + "/", run_type_str)

    @staticmethod
    def _get_irida_exception(response):
        """
        Generates and returns an appropriate exception based on the status code in the response returned by irida

        :param response: response from irida (Non 201)
        :return: Exception Sub Class
        """
        logging.debug("response.status_code: " + str(response.status_code))
        logging.debug("response.text: " + response.text)
        if response.status_code == HTTPStatus.BAD_REQUEST:
            e = exceptions.IridaResourceError("Request to IRIDA was invalid: "
                                              "{status_code}: {err_msg}\n".format(
                                                  status_code=str(response.status_code),
                                                  err_msg=response.reason))
        elif response.status_code in [HTTPStatus.UNAUTHORIZED,
                                      HTTPStatus.FORBIDDEN]:
            e = exceptions.IridaResourceError("Request to IRIDA is Forbidden. Do you have access to this resource?: "
                                              "{status_code}: {err_msg}\n".format(
                                                  status_code=str(response.status_code),
                                                  err_msg=response.reason))
        elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            e = exceptions.IridaConnectionError("IRIDA encountered an error while handling your request: "
                                                "{status_code}: {err_msg}\n".format(
                                                    status_code=str(response.status_code),
                                                    err_msg=response.reason))
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
            url = self._get_link(self.base_url, "projects")
            response = self._session.get(url)

            result = response.json()["resource"]["resources"]

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
                raise exceptions.IridaKeyError(msg_arg + " not found. Available keys: "
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
            try:
                project_url = self._get_link(self.base_url, "projects")
                url = self._get_link(project_url, "project/samples",
                                     target_dict={
                                         "key": "identifier",
                                         "value": project_id
                                     })

            except StopIteration:
                logging.error("The given project ID doesn't exist: ".format(project_id))
                raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

            response = self._session.get(url)
            result = response.json()["resource"]["resources"]

            sample_list = []
            for sample_dict in result:
                # use name and description from dictionary as base parameters when creating sample
                sample_name = sample_dict['sampleName']
                sample_desc = sample_dict['description']
                # remove them from the dict so we don't have useless duplicate data
                del sample_dict['sampleName']
                del sample_dict['description']
                sample_list.append(model.Sample(
                    sample_name=sample_name,
                    description=sample_desc,
                    samp_dict=sample_dict
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

        try:
            project_url = self._get_link(self.base_url, "projects")
            sample_url = self._get_link(project_url, "project/samples",
                                        target_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            url = self._get_link(sample_url, "sample/sequenceFiles",
                                 target_dict={
                                     "key": "sampleName",
                                     "value": sample_name
                                 })
            response = self._session.get(url)

        except StopIteration:
            logging.error("The given sample doesn't exist: ".format(sample_name))
            raise exceptions.IridaResourceError("The given sample ID doesn't exist", sample_name)

        # todo future development
        # This response should be parsed into SequenceFile objects
        # This is a bit tricky because Forward and Reverse reads are different files in the returned resources
        result = response.json()["resource"]["resources"]

        return result

    def get_assemblies_files(self, project_id, sample_name):
        """
        API call to api/projects/project_id/sample_id/assemblies
        We fetch the assemblies files through the project id on this route

        arguments:

            sample_name -- the sample name identifier to get from irida, relative to a project
            project_id -- the id of the project the sample is on

        returns list of assemblies files dictionary for given sample_id
        """

        logging.info("Getting assemblies files from sample '{}' on project '{}'".format(sample_name, project_id))

        try:
            project_url = self._get_link(self.base_url, "projects")
            sample_url = self._get_link(project_url, "project/samples",
                                        target_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            url = self._get_link(sample_url, "sample/assemblies",
                                 target_dict={
                                     "key": "sampleName",
                                     "value": sample_name
                                 })
            response = self._session.get(url)

        except StopIteration:
            logging.error("The given sample doesn't exist: ".format(sample_name))
            raise exceptions.IridaResourceError("The given sample ID doesn't exist", sample_name)

        # todo future development if needed one day
        # This response should be returned as some sort of file object
        # This is related to how we return get_sequence_files too, but there is no real use for it at the moment, yagni
        result = response.json()["resource"]["resources"]

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

        try:
            project_url = self._get_link(self.base_url, "projects")
            sample_url = self._get_link(project_url, "project/samples",
                                        target_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            url = self._get_link(sample_url, "sample/sequenceFiles/fast5",
                                 target_dict={
                                     "key": "sampleName",
                                     "value": sample_name
                                 })
            response = self._session.get(url)

        except StopIteration:
            logging.error("The given sample doesn't exist: ".format(sample_name))
            raise exceptions.IridaResourceError("The given sample ID doesn't exist", sample_name)

        # todo future development if needed one day
        # This response should be returned as some sort of file object
        # This is related to how we return get_sequence_files too, but there is no real use for it at the moment, yagni
        result = response.json()["resource"]["resources"]

        return result

    def get_metadata(self, sample_name, project_id):
        """
        API call to api/samples/{sampleId}/metadata
        arguments:
            sample_name
            project_id
        returns list of metadata associated with sampleID
        """

        logging.info("Getting metadata from sample name '{}' found in project ID '{}'".format(sample_name, project_id))

        try:
            project_url = self._get_link(self.base_url, "projects")
            sample_url = self._get_link(project_url, "project/samples",
                                        target_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            url = self._get_link(sample_url, "sample/metadata",
                                 target_dict={
                                     "key": "sampleName",
                                     "value": sample_name
                                 })
            response = self._session.get(url)

        except StopIteration:
            logging.error("The given sample name doesn't exist: ".format(sample_name))
            raise exceptions.IridaResourceError("The given sample name doesn't exist", sample_name)

        result = response.json()["resource"]["metadata"]

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
        url = self._get_link(self.base_url, "projects")
        json_obj = json.dumps(project.get_uploadable_dict())
        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

        response = self._session.post(url, json_obj, **headers)

        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Error sending project: {} {}".format(response.status_code, response.text))
            raise self._get_irida_exception(response)

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

        try:
            project_url = self._get_link(self.base_url, "projects")
            url = self._get_link(project_url, "project/samples",
                                 target_dict={
                                     "key": "identifier",
                                     "value": project_id
                                 })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

        json_obj = json.dumps(sample.get_uploadable_dict())
        response = self._session.post(url, json_obj, **headers)

        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Did not create sample on server. Response code is '{}' and error message is '{}'"
                          "".format(response.status_code, response.text))
            raise self._get_irida_exception(response)

        return json_res

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
        # Verify the project exists
        try:
            project_url = self._get_link(self.base_url, "projects")
            samples_url = self._get_link(project_url, "project/samples",
                                         target_dict={
                                             "key": "identifier",
                                             "value": project_id
                                         })
        except StopIteration:
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        # Get upload url
        url = self._get_sample_upload_url(sequence_file, samples_url, sample_name, upload_mode)

        # Get the data encoder
        data_pkg = self._get_sequence_data_pkg(sequence_file, upload_id)
        # Generate headers from the data encoder
        headers_pkg = {'Content-Type': data_pkg.content_type}

        logging.debug("Sending files to [{}]".format(url))
        logging.debug("headers: " + str(headers_pkg))

        timeout = self._get_sequence_file_timeout(sequence_file)

        try:
            response = self._session.post(url, data=data_pkg, headers=headers_pkg, timeout=timeout)
        except ConnectionError as e:
            # This could be anything from disconnection during post to IRIDA crashing
            logging.error("ConnectionError occurred while transferring data: " + str(e))
            raise exceptions.IridaConnectionError(e)
        except Exception as e:
            # Any other exception, like a library not handling the response properly could be caught here
            logging.error("Exception occured while transferring data: " + str(e))
            raise exceptions.IridaConnectionError(e)

        if response.status_code == HTTPStatus.CREATED:
            json_res = json.loads(response.text)
        else:
            logging.error("Error while uploading [{}]: [{}]".format(sample_name, response.reason))
            raise self._get_irida_exception(response)

        return json_res

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

    def send_metadata(self, metadata, project_id, sample_name):
        """
        Put request to add metadata to specific sample ID

        :param metadata: Metadata object
        :param project_id: id of project sample id is in
        :param sample_name: name of sample in project to add metadata to
        :return: json response from server
        """

        logging.info("Adding metadata to sample '{}' found in project '{}' on IRIDA.".format(sample_name, project_id))

        try:
            project_url = self._get_link(self.base_url, "projects")
            sample_url = self._get_link(project_url, "project/samples",
                                        target_dict={
                                            "key": "identifier",
                                            "value": project_id
                                        })

        except StopIteration:
            logging.error("The given project ID doesn't exist: ".format(project_id))
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            url = self._get_link(sample_url, "sample/metadata",
                                 target_dict={
                                     "key": "sampleName",
                                     "value": sample_name
                                 })

        except StopIteration:
            logging.error("The given sample doesn't exist: ".format(sample_name))
            raise exceptions.IridaResourceError("The given sample doesn't exist", sample_name)

        json_obj = json.dumps(metadata.get_uploadable_dict())

        headers_pkg = {'Content-Type': 'application/json'}

        response = self._session.put(url, data=json_obj, headers=headers_pkg)

        if response.status_code == 200:  # 200
            json_res = json.loads(response.text)
        else:
            logging.error("Did not add metadata to sample. Response code is '{}' and error message is '{}'"
                          "".format(response.status_code, response.text))
            raise self._get_irida_exception(response)

        return json_res

    def _get_sample_upload_url(self, sequence_file, samples_url, sample_name, upload_mode):
        """
        Gets the appropriate url for single end, paired end, or assemblies files.
        :param sequence_file: Sequence Fle to upload
        :param samples_url: Sample Url to upload to
        :param sample_name: Sample Name (identifier) to upload to
        :param upload_mode: String indicating upload mode
        :return:
        """
        try:
            if upload_mode == MODE_ASSEMBLIES:
                url = self._get_link(samples_url, "sample/assemblies",
                                     target_dict={
                                         "key": "sampleName",
                                         "value": sample_name
                                     })
            elif upload_mode == MODE_FAST5:
                url = self._get_link(samples_url, "sample/sequenceFiles/fast5",
                                     target_dict={
                                         "key": "sampleName",
                                         "value": sample_name
                                     })
            elif upload_mode == MODE_DEFAULT:
                part_url = self._get_link(samples_url, "sample/sequenceFiles",
                                          target_dict={
                                              "key": "sampleName",
                                              "value": sample_name
                                          })
                # get paired or single end url
                if sequence_file.is_paired_end():
                    logging.debug("api_calls: sending paired-end file")
                    url = self._get_link(part_url, "sample/sequenceFiles/pairs")
                else:
                    logging.debug("api_calls: sending single-end file")
                    url = part_url
            else:
                error = "Upload mode '{}' is invalid. Upload mode must be one of {}".format(
                    upload_mode,
                    UPLOAD_MODES
                )
                logging.error(error)
                raise exceptions.IridaResourceError(error, upload_mode)

        except StopIteration:
            logging.error("The given sample '{}' does not exist on that project".format(sample_name))
            raise exceptions.IridaResourceError("The given sample ID does not exist on that project", sample_name)

        return url

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
        encoder = self._get_multipart_encoder(sequence_file, upload_id)
        # create callback monitor for file progress
        monitor = MultipartEncoderMonitor(encoder, self._send_file_callback)
        # override max byte read size
        # This lambda overrides httplibs hard coded 8192 byte read size
        # More details: https://github.com/requests/toolbelt/issues/75#issuecomment-237189952
        monitor._read = monitor.read
        monitor.read = lambda size: monitor._read(1024 * 1024)
        # return the monitor/encoder object
        return monitor

    def _get_multipart_encoder(self, sequence_file, upload_id):
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

        url = self._get_upload_url(self.base_url, sequencing_run_type)

        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

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

        response = self._session.post(url, json_obj, **headers)
        if response.status_code == HTTPStatus.CREATED:  # 201
            json_res = json.loads(response.text)
        else:
            logging.error("Encountered error while creating sequence run: {} {}"
                          "".format(response.status_code, response.reason))
            raise self._get_irida_exception(response)

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

        url = self._get_link(self.base_url, "sequencingRuns")
        response = self._session.get(url)

        json_res_list = response.json()["resource"]["resources"]

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
        seq_run_url = self._get_link(self.base_url, "sequencingRuns")

        url = self._get_link(seq_run_url, "self",
                             target_dict={
                                 "key": "identifier",
                                 "value": identifier
                             })
        headers = {
            "headers": {
                "Content-Type": "application/json"
            }
        }

        update_dict = {"uploadStatus": status}
        json_obj = json.dumps(update_dict)

        response = self._session.patch(url, json_obj, **headers)

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

    def sample_exists(self, sample_name, project_id):
        """
        Check if a sample exists on a project

        :param sample_name: sample to confirm existence of
        :param project_id: project that we think the sample is on
        :return: True or False
        """
        logging.debug("sample exists: sample: {}, on project: {}".format(sample_name, project_id))
        sample_list = self.get_samples(project_id)
        return any([s.sample_name.lower() == sample_name.lower() for s in sample_list])
