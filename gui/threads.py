import logging
import os
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore

from pprint import pformat

from core import cli_entry, parsing_handler, exit_return
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
        except exceptions.SampleSheetError as e:
            # SampleSheet was not valid for some reason
            error_msg = "GUI: ERROR! Errors occurred during parsing with message: {}".format(e.message)
            logging.error(error_msg)
            self._error = "Errors occurred during parsing `{}` with message: {}".format(e.errors, e.message)
            self._run = None
        except exceptions.SequenceFileError as e:
            # Sequence Files were invalid for some reason
            full_error = "GUI: ERROR! An error occurred while parsing: {}".format(e.message)
            logging.error(full_error)
            self._error = e.message
            self._run = None
        except Exception as e:
            # Some other error occurred
            full_error = "GUI: ERROR! An error occurred while parsing: {}".format(str(e))
            logging.error(full_error)
            self._error = "ERROR! An error occurred while parsing: {}".format(str(e))
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
        self._read_only = False
        self._exit_return = None

    def set_vars(self, run_dir, force_state, read_only):
        """
        Sets the variables in the object to the ones passed in
        :param run_dir:
        :param force_state:
        :param read_only:
        :return:
        """
        self._run_dir = run_dir
        self._force_state = force_state
        self._read_only = read_only

    def run(self):
        """
        This runs when the threads start call is done
        :return:
        """
        # Verify directory is readable/writable before upload
        if self._read_only:
            # Even in read only the directory still needs to be readable
            if not os.access(self._run_dir, os.R_OK):  # cannot read the upload directory
                error_reason = "ERROR! Specified directory is not readable: {} , ".format(self._run_dir)
                logging.error(error_reason)
                self._exit_return = exit_return.ExitReturn(exit_return.EXIT_CODE_ERROR, error_reason)
                return
        else:
            if not os.access(self._run_dir, os.W_OK):  # Cannot write to upload directory
                error_reason = "ERROR! Specified directory is not writable: {} , ".format(self._run_dir) + \
                               "If this is the correct directory, either make it writable or use read-only mode."
                logging.error(error_reason)
                self._exit_return = exit_return.ExitReturn(exit_return.EXIT_CODE_ERROR, error_reason)
                return

        self._exit_return = cli_entry.upload_run_single_entry(self._run_dir, self._force_state, self._read_only)
        pass

    def is_success(self):
        if self._exit_return:
            return self._exit_return.exit_code == exit_return.EXIT_CODE_SUCCESS

    def get_exit_error(self):
        if self._exit_return:
            return self._exit_return.error
