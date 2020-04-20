class SequenceFileError(Exception):
    """An exception that's raised when errors are encountered with a sequence file.

    Examples include when files cannot be found for samples that are in the sample
    sheet, or when the server rejects a file during upload.
    """
    def __init__(self, message):
        """Initialize a SequenceFileError.

        Args:
            message: a summary message of the error.
        """
        self._message = message

    @property
    def message(self):
        return self._message

    def __str__(self):
        return self.message
