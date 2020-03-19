class DirectoryError(Exception):
    """
    This error is thrown when the parser cannot access a directory
    """

    def __init__(self, message, directory):
        """Initialize a IridaResourceError.

        Args:
            message: the summary message that's causing the error.
        """
        self._message = message
        self._directory = directory

    @property
    def message(self):
        return self._message

    @property
    def directory(self):
        return self._directory
