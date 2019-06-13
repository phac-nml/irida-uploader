import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore

from pprint import pformat

from core import cli_entry, parsing_handler
from parsers import exceptions


class StatusThread(QtCore.QThread):
    """
    This class handles the arguments for uploading
    Is used an a separate thread to upload so that the GUI is still responsive while uploading
    """
    def __init__(self):
        super().__init__()
        self._directory = ""
        self._result = None

    def set_vars(self, directory):
        """
        Sets the variables in the object to the ones passed in
        :return:
        """
        self._directory = directory

    def get_result(self):
        """
        returns the result that was returned after run was called.
        :return: DirectoryStatus object
        """
        return self._result

    def run(self):
        """
        This runs when the threads start call is done
        :return: None
        """
        self._result = parsing_handler.get_run_status(self._directory)
        pass


class ParseThread(QtCore.QThread):
    """
    This class handles the arguments for uploading
    Is used an a separate thread to upload so that the GUI is still responsive while uploading
    """
    def __init__(self):
        super().__init__()
        self._directory = ""
        self._run = None
        self._error = None

    def set_vars(self, directory):
        """
        Sets the variables in the object to the ones passed in
        :return:
        """
        self._directory = directory

    def get_run(self):
        return self._run

    def get_error(self):
        return self._error

    def run(self):
        """
        This runs when the threads start call is done
        :return:
        """
        try:
            self._run = parsing_handler.parse_and_validate(self._directory)
        except exceptions.DirectoryError as e:
            # Directory was not valid for some reason
            full_error = "GUI: ERROR! An error occurred with directory '{}', with message: {}".format(e.directory,
                                                                                                      e.message)
            logging.error(full_error)
            self._error = e.message
            self._run = None
        except exceptions.ValidationError as e:
            # Sequencing Run / SampleSheet was not valid for some reason
            error_msg = "GUI: ERROR! Errors occurred during validation with message: {}".format(e.message)
            logging.error(error_msg)
            error_list_msg = "GUI: Error list: " + pformat(e.validation_result.error_list)
            logging.error(error_list_msg)
            full_error = "Error: " + e.message + "\nError List:\n"
            for err in e.validation_result.error_list:
                full_error = full_error + str(err) + "\n"
            self._error = full_error
            self._run = None

        pass


class UploadThread(QtCore.QThread):
    """
    This class handles the arguments for uploading
    Is used an a separate thread to upload so that the GUI is still responsive while uploading
    """
    def __init__(self):
        super().__init__()
        self._run_dir = ""
        self._force_state = False
        self._exit_return = None

    def set_vars(self, run_dir, force_state):
        """
        Sets the variables in the object to the ones passed in
        :param run_dir:
        :param force_state:
        :return:
        """
        self._run_dir = run_dir
        self._force_state = force_state

    def run(self):
        """
        This runs when the threads start call is done
        :return:
        """
        self._exit_return = cli_entry.upload_run_single_entry(self._run_dir, self._force_state)
        pass

    def get_exit_code(self):
        if self._exit_return:
            return self._exit_return.exit_code

    def get_exit_error(self):
        if self._exit_return:
            return self._exit_return.error


class QtHandler(logging.Handler):
    """
    Custom logging handler
    Overrides the default emit function to call the message writers emit instead

    A non Qt object cannot execute Qt emits so we wrap this handler around the MessageWriter
    """
    # def __init__(self, message_writer):
    def __init__(self):
        logging.Handler.__init__(self)
        # self._message_writer = message_writer
        self._message_writer = MessageWriter()

    def emit(self, record):
        record = self.format(record)
        if record:
            self._message_writer.write(record)

    @property
    def message_writer(self):
        return self._message_writer


class MessageWriter(QtCore.QObject):
    """
    Wrapper the logging handler can use to emit a message,
    This object is needed to hold the messageWritten signal that needs to belong to Qt
    """
    messageWritten = QtCore.pyqtSignal(str)

    def flush(self):
        pass

    def write(self, msg):
        self.messageWritten.emit(msg)
