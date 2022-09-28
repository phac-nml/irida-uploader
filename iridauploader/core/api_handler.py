"""
This file has api related core functionality
It handles initializing and managing an api instance as well as preparing IRIDA for an upload and starting the upload
"""

from http import HTTPStatus
import logging
import concurrent.futures

import iridauploader.api as api
import iridauploader.config as config
import iridauploader.model as model
import iridauploader.progress as progress
from iridauploader.core import model_validator

# The api instance is a global variable which lets the api behave like a singleton
# managed within this file
_api_instance = None


def _initialize_api(
        client_id, client_secret, base_url, username, password, timeout_multiplier, max_wait_time=20):
    """
    Creates the ApiCalls object from the api layer.
    Sets the instance to use the global _api_instance variable so it behaves as a singleton that can be easily re-init

    :param client_id:
    :param client_secret:
    :param base_url:
    :param username:
    :param password:
    :param timeout_multiplier:
    :param max_wait_time:
    :return: The ApiCalls instance
    """
    global _api_instance
    _api_instance = api.ApiCalls(client_id, client_secret, base_url, username, password,
                                 timeout_multiplier, max_wait_time)
    if not base_url.endswith('/api/'):
        logging.warning("base_url does not end in /api/, this configuration might be incorrect")
    # todo something messed up going on here with a double init
    _api_instance = api.ApiCalls(client_id, client_secret, base_url, username, password, max_wait_time)
    return _api_instance


def _get_api_instance():
    """
    Returns the current ApiCalls instance, This function should be used anytime the ApiCalls object is needed

    Raises an exception if the api has not been initialized

    :return: the current ApiCalls instance
    """
    global _api_instance
    if _api_instance is None:
        logging.debug("_get_api_instance: The api instance has been called before being initialized.")
        raise Exception("The API has not been initialized")
    return _api_instance


def initialize_api_from_config():
    """
    Loads the api parameters from the config file and initializes the api with them

    :return: the api instance
    """
    client_id = config.read_config_option("client_id")
    client_secret = config.read_config_option("client_secret")
    base_url = config.read_config_option("base_url")
    username = config.read_config_option("username")
    password = config.read_config_option("password")
    timeout = config.read_config_option("timeout")

    return _initialize_api(client_id=client_id,
                           client_secret=client_secret,
                           base_url=base_url,
                           username=username,
                           password=password,
                           timeout_multiplier=timeout)


def prepare_and_validate_for_upload(sequencing_run):
    """
    Prepares IRIDA to accept the sequencing run
    Validates that projects exist,
    Creates Samples on Projects on Irida if they do not exist yet

    Collects all errors during prep/validation in ValidationResult

    :param sequencing_run: SequencingRun object
    :return: ValidationResult object with all errors that raised while prepping
    """
    # get api
    api_instance = _get_api_instance()

    validation_result = model.ValidationResult()
    # Start online validation
    logging.debug("Checking existence of projects")
    for project in sequencing_run.project_list:
        logging.debug("Checking existence of project: {}".format(project.id))
        if not api_instance.project_exists(project.id):
            if api_instance.try_project_access(project.id) in [HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN]:
                # Project exists but is not accessible by the user
                logging.debug("Project found but user does not have permission")
                err = api.exceptions.IridaResourceError("You do not have permission to access this project", project.id)
            else:
                # No project, add error to validation result and continue
                logging.debug("Could not find project: {}".format(project.id))
                err = api.exceptions.IridaResourceError("Project does not exist", project.id)
            validation_result.add_error(err)
            continue
        logging.debug("Project {} exists".format(project.id))

        logging.debug("Checking existence of samples")
        for sample in project.sample_list:
            logging.debug("Checking existence of Sample {} on Project {}".format(sample.sample_name, project.id))
            if api_instance.sample_exists(sample.sample_name, project.id):
                logging.debug("Sample {} exists on Project {}".format(sample.sample_name, project.id))
            else:
                logging.debug("Sample not found, creating new Sample")
                try:
                    api_instance.send_sample(sample, project.id)
                except api.exceptions.IridaResourceError as e:
                    logging.debug("Sample could not be created")
                    validation_result.add_error(e)
                    continue
                except api.exceptions.IridaConnectionError as e:
                    logging.debug("Sample could not be created")
                    validation_result.add_error(e)
                    continue
                logging.debug("Verifying sample was created")
                if not api_instance.sample_exists(sample.sample_name, project.id):
                    logging.debug("Sample was not created")
                    err = api.exceptions.IridaResourceError("Could not create new Sample on Project {}", project.id)
                    validation_result.add_error(err)
                    continue
                logging.debug("Sample Created")

    return validation_result


