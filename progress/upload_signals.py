from PyQt5 import QtCore


class QSignalWorker(QtCore.QObject):
    progress_signal = QtCore.pyqtSignal(dict)

    def send_progress(self, data):
        self.progress_signal.emit(data)


signal_worker = QSignalWorker()


def send_progress(data):
    signal_worker.send_progress(data)
