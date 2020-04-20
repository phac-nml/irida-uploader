# todo: an improved code flow may include another modules for handling pubsub, and having the QSignalWorker sub to that
#  that way, the QSignalWorker will only get imported from gui code, and not api code (which would only load the new
#  pubsub module)

import sys
# Check if the PyQt5 is installed
GUI_PKG_INSTALLED = 'PyQt5' in sys.modules

# Don't import gui stuff if we are doing command line only
if GUI_PKG_INSTALLED:
    from PyQt5 import QtCore


class ProgressData:
    """
    A class to wrap upload progress data with standardised getters/setters
    """
    def __init__(self, sample, project, progress):
        self._sample = sample
        self._project = project
        self._progress = progress

    @property
    def sample(self):
        return self._sample

    @property
    def project(self):
        return self._project

    @property
    def progress(self):
        return self._progress


# int to none so send_progress knows it exists
signal_worker = None

# Class does not need to be defined unless gui is loaded
if GUI_PKG_INSTALLED:
    class QSignalWorker(QtCore.QObject):
        # we are sending ProgressData type data
        progress_signal = QtCore.pyqtSignal(ProgressData)

        def send_progress(self, data):
            self.progress_signal.emit(data)

    signal_worker = QSignalWorker()


def send_progress(data):
    # Only send progress if gui is loaded
    if GUI_PKG_INSTALLED:
        signal_worker.send_progress(data)
