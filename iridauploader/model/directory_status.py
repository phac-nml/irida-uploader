import time

import iridauploader.config as config


class DirectoryStatus:
    """
    When looking for runs in a directory (or list of directories) this object is used to
    contain the relevant data.
    """

    # States that are valid for the status field

    # New runs, ready to upload
    NEW = 'new'
    # Delayed runs are new runs that have been discovered as new, but must wait before upload
    # When a run is found with the Delayed status, The uploader will check if enough time has passed to start the upload
    DELAYED = 'delayed'
    # Invalid is used when a run directory does not have the base requirements to act as a run
    # Never written to a status file
    INVALID = 'invalid'
    # Parsing/Upload has started/partially completed for this run
    PARTIAL = 'partial'
    # Parsing/Upload has stopped because of some error.
    ERROR = 'error'
    # Parsing/Upload has completed successfully
    COMPLETE = 'complete'

    VALID_STATUS_LIST = [
        NEW,
        DELAYED,
        INVALID,
        PARTIAL,
        ERROR,
        COMPLETE
    ]

    # Status field for a sequencing run
    JSON_STATUS_FIELD = "Upload Status"
    JSON_DIRECTORY_FIELD = "Directory"
    JSON_DATE_TIME_FIELD = "Date Time"
    JSON_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
    JSON_RUN_ID_FIELD = "Run ID"
    JSON_IRIDA_INSTANCE_FIELD = "IRIDA Instance"
    JSON_MESSAGE_FIELD = "Message"
    JSON_SAMPLES_UPLOADED_FIELD = "Sample Status"

    def __init__(self, directory, status=NEW, message=None):
        """
        :param directory: Directory of a potential run
        :param status: Default = NEW, must be one of VALID_STATUS_LIST
        :param message: Text to be added to the status file
        """
        self._directory = directory
        # use the status validation method
        self.status = status
        self._message = message
        self._run_id = None
        self._sample_status_list = None
        self._time = None
        self._irida_instance = None

    def init_file_status_list_from_sequencing_run(self, sequencing_run):
        """
        Creates list of SampleStatus objects (project/sample pairs w/ upload status) and sets to uploaded=False
        :param sequencing_run:
        :return:
        """
        self._sample_status_list = []
        for project in sequencing_run.project_list:
            for sample in project.sample_list:
                self._sample_status_list.append(self.SampleStatus(sample.sample_name, project.id))

    def set_sample_uploaded(self, sample_name, project_id, uploaded):
        """
        Finds the SampleStatus object in sample_status_list and updates uploaded to True
        :param sample_name:
        :param project_id:
        :param uploaded:
        :return:
        """
        for status in self._sample_status_list:
            if status.equals(sample_name=sample_name, project_id=project_id):
                status.uploaded = uploaded

    def sample_status_to_dict(self):
        """
        Creates list of dicts that can be easily written as json
        :return:
        """
        if self._sample_status_list is None:
            return None
        else:
            return [o.to_dict() for o in self._sample_status_list]

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, directory):
        self._directory = directory

    @property
    def run_id(self):
        return self._run_id

    @run_id.setter
    def run_id(self, run_id):
        self._run_id = run_id

    @property
    def status(self):
        """
        status property, setter is overridden by @status.setter
        :return: status
        """
        return self._status

    @status.setter
    def status(self, status):
        """
        Status setter
        Only accepts status's from the predefined VALID_STATUS_LIST
        :param status: Status to set on object
        :return:
        """
        if status not in DirectoryStatus.VALID_STATUS_LIST:
            raise Exception("Invalid status written to DirectoryStatus object.")
        self._status = status

    def status_equals(self, status):
        """
        Checks if status on object is the same as status given.
        Only accepts status's from the predefined VALID_STATUS_LIST
        :param status: check given status against current status
        :return:
        """
        if status not in DirectoryStatus.VALID_STATUS_LIST:
            raise Exception("Invalid status '{}' used for comparison.".format(status))
        return self._status == status

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    @property
    def time(self):
        if self._time is None:
            return None
        return self._time

    @time.setter
    def time(self, formatted_time):
        if formatted_time is None:
            self._time = None
        elif type(formatted_time) is not str:
            raise TypeError("Time given is not a string: {}".format(formatted_time))
        else:
            self._time = time.strptime(formatted_time, self.JSON_DATE_TIME_FORMAT)

    @property
    def irida_instance(self):
        if self._irida_instance is None:
            self._irida_instance = config.read_config_option('base_url')
        return self._irida_instance

    @irida_instance.setter
    def irida_instance(self, irida_instance):
        self._irida_instance = irida_instance

    def get_sample_status_list(self):
        return self._sample_status_list

    def to_json_dict(self):
        sample_status_dict = self.sample_status_to_dict()

        json_dict = {
            self.JSON_STATUS_FIELD: self.status,
            self.JSON_DIRECTORY_FIELD: self.directory,
            self.JSON_MESSAGE_FIELD: self.message,
            self.JSON_DATE_TIME_FIELD: time.strftime(self.JSON_DATE_TIME_FORMAT),  # Generate a new timestamp
            self.JSON_RUN_ID_FIELD: self.run_id if self.run_id is not None else "",
            self.JSON_IRIDA_INSTANCE_FIELD: self.irida_instance,
            self.JSON_SAMPLES_UPLOADED_FIELD: sample_status_dict if sample_status_dict is not None else "",
        }

        return json_dict

    @staticmethod
    def init_from_json_dict(json_dict, directory=None):
        if directory is not None:
            new_directory_status = DirectoryStatus(directory)
        else:
            new_directory_status = DirectoryStatus(DirectoryStatus._get_field_or_none(
                json_dict, DirectoryStatus.JSON_DIRECTORY_FIELD))
        new_directory_status.status = DirectoryStatus._get_field_or_none(
            json_dict, DirectoryStatus.JSON_STATUS_FIELD)
        new_directory_status.message = DirectoryStatus._get_field_or_none(
            json_dict, DirectoryStatus.JSON_MESSAGE_FIELD)
        new_directory_status.time = DirectoryStatus._get_field_or_none(
            json_dict, DirectoryStatus.JSON_DATE_TIME_FIELD)
        new_directory_status.run_id = DirectoryStatus._get_field_or_none(
            json_dict, DirectoryStatus.JSON_RUN_ID_FIELD)
        new_directory_status.irida_instance = DirectoryStatus._get_field_or_none(
            json_dict, DirectoryStatus.JSON_IRIDA_INSTANCE_FIELD)

        new_directory_status._sample_status_list = DirectoryStatus._get_sample_status_list_from_json(
            json_dict, DirectoryStatus.JSON_SAMPLES_UPLOADED_FIELD)

        return new_directory_status

    @staticmethod
    def _get_field_or_none(json_dict, field):
        return json_dict[field] if field in json_dict else None

    @staticmethod
    def _get_sample_status_list_from_json(json_dict, samples_field):
        new_sample_status_list = []

        samples_uploaded_field = DirectoryStatus._get_field_or_none(
            json_dict, samples_field)

        if samples_uploaded_field is not None:
            for sample_dict in json_dict[samples_field]:
                new_sample_status_list.append(DirectoryStatus.SampleStatus(
                    sample_name=sample_dict[DirectoryStatus.SampleStatus.SAMPLE_NAME_FIELD],
                    project_id=sample_dict[DirectoryStatus.SampleStatus.PROJECT_ID_FIELD],
                    uploaded=sample_dict[DirectoryStatus.SampleStatus.UPLOADER_FIELD],
                ))

        return new_sample_status_list

    class SampleStatus:
        """
        Contains a sample name, project id and upload status
        This is used to simply jsonify the directory status info
        """

        SAMPLE_NAME_FIELD = "Sample Name"
        PROJECT_ID_FIELD = "Project ID"
        UPLOADER_FIELD = "Uploaded"

        def __init__(self, sample_name, project_id, uploaded=False):
            """
            Init SampleStatus Object, initializes uploaded to False

            :param sample_name: sample.sample_name from Sample object
            :param project_id: project.id from Project object
            """
            self._sample_name = sample_name
            self._project_id = project_id
            # if `uploaded` is a string, convert it to a boolean
            if type(uploaded) is str:
                uploaded = uploaded.lower() in ['true', '1', 't', 'y', 'yes']
            self._uploaded = uploaded

        @property
        def uploaded(self):
            return self._uploaded

        @uploaded.setter
        def uploaded(self, uploaded):
            self._uploaded = uploaded

        @property
        def sample_name(self):
            return self._sample_name

        @property
        def project_id(self):
            return self._project_id

        def equals(self, sample_name, project_id):
            """
            Verifies sample id and project id match current instance.
            Upload status bool is not inspected
            :param sample_name:
            :param project_id:
            :return:
            """
            return self.sample_name == sample_name and self.project_id == project_id

        def to_dict(self):
            """
            Creates and returns a json ready dict that gets used when updating the status file
            :return:
            """
            return {
                self.SAMPLE_NAME_FIELD: self.sample_name,
                self.PROJECT_ID_FIELD: self.project_id,
                self.UPLOADER_FIELD: str(self.uploaded)
            }
