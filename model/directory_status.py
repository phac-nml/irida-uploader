class DirectoryStatus:
    """
    When looking for runs in a directory (or list of directories) this object is used to
    contain the relevant data.
    """

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