def upload_sequencing_run(sequencing_run, directory_status, upload_mode, run_id=None):
    """
    Handles uploading a sequencing run

    Expects api to have been set up
    Expects sequencing run to have been validated
    Expects sequencing run to be valid for upload
    Expects directory_status to be valid

    :param sequencing_run: run to upload
    :param directory_status: DirectoryStatus object to update as files get uploaded
    :param upload_mode: mode of upload
    :param run_id: Default None, when given, run_id will be used instead of generating a new run_id
    :return:
    """
    # get api
    api_instance = _get_api_instance()

    # create a new seq run identifier if none is given
    if run_id is None:
        run_id = api_instance.create_seq_run(sequencing_run.metadata, sequencing_run.sequencing_run_type)
        logging.info("Sequencing run id '{}' has been created for this upload.".format(run_id))
    else:
        logging.info("Using existing run id '{}' for this upload.".format(run_id))
    # Update directory status file
    directory_status.run_id = run_id
    directory_status.status = model.DirectoryStatus.PARTIAL
    progress.write_directory_status(directory_status)

    try:
        # set seq run to upload
        api_instance.set_seq_run_uploading(run_id)

        # Upload
        _run_upload_handler(api_instance, sequencing_run, run_id, directory_status, upload_mode)

        # set seq run to complete
        api_instance.set_seq_run_complete(run_id)

        # set seq run to error if there is an error
    except api.exceptions.IridaConnectionError as e:
        logging.error("Failed to upload SequencingRun, Could not connect to IRIDA")
        raise e
    except api.exceptions.IridaResourceError as e:
        logging.error("Failed to upload SequencingRun, Could not access resources on IRIDA")
        api_instance.set_seq_run_error(run_id)
        raise e
    except api.exceptions.FileError as e:
        logging.error("Failed to upload SequencingRun, Could not access files to upload to IRIDA")
        api_instance.set_seq_run_error(run_id)
        raise e
    # Todo: once threading is added, the upload canceled error will likely need to be caught/raised here


def _run_upload_handler(api_instance, sequencing_run, run_id, directory_status, upload_mode):
    """
    Gets the multithreading config option and runs either the standard upload, or the multithreaded upload
    :param api_instance: api instance should have already been initialized
    :param sequencing_run: sequencing run to upload
    :param run_id: run id to use for upload
    :param directory_status:
    :param upload_mode:
    :return:
    """
    thread_count = config.read_config_option("multithread", int, 0)
    thread_count = 4  # TODO REMOVE THIS TESTING LINE

    if thread_count < 2:
        return _run_upload_basic(api_instance, sequencing_run, run_id, directory_status, upload_mode)
    else:
        _run_upload_multithreaded(api_instance, sequencing_run, run_id, directory_status, upload_mode, thread_count)


def _run_upload_basic(api_instance, sequencing_run, run_id, directory_status, upload_mode):
    """
    Loop through projects and files one at a time to upload
    :param api_instance:
    :param sequencing_run:
    :param run_id:
    :param directory_status:
    :param upload_mode:
    :return:
    """
    # loop through projects
    for project in sequencing_run.project_list:
        # loop through samples
        for sample in project.sample_list:
            if sample.skip:
                logging.info("Skipping Sample {} on Project {}, already uploaded."
                             "".format(sample.sample_name, project.id))
            else:
                logging.info("Uploading to Sample {} on Project {}".format(sample.sample_name, project.id))
                # upload files
                api_instance.send_sequence_files(sequence_file=sample.sequence_file,
                                                 sample_name=sample.sample_name,
                                                 project_id=project.id,
                                                 upload_id=run_id,
                                                 upload_mode=upload_mode)
            # Update status file on progress
            # Skipped samples are set to uploaded too, s.t. if they are skipped,
            #   and the upload fails and is continued again, they will be skipped again.
            directory_status.set_sample_uploaded(sample_name=sample.sample_name,
                                                 project_id=project.id,
                                                 uploaded=True)
            progress.write_directory_status(directory_status)


