import ast
import itertools
import json
import logging
import threading

from http import HTTPStatus
from os import path
from rauth import OAuth2Service
from requests import ConnectionError
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urlparse
from urllib.error import URLError

import model

from . import exceptions


class ApiCalls(object):

    def __init__(self, client_id, client_secret,
                 base_url, username, password, max_wait_time=20, http_max_retries=5):
        """
        Create OAuth2Session and store it

        arguments:
            client_id -- client_id for creating access token.
            client_secret -- client_secret for creating access token.
            base_url -- url of the IRIDA server
            username -- username for server
            password -- password for given username

        return ApiCalls object
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.username = username
        self.password = password
        self.max_wait_time = max_wait_time
        self.http_max_retries = http_max_retries

        self._stop_upload = False

        self._session_lock = threading.Lock()
        self._session_set_externally = False
        self._create_session()
        self.cached_projects = None
        self.cached_samples = {}

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
            irida_dict = ast.literal_eval(return_dict.decode("utf-8"))
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

            resources_list = response.json()["resource"]["resources"]
            # try to get all keys from target_dict to our list or links
            try:
                links_list = next(
                    r["links"] for r in resources_list
                    if r[target_dict["key"]].lower() ==
                    str(target_dict["value"]).lower()
                )

            except KeyError:
                raise exceptions.IridaKeyError(target_dict["key"] + " not found. Available keys: " +
                                               ", ".join(resources_list[0].keys()))

            except StopIteration:
                raise exceptions.IridaKeyError(target_dict["value"] + " not found.")

        else:  # get all the links in the response
            links_list = response.json()["resource"]["links"]
        try:
            ret_val = next(link["href"] for link in links_list
                           if link["rel"] == target_key)

        except StopIteration:
            logging.debug(target_key + " not found in links. Available links: " +
                          ", ".join([str(link["rel"]) for link in links_list]))
            raise exceptions.IridaKeyError(target_key + " not found in links. Available links: " +
                                           ", ".join([str(link["rel"]) for link in links_list]))

        return ret_val

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
                logging.debug(msg_arg + " not found. Available keys: " +
                              ", ".join(result[0].keys()))
                raise exceptions.IridaKeyError(msg_arg + " not found. Available keys: " +
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

            sample_name -- the sample id to get from irida, relative to a project
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
            raise exceptions.IridaResourceError("Error sending project: {} {}"
                                                "".format(response.status_code, response.text))

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
            e = exceptions.IridaResourceError("Error {status_code}: {err_msg}.\nSample data: {sample_data}"
                                              "".format(
                                                    status_code=str(response.status_code),
                                                    err_msg=response.text,
                                                    sample_data=str(sample)
                                              ), sample.sample_name)
            raise e

        return json_res

    # Todo: Rename to kill_connections(self), to be done when working on threading
    def _kill_connections(self):
        """Terminate any currently running uploads.

        This method simply sets a flag to instruct any in-progress generators called
        by `_send_sequence_files` below to stop generating data and raise an exception
        that will set the run to an error state on the server.
        """

        self._stop_upload = True
        self._session.close()

    def send_sequence_files(self, sequence_file, sample_name, project_id, upload_id):
        """
        post request to send sequence files found in given sample argument
        raises error if either project ID or sample ID found in Sample object
        doesn't exist in irida

        arguments:
            sample -- Sample object
            upload_id -- the run to upload the files to

        returns result of post request.
        """

        boundary = "B0undary"
        read_size = 32768
        self._stop_upload = False

        def _send_file(filename, parameter_name):
            """This function is a generator that yields a multipart form-data
            entry for the specified file. This function will yield `read_size`
            bytes of the specified file name at a time as the generator is called.
            This function will also terminate generating data when the field
            `self._stop_upload` is set.

            Args:
                filename: the file to read and yield in `read_size` chunks to
                          the server.
                parameter_name: the form field name to send to the server.
            """

            # Send the boundary header section for the file
            logging.debug("Sending the boundary header section for {}".format(filename))
            yield (("\r\n--{boundary}\r\n"
                   "Content-Disposition: form-data; name=\"{parameter_name}\"; filename=\"{filename}\"\r\n\r\n").format(
                boundary=boundary, parameter_name=parameter_name, filename=filename.replace("\\", "/"))).encode()

            # Get total file size for progress
            total_file_size = path.getsize(filename)

            # Send the contents of the file, read_size bytes at a time until
            # we've either read the entire file, or we've been instructed to
            # stop the upload by the UI
            logging.info("Starting to send file {}".format(filename))
            try:
                with open(filename, "rb", read_size) as fastq_file:
                    data = fastq_file.read(read_size)
                    # Command line progress info printing
                    # Todo: once message passing is in place, this might find its home in that module
                    bytes_read = 0
                    while data and not self._stop_upload:
                        bytes_read += len(data)
                        print("Progress: ", round(bytes_read/total_file_size*100, 2),
                              "% Uploaded     \r", end="")
                        yield data
                        data = fastq_file.read(read_size)
                    print()  # end cap to the dots we printed above
                    logging.info("Finished sending file {}".format(filename))
                    if self._stop_upload:
                        logging.info("Halting upload on user request.")
            except IOError:
                logging.error("Could not open file: {}".format(filename))
                raise exceptions.FileError("Could not open file: {}".format(filename))

        def _send_parameters(parameter_name, parameters):
            """This function is a generator that yields a multipart form-data
            entry with additional file metadata.

            Args:
                parameter_name: the form field name to use to send to the server.
                parameters: a JSON encoded object with the metadata for the file.
            """

            logging.debug("Going to send parameters for {}".format(parameter_name))
            yield (("\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"{parameter_name}\"\r\n"
                   "Content-Type: application/json\r\n\r\n{parameters}\r\n").format(
                boundary=boundary, parameter_name=parameter_name, parameters=parameters)).encode()

        def _finish_request():
            """This function is a generator that yields the terminal boundary
            entry for a multipart form-data upload."""

            yield ("--{boundary}--".format(boundary=boundary)).encode()

        def _sample_upload_generator(sequence_file_up):
            """This function accepts the sequence_file and composes a series of generators
            that are used to send the file contents and metadata for the sample.

            Args:
                sequence_file_up: the sequence_file to send to the server
            """

            file_metadata = sequence_file_up.properties_dict
            file_metadata["miseqRunId"] = str(upload_id)
            file_metadata_json = json.dumps(file_metadata)

            if sequence_file_up.is_paired_end():
                # Compose a collection of generators to send both files of a paired-end
                # file set and the corresponding metadata
                logging.debug("api_calls._sample_upload_generator: is paired end read")
                return itertools.chain(
                    _send_file(filename=sequence_file_up.file_list[0], parameter_name="file1"),
                    _send_file(filename=sequence_file_up.file_list[1], parameter_name="file2"),
                    _send_parameters(parameter_name="parameters1", parameters=file_metadata_json),
                    _send_parameters(parameter_name="parameters2", parameters=file_metadata_json),
                    _finish_request())
            else:
                # Compose a generator to send the single file from a single-end
                # file set and the corresponding metadata.
                logging.debug("api_calls._sample_upload_generator: is single end read")
                return itertools.chain(
                    _send_file(filename=sequence_file_up.file_list[0], parameter_name="file"),
                    _send_parameters(parameter_name="parameters", parameters=file_metadata_json),
                    _finish_request())

        try:
            project_url = self._get_link(self.base_url, "projects")
            samples_url = self._get_link(project_url, "project/samples",
                                         target_dict={
                                             "key": "identifier",
                                             "value": project_id
                                         })
        except StopIteration:
            raise exceptions.IridaResourceError("The given project ID doesn't exist", project_id)

        try:
            seq_url = self._get_link(samples_url, "sample/sequenceFiles",
                                     target_dict={
                                         "key": "sampleName",
                                         "value": sample_name
                                     })
        except StopIteration:
            logging.error("The given sample '{}' does not exist on that project".format(sample_name))
            raise exceptions.IridaResourceError("The given sample ID does not exist on that project", sample_name)

        if sequence_file.is_paired_end():
            logging.debug("api_calls: sending paired-end file")
            url = self._get_link(seq_url, "sample/sequenceFiles/pairs")
        else:
            logging.debug("api_calls: sending single-end file")
            url = seq_url

        logging.debug("Sending files to [{}]".format(url))
        data_pkg = _sample_upload_generator(sequence_file)
        headers_pkg = {"Content-Type": "multipart/form-data; boundary={}".format(boundary)}
        logging.debug("data:" + str(data_pkg))
        logging.debug("headers: " + str(headers_pkg))

        response = self._session.post(url, data=data_pkg, headers=headers_pkg)

        logging.debug("api_calls: send_sequence_files: response: " + response.text)
        if self._stop_upload:
            logging.info("Upload was halted on user request")
            logging.debug("Raising exception so that server upload status is set to error state.")
            raise exceptions.IridaUploadCanceledException("Upload halted on user request.")

        if response.status_code == HTTPStatus.CREATED:
            json_res = json.loads(response.text)
        else:
            e = exceptions.IridaConnectionError("Error {status_code}: {err_msg}\n".format(
                                                status_code=str(response.status_code), err_msg=response.reason))
            logging.error("Error while uploading [{}]: [{}]".format(sample_name, response.reason))
            logging.debug("response.text: " + response.text)
            raise e

        return json_res

    def create_seq_run(self, metadata):
        """
        Create a sequencing run.

        uploadStatus "UPLOADING"

        There are some parsed metadata keys from the SampleSheet.csv that are
        currently not accepted/used by the API so they are discarded.
        Everything not in the acceptable_properties list below is discarded.

        arguments:
            metadata -- SequencingRun's metadata

        returns: the sequencing run identifier for the sequencing run that was created
        """

        logging.debug("Creating new sequencing run on IRIDA")

        metadata_dict = metadata.copy()
        # metadata_dict requires the workflow parameter or else IRIDA will not create the seq run
        if 'workflow' not in metadata_dict:
            metadata_dict['workflow'] = 'workflow'

        seq_run_url = self._get_link(self.base_url, "sequencingRuns")
        # todo: we upload everything as miseq, should change when new sequencers are added to IRIDA
        # The easiest way to do this would be to add a sequencer type param to the metadata when parsing the sample
        url = self._get_link(seq_run_url, "sequencingRun/miseq")

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
            raise exceptions.IridaConnectionError("Error: {} {}".format(response.status_code, response.reason))

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
