import logging
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtCore as QtCore

from iridauploader.core import api_handler


class QtHandler(logging.Handler):
    """
    Custom logging handler
    Overrides the default emit function to call the message writers emit instead

    A non Qt object cannot execute Qt emits so we wrap this handler around the MessageWriter
    """
    def __init__(self):
        logging.Handler.__init__(self)
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


def is_connected_to_irida():
    try:
        api_handler.initialize_api_from_config()
        return True
    except Exception:
        return False
