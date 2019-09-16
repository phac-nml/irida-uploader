EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0


class ExitReturn:
    """
    When the program exits it returns this class.
    Contains an exit code (0 or 1)
    if exiting with error, an Exception object will be included

    This acts as a wrapper for exit status's so that exception info can be captured in gui, but cli can still return 0/1
    """

    def __init__(self, exit_code, error=None):
        self._exit_code = exit_code
        if type(error) is str:
            # If a string is given as the error, wrap in an exception.
            # todo: when reworking exceptions, this will likely be something that could be improved
            error = Exception(error)
        self._error = error

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def error(self):
        return self._error
