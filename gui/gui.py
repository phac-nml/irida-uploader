import logging
import os
# PyQt needs to be imported like this because for whatever reason they decided not to include a __all__ = [...]
import PyQt5.QtWidgets as QtWidgets

from core import logger
from config import config
from progress import signal_worker
from model import DirectoryStatus

from .config import ConfigDialog
from .tools import StatusThread, ParseThread, UploadThread, QtHandler

# X index for the table
TABLE_SAMPLE_NAME = 0
TABLE_FILE_1 = 1
TABLE_FILE_2 = 2
TABLE_PROJECT = 3
TABLE_PROGRESS = 4


class MainDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        logging.debug("GUI: Setting up MainDialog")

        self.config_dlg = ConfigDialog(parent=self)

        # Initialize threads
        # todo
        self._status_thread = StatusThread()
        self._parse_thread = ParseThread()
        self._upload_thread = UploadThread()

        # internal variables
        self._run_dir = ""
        self._force_state = False
        self._config_file = ""
        self._console_hidden = True
        self._table_sample_index_dict = None

        ###################################
        #           QT Objects            #
        ###################################

        # directory
        self._dir_button = QtWidgets.QPushButton(self)
        self._dir_button.setText("Open Run Directory")
        self._dir_button.setFixedWidth(200)
        self._dir_line = QtWidgets.QLineEdit(self)
        self._dir_line.setReadOnly(True)
        # config
        self._config_button = QtWidgets.QPushButton(self)
        self._config_button.setText("Configure Settings")
        self._config_button.setFixedWidth(200)
        # refresh
        self._refresh_button = QtWidgets.QPushButton(self)
        self._refresh_button.setText("Refresh")
        # upload
        self._upload_button = QtWidgets.QPushButton(self)
        self._upload_button.setText('Start Upload')

        # todo
        # Table
        self._table = QtWidgets.QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Sample Name", "File 1", "File 2", "Project", "Progress"])
        self._table.setColumnWidth(TABLE_SAMPLE_NAME, 170)
        self._table.setColumnWidth(TABLE_FILE_1, 200)
        self._table.setColumnWidth(TABLE_FILE_2, 200)
        self._table.setColumnWidth(TABLE_PROJECT, 70)
        self._table.setColumnWidth(TABLE_PROGRESS, 135)

        self._status_label = QtWidgets.QLabel("Status Result:")
        self._status_result = QtWidgets.QLineEdit()
        self._status_result.setReadOnly(True)

        # Setup logging handler
        handler = QtHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S'))
        handler.setLevel(logging.INFO)
        handler.message_writer.messageWritten.connect(self.write_log_and_redraw)
        logger.root_logger.addHandler(handler)
        self._console = QtWidgets.QPlainTextEdit(self)
        self._console.setReadOnly(True)
        self._console.hide()
        self._console_button = QtWidgets.QPushButton(self)
        self._console_button.setFixedWidth(100)
        self._console_button.setText("Show Log")

        # Set Layout and Geometry
        self.setLayout(self._layout())
        self.setGeometry(0, 0, 800, 600)
        # Center Window
        self._center_window()

        ######################################
        #         Signals and Slots          #
        ######################################

        # buttons
        self._dir_button.clicked.connect(self.open_dir)
        self._config_button.clicked.connect(self.show_config)
        self._refresh_button.clicked.connect(self.refresh)
        self._upload_button.clicked.connect(self.start_upload)
        self._console_button.clicked.connect(self.log_button_clicked)
        # connect threads finishing to finish functions
        self._status_thread.finished.connect(self.finished_status)
        self._parse_thread.finished.connect(self.finished_parse)
        self._upload_thread.finished.connect(self.finished_upload)
        # todo: connecting advanced
        signal_worker.progress_signal.connect(self.update_progress)

        # init the config stuff
        config.setup()

    def _layout(self):
        """
        Setup layout
        :return:
        """
        # main layout
        layout = QtWidgets.QVBoxLayout()

        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(self._dir_button)
        dir_layout.addWidget(self._dir_line)
        layout.addLayout(dir_layout)

        # Config selection & refresh
        config_layout = QtWidgets.QHBoxLayout()
        config_layout.addWidget(self._config_button)
        config_layout.addWidget(self._refresh_button)
        config_layout.addWidget(self._status_label)
        config_layout.addWidget(self._status_result)
        layout.addLayout(config_layout)

        layout.addWidget(self._table)

        # Upload button
        layout.addWidget(self._upload_button)

        # todo make collapsible
        # logging text box
        layout.addWidget(self._console_button)
        layout.addWidget(self._console)

        return layout

    def update_progress(self, data):
        sample_name_project = data["sample"] + "." + str(data["project"])
        self._table_sample_index_dict[sample_name_project].setValue(data["progress"])

    def write_log_and_redraw(self, text):
        """
        Adds the text given to the logger box, and repaints so it displays
        Used as a slot for emits
        :param text:
        :return:
        """
        self._console.appendPlainText(text)
        self._console.repaint()

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

        # Kick of status check and parsing after opening a new directory
        self.start_status_parse()

    def refresh(self):
        self.start_status_parse()

    def show_config(self):
        """
        Open the config dialog window
        :return:
        """
        self.config_dlg.center_window()
        self.config_dlg.show()

        # init / re-init config with config file selected
        # todo: This might be unnecessary,
        config.setup()

    def log_button_clicked(self):
        if self._console_hidden:
            self._console.show()
            self._console_button.setText("Hide Log")
            self._console_hidden = False
        else:
            self._console.hide()
            self._console_button.setText("Show Log")
            self._console_hidden = True

    # todo start
    def start_status_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")

        # lock the gui so users don't click things while the parsing is still happening.
        self._lock_gui()
        # Clear the table
        self._clear_table()

        # start upload
        self._status_thread.set_vars(self._run_dir)
        self._status_thread.start()

    def finished_status(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")
        # Output info
        status = self._status_thread.get_result()
        text = status.directory + ", " + status.status + ", " + str(status.message)
        self._status_result.setText(text)

        self.status_parse_logic(status)

    def status_parse_logic(self, status):

        if status.status_equals(DirectoryStatus.INVALID):
            print("gui status: invalid")
            # todo: do something with this info, tell the user is bad
            # since we return here, we need to unlock the gui
            self._unlock_gui()
            return
        elif status.status_equals(DirectoryStatus.NEW):
            print("gui status: new run")
            self._force_state = False
        elif status.status_equals(DirectoryStatus.COMPLETE):
            print("gui status: complete")
            # todo: warn users this was completed already & set force
            self._force_state = True
        elif status.status_equals(DirectoryStatus.PARTIAL):
            print("gui status: partial")
            # todo: warn users its partial & set force
            self._force_state = True
        elif status.status_equals(DirectoryStatus.ERROR):
            print("gui status: error")
            # todo: warn users that it was an error & set force
            self._force_state = True

        self.start_parse()

    def start_parse(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # start upload
        self._parse_thread.set_vars(self._run_dir)
        self._parse_thread.start()

    def finished_parse(self):
        """
        Unblocks the UI elements, resets the run directory and checkbox
        This acts as a slot for the upload thread on finish
        :return:
        """
        logging.debug("GUI: finished_upload called")

        self._post_parse()

        # Unlock GUI
        self._unlock_gui()

    def _post_parse(self):
        sequencing_run = self._parse_thread.get_run()

        if sequencing_run:
            # run parsed correctly
            self._fill_table(sequencing_run)
        else:
            run_errors = self._parse_thread.get_error()
            # todo: do something when a run fails to parse

    # todo end

    def start_upload(self):
        """
        Blocks usage of the ui elements, runs the config setup, and starts the upload thread with set variables
        :return:
        """
        logging.debug("GUI: start_upload clicked")
        # Lock Gui
        self._lock_gui()
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
        self._unlock_gui()

    def _center_window(self):
        """
        Gets the windows size, and centers the main qt widget
        :return:
        """
        qt_rectangle = self.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.move(qt_rectangle.topLeft())

    def _fill_table(self, sequencing_run):
        # total number of samples
        sample_count = 0

        project_list = sequencing_run.project_list
        for project in project_list:
            sample_list = project.sample_list
            sample_count = sample_count + len(sample_list)

        self._table.setRowCount(sample_count)
        self._table_sample_index_dict = {}

        y_index = 0
        for project in project_list:
            sample_list = project.sample_list
            for sample in sample_list:
                files = sample.sequence_file.file_list
                self._table.setItem(y_index, TABLE_SAMPLE_NAME, QtWidgets.QTableWidgetItem(sample.sample_name))
                self._table.setItem(y_index, TABLE_FILE_1, QtWidgets.QTableWidgetItem(os.path.basename(files[0])))
                if len(files) == 2:
                    self._table.setItem(y_index, TABLE_FILE_2, QtWidgets.QTableWidgetItem(os.path.basename(files[1])))
                self._table.setItem(y_index, TABLE_PROJECT, QtWidgets.QTableWidgetItem(project.id))

                new_progress_bar = QtWidgets.QProgressBar()
                self._table.setCellWidget(y_index, TABLE_PROGRESS, new_progress_bar)
                sample_project_key = sample.sample_name + "." + str(project.id)
                self._table_sample_index_dict[sample_project_key] = new_progress_bar

                y_index = y_index + 1

    def _clear_table(self):
        self._table.clearContents()
        self._table.setRowCount(0)

    def _lock_gui(self):
        # Lock Gui
        self._upload_button.setEnabled(False)
        self._config_button.setEnabled(False)
        self._dir_button.setEnabled(False)

    def _unlock_gui(self):
        self._upload_button.setEnabled(True)
        self._config_button.setEnabled(True)
        self._dir_button.setEnabled(True)
