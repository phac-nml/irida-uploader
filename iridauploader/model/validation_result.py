class ValidationResult:

    def __init__(self):
        self._error_list = []

    def add_error(self, error):
        self._error_list.append(error)

    def error_count(self):
        return len(self._error_list)

    @property
    def error_list(self):
        return self._error_list

    def is_valid(self):
        return self.error_count() == 0
