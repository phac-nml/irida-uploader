class DirectoryStatus:
    """
    When looking for runs in a directory (or list of directories) this object is used to
    contain the relevant data.
    """

    # States that are valid for the status field
    NEW = 'new'
    INVALID = 'invalid'
    PARTIAL = 'partial'
    ERROR = 'error'
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
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, message):
        self._message = message

    def is_new(self):
        return self.status == self.NEW

    def is_invalid(self):
        return self.status == self.INVALID

    def is_partial(self):
        return self.status == self.PARTIAL

    def is_error(self):
        return self.status == self.ERROR

    def is_complete(self):
        return self.status == self.COMPLETE
