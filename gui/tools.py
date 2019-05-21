import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore

from core import cli_entry


class UploadThread(QtCore.QThread):
    """
    This class handles the arguments for uploading
    Is used an a separate thread to upload so that the GUI is still responsive while uploading
    """
    def __init__(self):
        super().__init__()
        self._run_dir = ""
        self._force_state = False

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
        cli_entry.upload_run_single_entry(self._run_dir, self._force_state)
        pass


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
