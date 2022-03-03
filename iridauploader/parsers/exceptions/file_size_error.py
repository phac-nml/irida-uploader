class FileSizeError(Exception):
    """An exception raised when errors are encountered while validating the minimum file size of files

    """
    def __init__(self, message, object):
        """Initialize a FileSizeError.

        Args:
            message: a summary message that's causing the error.
            object: the object that has the validation error
        """
        self._message = message
        self._object = object

    @property
    def message(self):
        return self._message

    @property
    def object(self):
        return self._object

    def __str__(self):
        return str(self.message)
