# todo: an improved code flow may include another modules for handling pubsub, and having the QSignalWorker sub to that
#  that way, the QSignalWorker will only get imported from gui code, and not api code (which would only load the new
#  pubsub module)

import sys
# Check if the PyQt5 is installed
GUI_PKG_INSTALLED = 'PyQt5' in sys.modules

# Don't import gui stuff if we are doing command line only
if GUI_PKG_INSTALLED:
    from PyQt5 import QtCore


signal_worker = None

# Class does not need to be defined unless gui is loaded
if GUI_PKG_INSTALLED:
    class QSignalWorker(QtCore.QObject):
        progress_signal = QtCore.pyqtSignal(dict)

        def send_progress(self, data):
            self.progress_signal.emit(data)

    signal_worker = QSignalWorker()


def send_progress(data):
    # Only send progress if gui is loaded
    if GUI_PKG_INSTALLED:
        signal_worker.send_progress(data)
