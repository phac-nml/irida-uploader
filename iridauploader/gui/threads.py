import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore

from pprint import pformat

from iridauploader.core import upload, parsing_handler, exit_return, upload_helpers
from iridauploader.parsers import exceptions


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
        self._parse_as_partial = False
        self._run = None
        self._error = None

    def set_vars(self, directory, parse_as_partial):
        """
        Sets the variables in the object to the ones passed in
        :return:
        """
        self._directory = directory
        self._parse_as_partial = parse_as_partial

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
            status = parsing_handler.get_run_status(self._directory)
            seq_run = parsing_handler.parse_and_validate(self._directory)
            if self._parse_as_partial:
                seq_run = upload_helpers.set_uploaded_samples_to_skip(seq_run, status.get_sample_status_list())
            self._run = seq_run

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
            full_error = "GUI: ERROR! An unknown error occurred while parsing: {}".format(str(e))
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
        self._upload_mode = None
        self._exit_return = None
        self._partial_continue = False

    def set_vars(self, run_dir, upload_mode, partial_continue):
        """
        Sets the variables in the object to the ones passed in
        :param run_dir:
        :param upload_mode:
        :param partial_continue:
        :return:
        """
        self._run_dir = run_dir
        self._upload_mode = upload_mode
        self._partial_continue = partial_continue

    def run(self):
        """
        This runs when the threads start call is done

        When uploading, the default is to upload with force_upload=True,
          when continuing a partial upload, force_upload=False instead
          s.t. we ignore delay logic and simplify earlier run parse logic
        :return:
        """

        force_upload = not self._partial_continue
        self._exit_return = upload.upload_run_single_entry(directory=self._run_dir,
                                                           force_upload=force_upload,
                                                           upload_mode=self._upload_mode,
                                                           continue_upload=self._partial_continue)
        pass

    def is_success(self):
        if self._exit_return:
            return self._exit_return.exit_code == exit_return.EXIT_CODE_SUCCESS

    def get_exit_error(self):
        if self._exit_return:
            return self._exit_return.error
