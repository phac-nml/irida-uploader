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

    @property
    def directory(self):
        return self._directory

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
