from PyQt5 import QtWidgets, QtCore
import logging
import sys

from core import logger, cli_entry, api_handler
from config import config
from parsers import supported_parsers
from progress import signal_worker


class QtHandler(logging.Handler):
    """
    Custom logging handler
    Overrides the default emit function to call the message writers emit instead

    A non Qt object cannot execute Qt emits so we wrap this handler around the MessageWriter
    """
    def __init__(self, message_writer):
        logging.Handler.__init__(self)
        self._message_writer = message_writer

    def emit(self, record):
        record = self.format(record)
        if record:
            self._message_writer.write(record)


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


class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MyDialog")

        self.config_dlg = ConfigDialog(self)

        # Initialize thread to execute uploader
        self._upload_thread = UploadThread()

        # internal variables
        self._run_dir = ""
        self._config_file = ""

        ###################################
        #           QT Objects            #
        ###################################

        # directory
        self._dir_label = QtWidgets.QLabel(self)
        self._dir_label.setText("Sequence Run Directory")
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Directory")
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        # force upload
        self._force_checkbox = QtWidgets.QCheckBox(self)
        self._force_checkbox.setText("Force Upload")
        self._force_checkbox.setChecked(False)
        self._force_state = False
        # upload
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')
        # Upload Progress
        self._current_project_label = QtWidgets.QLabel("Current Project:")
        self._current_project = QtWidgets.QLineEdit()
        self._current_project.setReadOnly(True)
        self._project_progress_label = QtWidgets.QLabel("Project Upload Progress")
        self._project_progress = QtWidgets.QProgressBar()
        self._current_sample_label = QtWidgets.QLabel("Current Sample:")
        self._current_sample = QtWidgets.QLineEdit()
        self._current_sample.setReadOnly(True)
        self._sample_progress_label = QtWidgets.QLabel("Sample Upload Progress")
        self._sample_progress = QtWidgets.QProgressBar()
        self._current_file_label = QtWidgets.QLabel("Current File:")
        self._current_file = QtWidgets.QLineEdit()
        self._current_file.setReadOnly(True)
        self._file_progress_label = QtWidgets.QLabel("File Upload Progress")
        self._file_progress = QtWidgets.QProgressBar()

        # logger initialization
        message_writer = MessageWriter()
        handler = QtHandler(message_writer)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        logger.root_logger.addHandler(handler)
        self._console = QtWidgets.QPlainTextEdit(self)
        self._console.setReadOnly(True)
        message_writer.messageWritten.connect(self.write_log_and_redraw)

        ##################################
        #           QT Layout            #
        ##################################

        # main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._dir_label)
        dir_layout.addWidget(self._dir_line)
        dir_layout.addWidget(self._dir_button)
        layout.addLayout(dir_layout)

        # Config selection & force checkbox & upload button
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_button)
        config_layout.addWidget(self._force_checkbox)
        config_layout.addWidget(self._upload_button)
        layout.addLayout(config_layout)

        # logging text box
        layout.addWidget(self._console)

        # Upload Progress
        current_project_layout = QtWidgets.QHBoxLayout()
        current_project_layout.addWidget(self._current_project_label)
        current_project_layout.addWidget(self._current_project)
        layout.addLayout(current_project_layout)
        project_progress_layout = QtWidgets.QHBoxLayout()
        project_progress_layout.addWidget(self._project_progress_label)
        project_progress_layout.addWidget(self._project_progress)
        layout.addLayout(project_progress_layout)

        current_sample_layout = QtWidgets.QHBoxLayout()
        current_sample_layout.addWidget(self._current_sample_label)
        current_sample_layout.addWidget(self._current_sample)
        layout.addLayout(current_sample_layout)
        sample_progress_layout = QtWidgets.QHBoxLayout()
        sample_progress_layout.addWidget(self._sample_progress_label)
        sample_progress_layout.addWidget(self._sample_progress)
        layout.addLayout(sample_progress_layout)

        current_file_layout = QtWidgets.QHBoxLayout()
        current_file_layout.addWidget(self._current_file_label)
        current_file_layout.addWidget(self._current_file)
        layout.addLayout(current_file_layout)
        file_progress_layout = QtWidgets.QHBoxLayout()
        file_progress_layout.addWidget(self._file_progress_label)
        file_progress_layout.addWidget(self._file_progress)
        layout.addLayout(file_progress_layout)

        # Set Layout and Geometry
        self.setLayout(layout)
        self.setGeometry(300, 300, 1200, 800)

        ######################################
        #         Signals and Slots          #
        ######################################

        # buttons
        self._dir_button.clicked.connect(self.open_dir)
        self._config_button.clicked.connect(self.show_config)
        self._force_checkbox.stateChanged.connect(self.click_force_upload)
        self._upload_button.clicked.connect(self.start_upload)
        # connect running upload thread finishing to finish function
        self._upload_thread.finished.connect(self.finished_upload)
        # connect progress bars
        signal_worker.project_progress_signal.connect(self._project_progress.setValue)
        signal_worker.sample_progress_signal.connect(self._sample_progress.setValue)
        signal_worker.file_progress_signal.connect(self._file_progress.setValue)
        # connect current file/sample/project text boxes
        signal_worker.current_project_signal.connect(self.update_current_project)
        signal_worker.current_sample_signal.connect(self.update_current_sample)
        signal_worker.current_file_signal.connect(self.update_current_file)

    def write_log_and_redraw(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self._console.appendPlainText(text)
        self._console.repaint()

    def update_current_project(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_project.setText(text)
        self._current_project.repaint()

    def update_current_sample(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_sample.setText(text)
        self._current_sample.repaint()

    def update_current_file(self, text):
        """
        Set text and repaint
        Used as a slot for emits
        :param text:
        :return:
        """
        self._current_file.setText(text)
        self._current_file.repaint()

    def open_dir(self):
        """
        Opens a file(directory) dialog and sets the _run_dir variable to chosen directory
        Updates ui to reflect changes
        :return:
        """
        logging.debug("GUI: open_dir clicked")
        self._run_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self._dir_line.setText(self._run_dir)
        logging.debug("GUI: result: " + self._run_dir)

    def show_config(self):
        """
        Open the config dialog window
        :return:
        """
        self.config_dlg.show()

    def click_force_upload(self, state):
        """
        Sets the _force_state variable to reflect the current checkbox state
        :param state: True/False
        :return:
        """
        logging.debug("GUI: click_force_upload clicked")
        if state == QtCore.Qt.Checked:
            logging.debug("GUI: set force upload to TRUE")
            self._force_state = True
        else:
            logging.debug("GUI: set force upload to False")
            self._force_state = False

    def start_upload(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)
        self._force_checkbox.setEnabled(False)
        # init / re-init config with config file selected
        config.setup()
        # start upload
        self._upload_thread.set_vars(self._run_dir, self._force_state)
        self._upload_thread.start()

    def finished_upload(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")
        # Unlock GUI
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
        self._force_checkbox.setEnabled(True)
        # reset checkbox
        self._force_state = False
        self._force_checkbox.setChecked(False)


class ConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.debug("GUI: Setting up ConfigDialog")

        self._client_id_label = QtWidgets.QLabel("Client ID")
        self._client_id = QtWidgets.QLineEdit()
        self._client_secret_label = QtWidgets.QLabel("Client Secret")
        self._client_secret = QtWidgets.QLineEdit()
        self._username_label = QtWidgets.QLabel("Username")
        self._username = QtWidgets.QLineEdit()
        self._password_label = QtWidgets.QLabel("Password")
        self._password = QtWidgets.QLineEdit()
        self._base_url_label = QtWidgets.QLabel("Base URL")
        self._base_url = QtWidgets.QLineEdit()
        self._parser_label = QtWidgets.QLabel("Parser")
        # self._parser = QtWidgets.QLineEdit()
        self._parser = QtWidgets.QComboBox()
        self._parser.addItems(supported_parsers)

        self._btn_check_settings = QtWidgets.QPushButton("Save and Test Settings")
        self._settings_status = QtWidgets.QLineEdit()
        self._settings_status.setReadOnly(True)
        self._btn_accept = QtWidgets.QPushButton("Accept")
        self._btn_cancel = QtWidgets.QPushButton("Cancel")

        # base layout
        layout = QtWidgets.QVBoxLayout()
        # Client ID
        client_id_layout = QtWidgets.QHBoxLayout()
        client_id_layout.addWidget(self._client_id_label)
        client_id_layout.addWidget(self._client_id)
        layout.addLayout(client_id_layout)
        # Client Secret
        client_secret_layout = QtWidgets.QHBoxLayout()
        client_secret_layout.addWidget(self._client_secret_label)
        client_secret_layout.addWidget(self._client_secret)
        layout.addLayout(client_secret_layout)
        # Username
        username_layout = QtWidgets.QHBoxLayout()
        username_layout.addWidget(self._username_label)
        username_layout.addWidget(self._username)
        layout.addLayout(username_layout)
        # Password
        password_layout = QtWidgets.QHBoxLayout()
        password_layout.addWidget(self._password_label)
        password_layout.addWidget(self._password)
        layout.addLayout(password_layout)
        # Base URL
        base_url_layout = QtWidgets.QHBoxLayout()
        base_url_layout.addWidget(self._base_url_label)
        base_url_layout.addWidget(self._base_url)
        layout.addLayout(base_url_layout)
        # Parser
        parser_layout = QtWidgets.QHBoxLayout()
        parser_layout.addWidget(self._parser_label)
        parser_layout.addWidget(self._parser)
        layout.addLayout(parser_layout)
        # Buttons
        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self._btn_check_settings)
        status_layout.addWidget(self._settings_status)
        layout.addLayout(status_layout)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self._btn_accept)
        button_layout.addWidget(self._btn_cancel)
        layout.addLayout(button_layout)

        # connections
        self._btn_check_settings.clicked.connect(self.check_connection_to_irida)
        self._btn_accept.clicked.connect(self.accept_and_exit)
        self._btn_cancel.clicked.connect(self.cancel_and_exit)

        # Set Layout and Geometry
        self.setLayout(layout)
        self.setGeometry(300, 300, 600, 300)
        # Init settings
        self.get_settings_from_file()
        self.contact_irida()

    def accept_and_exit(self):
        self.write_settings_to_file()
        self.close()

    def cancel_and_exit(self):
        self.close()

    def get_settings_from_file(self):
        config.setup()
        self._client_id.setText(config.read_config_option('client_id'))
        self._client_secret.setText(config.read_config_option('client_secret'))
        self._username.setText(config.read_config_option('username'))
        self._password.setText(config.read_config_option('password'))
        self._base_url.setText(config.read_config_option('base_url'))
        index = self._parser.findText(config.read_config_option('parser'))
        self._parser.setCurrentIndex(index)

    def write_settings_to_file(self):
        config.set_config_options(client_id=self._client_id.text(),
                                  client_secret=self._client_secret.text(),
                                  username=self._username.text(),
                                  password=self._password.text(),
                                  base_url=self._base_url.text(),
                                  parser=self._parser.currentText())
        config.write_config_options_to_file()

    def contact_irida(self):
        try:
            api_handler.initialize_api_from_config()
            self._settings_status.setText("Connection OK")
            self._settings_status.setStyleSheet("background-color: green; color: white;")
            logging.info("Successfully connected to IRIDA")
        except Exception:
            self._settings_status.setText("ERROR!")
            self._settings_status.setStyleSheet("background-color: red; color: white;")
            logging.info("Error occurred while trying to connect to IRIDA")

    def check_connection_to_irida(self):
        self.write_settings_to_file()
        self.contact_irida()


class UploadThread(QtCore.QThread):
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


def main():
    """
    Entry point for GUI
    :return:
    """
    app = QtWidgets.QApplication(["IRIDA Uploader"])
    dlg = MyDialog()
    dlg.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
