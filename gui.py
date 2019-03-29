from PyQt5 import QtWidgets, QtCore
import logging
import sys

from core import logger, cli_entry
from config import config
import global_settings


class QtHandler(logging.Handler):
    def __init__(self, message_writer):
        logging.Handler.__init__(self)
        self._message_writer = message_writer

    def emit(self, record):
        record = self.format(record)
        if record:
            self._message_writer.write(record)


class MessageWriter(QtCore.QObject):
    messageWritten = QtCore.pyqtSignal(str)

    def flush(self):
        pass

    def write(self, msg):
        self.messageWritten.emit(msg)


class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MyDialog")

        # variables
        self._run_dir = ""
        self._config_file = ""
        # directory
        self._dir_label = QtWidgets.QLabel(self)
        self._dir_label.setText("Sequence Run Directory")
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Directory")
        # config
        self._config_label = QtWidgets.QLabel(self)
        self._config_label.setText("Config File")
        self._config_line = QtWidgets.QLineEdit(self)
        self._config_line.setReadOnly(True)
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Select Config File")
        # force upload
        self._force_checkbox = QtWidgets.QCheckBox(self)
        self._force_checkbox.setText("Force Upload")
        self._force_checkbox.setChecked(False)
        self._force_state = False
        # upload
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')

        # Setup logger
        message_writer = MessageWriter()
        handler = QtHandler(message_writer)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        logger.root_logger.addHandler(handler)
        self._console = QtWidgets.QPlainTextEdit(self)
        message_writer.messageWritten.connect(self.write_log_and_redraw)
        self._my_thread = ExecuteThread()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        # Directory
        dir_layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._dir_label)
        dir_layout.addWidget(self._dir_line)
        dir_layout.addWidget(self._dir_button)
        layout.addLayout(dir_layout)
        # Config
        layout.addWidget(self._config_label)
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_line)
        config_layout.addWidget(self._config_button)
        layout.addLayout(config_layout)
        # Force Upload
        layout.addWidget(self._force_checkbox)
        # Upload
        layout.addWidget(self._upload_button)
        # Text box logger
        layout.addWidget(self._console)
        # set layout
        self.setLayout(layout)
        self.setGeometry(300, 300, 1200, 1200)

        # Connect signal to slot
        self._dir_button.clicked.connect(self.open_dir)
        self._config_button.clicked.connect(self.select_config)
        self._force_checkbox.stateChanged.connect(self.click_force_upload)
        self._upload_button.clicked.connect(self.start_upload)
        # connect running upload thread finishing to finish function
        self._my_thread.finished.connect(self.finished_upload)

    def write_log_and_redraw(self, text):
        self._console.appendPlainText(text)
        self._console.repaint()

    def open_dir(self):
        logging.debug("GUI: open_dir clicked")
        self._run_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self._dir_line.setText(self._run_dir)
        logging.debug("GUI: result: " + self._run_dir)

    def select_config(self):
        logging.debug("GUI: select_config clicked")
        self._config_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Config File", "", "Config Files (*.conf)")
        self._config_line.setText(self._config_file)
        global_settings.config_file = self._config_file
        logging.debug("GUI: result: " + self._config_file)

    def click_force_upload(self, state):
        logging.debug("GUI: click_force_upload clicked")
        if state == QtCore.Qt.Checked:
            logging.debug("GUI: set force upload to TRUE")
            self._force_state = True
        else:
            logging.debug("GUI: set force upload to False")
            self._force_state = False

    def start_upload(self):
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._force_checkbox.setEnabled(False)
        # init / re-init config with config file selected
        config.setup()
        # start upload
        self._my_thread.set_vars(self._run_dir, self._force_state)
        self._my_thread.start()

    def finished_upload(self):
        logging.debug("GUI: finished_upload called")
        # Unlock GUI
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._force_checkbox.setEnabled(True)
        # reset directory
        self._run_dir = ""
        self._dir_line.setText("")
        # reset checkbox
        self._force_state = False
        self._force_checkbox.setChecked(False)


class ExecuteThread(QtCore.QThread):
    def __init__(self):
        super().__init__()

    def set_vars(self, run_dir, force_state):
        self._run_dir = run_dir
        self._force_state = force_state

    def run(self):
        cli_entry.validate_and_upload_single_entry(self._run_dir, self._force_state)
        pass


def main():
    app = QtWidgets.QApplication(["IRIDA Uploader"])
    dlg = MyDialog()
    dlg.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
