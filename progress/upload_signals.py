from PyQt5 import QtCore


class QSignalWorker(QtCore.QObject):
    file_progress_signal = QtCore.pyqtSignal(float)
    sample_progress_signal = QtCore.pyqtSignal(float)
    project_progress_signal = QtCore.pyqtSignal(float)
    current_file_signal = QtCore.pyqtSignal(str)
    current_sample_signal = QtCore.pyqtSignal(str)
    current_project_signal = QtCore.pyqtSignal(str)

    def send_file_percent(self, percent):
        self.file_progress_signal.emit(percent)

    def send_sample_percent(self, percent):
        print("sample percent : " + str(percent))
        self.sample_progress_signal.emit(percent)

    def send_project_percent(self, percent):
        print("project percent : " + str(percent))
        self.project_progress_signal.emit(percent)

    def send_current_file(self, text):
        self.current_file_signal.emit(text)

    def send_current_sample(self, text):
        self.current_sample_signal.emit(text)

    def send_current_project(self, text):
        self.current_project_signal.emit(text)


signal_worker = QSignalWorker()


def send_file_percent(percent):
    signal_worker.send_file_percent(percent)


def send_sample_percent(percent):
    signal_worker.send_sample_percent(percent)


def send_project_percent(percent):
    signal_worker.send_project_percent(percent)


def send_current_file(text):
    signal_worker.send_current_file(text)


def send_current_sample(text):
    signal_worker.send_current_sample(text)


def send_current_project(text):
    signal_worker.send_current_project(text)
