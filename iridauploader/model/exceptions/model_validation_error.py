class ModelValidationError(Exception):
    """An exception raised when errors are encountered while validating the object model.

    """
    def __init__(self, message, object):
        """Initialize a ModelValidationError.

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
