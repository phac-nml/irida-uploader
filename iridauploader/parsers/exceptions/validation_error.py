class ValidationError(Exception):
    """
    An exception to be raised validation errors happen while parsing

    includes a ValidationResult object with list of errors that occurred
    """
    def __init__(self, message, validation_result):
        """Initialize a SampleError.

        Args:
            message: the summary message that's causing the error.
            validation_result: a ValidationResult object with list of errors that occurred
        """
        self._message = message
        self._validation_result = validation_result

    @property
    def message(self):
        return self._message

    @property
    def validation_result(self):
        return self._validation_result

    def __str__(self):
        return self.message
