class DirectoryStatus:
    """
    When looking for runs in a directory (or list of directories) this object is used to
    contain the relevant data.
    """

    # States that are valid for the status field

    # New runs, ready to upload
    NEW = 'new'
    # Used when a run directory does not have the base requirements to act as a run
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
        INVALID,
        PARTIAL,
        ERROR,
        COMPLETE
    ]

    def __init__(self, directory):
        """
        :param directory: Directory of a potential run
        status: status of the directory: 'new', 'partial', 'complete', 'invalid'
        message: Used when run is invalid,
        """
        self._directory = directory
        self._status = None
        self._message = None
        self._run_id = None
        self._sample_status_list = None

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

    class SampleStatus:
        """
        Contains a sample name, project id and upload status
        This is used to simply jsonify the directory status info
        """

        def __init__(self, sample_name, project_id):
            """
            Init SampleStatus Object, initializes uploaded to False

            :param sample_name: sample.sample_name from Sample object
            :param project_id: project.id from Project object
            """
            self._sample_name = sample_name
            self._project_id = project_id
            self._uploaded = False

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
                "Sample Name": self.sample_name,
                "Project ID": self.project_id,
                "Uploaded": str(self.uploaded)
            }