def _run_upload_multithreaded(api_instance, sequencing_run, run_id, directory_status, upload_mode, max_threads):
    """
    Starts a threading pool with thread count defined in config. Threadpool then uploads samples simultaneously
    :param api_instance: api instance should have already been initialized
    :param sequencing_run: sequencing run to upload
    :param run_id: run id to use for upload
    :param directory_status:
    :param upload_mode:
    :param max_threads: number of threads to use
    :return:
    """

    def _run_upload(d_dict, sequence_run_id, u_mode):
        """
        Do the data upload
        :param d_dict: dictionary containing the "project" and "sample"
        :param sequence_run_id: run id to upload with
        :return:
        """
        project_data = d_dict["project"]
        sample_data = d_dict["sample"]
        logging.debug("Processing queue item for project {} sample {}".format(project_data.id,
                                                                              sample_data.sample_name))

        api_instance.send_sequence_files(sequence_file=sample_data.sequence_file,
                                         sample_name=sample_data.sample_name,
                                         project_id=project_data.id,
                                         upload_id=sequence_run_id,
                                         upload_mode=u_mode)
        return d_dict

    def _set_sample_uploaded(d_status, s_name, p_id):
        d_status.set_sample_uploaded(sample_name=s_name,
                                     project_id=p_id,
                                     uploaded=True)
        progress.write_directory_status(d_status)

    # Put all the project/samples into a single list so the thread pool can assign them easier
    # filter out runs that have already been uploaded (skip)
    all_samples = []
    for project in sequencing_run.project_list:
        for sample in project.sample_list:
            if sample.skip:
                logging.info("Skipping Sample {} on Project {}, already uploaded."
                             "".format(sample.sample_name, project.id))
            else:
                all_samples.append({"project": project, "sample": sample})

    logging.info("Starting Multithreaded upload of {} samples with {} threads".format(len(all_samples), max_threads))

    # Keep track of the first exception, if an exception occurs
    upload_exception = None

    # Create a executor for our thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # future_to_upload is a list of future uploads (this starts the threads)
        future_to_upload = {executor.submit(_run_upload, data, run_id, upload_mode): data for data in all_samples}
        # as uploads/futures finish, they will be be handled here
        for future in concurrent.futures.as_completed(future_to_upload):
            try:
                # attempt to get the result. If an exception occurred, it will be thrown here
                data_dict = future.result()
                # Write to the directory status file. This part is sequential in order of completed
                sample_name = data_dict["sample"].sample_name
                project_id = data_dict["project"].id
                _set_sample_uploaded(directory_status, sample_name, project_id)
            except concurrent.futures.CancelledError:
                # In the case that we signaled cancellations, all futures will end up here.
                logging.debug("Upload on this thread canceled")
            except Exception as e:
                # If an exception occurs during upload capture it and cancel all futures
                upload_exception = e
                logging.error("Exception occured during upload. Canceling other uploads in threading pool.")
                for ff in future_to_upload:
                    ff.cancel()

    logging.info("Finished Multithreading, all threads closed")

    # Raise the exception so it can be handled at a higher level
    if upload_exception:
        raise upload_exception


def send_project(project):
    """
    Validates and sends a project object to IRIDA

    :param project: Project object
    :return: None
    """
    # get api
    api_instance = _get_api_instance()

    # validate project object
    try:
        model_validator.validate_send_project(project)
    except model.exceptions.ModelValidationError:
        raise api.exceptions.IridaResourceError("Project is invalid: check your project name and description")

    try:
        api_instance.send_project(project)
    except api.exceptions.IridaResourceError as e:
        logging.error("Failed to send project to IRIDA")
        raise e
    except api.exceptions.IridaConnectionError as e:
        logging.error("Failed to send project to IRIDA")
        raise e


def get_upload_modes():
    """
    Returns all the upload modes the api supports for sequence files

    :return: List of Strings
    """
    return api.UPLOAD_MODES


def get_default_upload_mode():
    """
    Returns the string for the default upload mode

    :return: Default upload mode string
    """
    return api.MODE_DEFAULT
