from PyQt5 import QtWidgets
import logging

from core import logger, cli_entry
from config import config
import global_settings


class QPlainTextEditLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
        self.widget.repaint()


class MyDialog(QtWidgets.QDialog, QPlainTextEditLogger):
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
        # upload
        self._upload_label = QtWidgets.QLabel(self)
        self._upload_label.setText("Upload Sequence Run")
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')

        log_text_box = QPlainTextEditLogger()
        log_text_box.setFormatter(logging.Formatter(logger.log_format, datefmt='%H:%M:%S'))
        log_text_box.setLevel(logging.INFO)
        logger.root_logger.addHandler(log_text_box)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        # Directory
        layout.addWidget(self._dir_label)
        layout.addWidget(self._dir_line)
        layout.addWidget(self._dir_button)
        # Config
        layout.addWidget(self._config_label)
        layout.addWidget(self._config_line)
        layout.addWidget(self._config_button)
        # Upload
        layout.addWidget(self._upload_label)
        layout.addWidget(self._upload_button)
        layout.addWidget(log_text_box.widget)
        # set layout
        self.setLayout(layout)
        self.setGeometry(300, 300, 1200, 1200)

        # Connect signal to slot
        self._dir_button.clicked.connect(self.open_dir)
        self._config_button.clicked.connect(self.select_config)
        self._upload_button.clicked.connect(self.start_upload)

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

    def start_upload(self):
        logging.debug("GUI: start_upload clicked")
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        config.setup()
        cli_entry.validate_and_upload_single_entry(self._run_dir)
        self.finished_upload()

    def finished_upload(self):
        logging.debug("GUI: finished_upload called")
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)


if __name__ == '__main__':
    app = None
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication([])
    dlg = MyDialog()
    dlg.show()
    dlg.raise_()
    if app:
        app.exec_()
