class IridaResourceError(Exception):
    """
    This error is thrown when the api tries to get a resource route that doesn't exist
    or send data to a resource route that does not exist

    All calls to the api should expect this error
    """

    def __init__(self, message, resource_id=None):
        """Initialize a IridaResourceError.

        Args:
            message: the summary message that's causing the error.
            errors: a more detailed list of errors.
        """
        self._message = message
        self._resource_id = resource_id

    @property
    def message(self):
        return self._message

    @property
    def resource_id(self):
        return self._resource_id

    def __str__(self):
        return self.message
